from flask import (
    Flask,
    request,
    render_template,
    flash,
    redirect,
    jsonify,
    make_response,
    url_for,
    g,
)
import os
import pathlib
import base64
import sqlite3
import arrow
from urllib.parse import urlparse, ParseResult

basedir = pathlib.Path(__file__).parent.resolve()
app = Flask(__name__)
app.config["SECRET_KEY"] = "verysecret"
DEPLOY_URL = os.getenv("DEPLOY_URL", "http://localhost:5000/")
DATABASE_URI = os.getenv("DATABASE_URI", pathlib.Path(basedir).joinpath("app.db"))


def get_db():
    """Connect to sqlite3 database and return db object"""
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE_URI)
    return db


@app.teardown_appcontext
def close_connection(exception):
    """Close db connection when application is shut down"""
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


@app.cli.command("init-db")
def init_db():
    """Clear out data and re-initialize database tables
    Can be called as well by the flask cli
    """
    with app.app_context():
        db = get_db()
        with app.open_resource("schema.sql", mode="r") as f:
            db.cursor().executescript(f.read())
        db.commit()


class UrlExistsError(Exception):
    """Custom exception for short URLs that already exist"""
    pass


def create_short_url(url, user_short_url=None, user_expiry=None):
    """Create a short URL for a given URL with optional expiry and user supplied short URL
    
    Generates a random 6 character URL if none is supplied using os.random,
    decode to ascii from bytes so we can use equality rather than like in SQLite
    """

    short_url = base64.urlsafe_b64encode(os.urandom(6)).decode("ascii")
    if user_short_url:
        short_url = user_short_url
    try:
        expiry = (
            arrow.get(user_expiry).format("YYYY-MM-DD HH:mm:ss")
            if user_expiry
            else None
        )
    except arrow.ParserError:
        return make_response(
            jsonify({"error": "date input malformed, please use ISO 8601"}), 400
        )

    conn = get_db()
    cur = get_db().cursor()
    try:
        cur.execute(
            "INSERT INTO urls (url, shorturl, expiry) VALUES (?,?,?)",
            (url, short_url, expiry),
        )
    except sqlite3.IntegrityError:
        # TODO: auto-regenerate a new random one if there is none supplied and try again
        conn.close()
        raise UrlExistsError(
            "that short URL already exists, please try a different one"
        )
    conn.commit()
    return short_url


@app.route("/", methods=["GET", "POST"])
def index():
    """Form to allow a user to shorten a URL via the web interface"""
    if request.method == "POST":
        try:
            user_short = request.form["short"] if request.form["short"] else None
            user_expiry = request.form["expiry"] if request.form["expiry"] else None
            short_url = create_short_url(request.form["url"], user_short, user_expiry)
            flash(DEPLOY_URL + short_url, "success")
            return redirect(url_for("index"))
        except UrlExistsError as error_message:
            flash(error_message, "error")

    return render_template("index.html")


@app.route("/api/create", methods=["POST"])
def create_shorturl():
    """API for creating a short URL"""
    # Check for required payload (the source url)
    try:
        url = request.json["url"]
    except KeyError:
        return make_response(
            jsonify(
                {
                    "error": "body parameter 'url' is required, please supply one and try again"
                }
            ),
            400,
        )

    # Create a random 6 character URL if none is supplied
    # Decode to ascii from bytes so we can use equality rather than like in SQLite
    short_url = base64.urlsafe_b64encode(os.urandom(6)).decode("ascii")
    user_expiry = None
    if "shorturl" in request.json:
        short_url = request.json["shorturl"]
    if "expiry" in request.json:
        user_expiry = request.json["expiry"]

    # Use URL parse to detect and add http if missing
    final_url = urlparse(url)
    if final_url.scheme == "http" or final_url.scheme == "https":
        final_url = url
    else:
        netloc = final_url.netloc or final_url.path
        path = final_url.path if final_url.netloc else ""
        final_url = ParseResult("http", netloc, path, *final_url[3:]).geturl()

    try:
        short_url = create_short_url(
            final_url, short_url, user_expiry if user_expiry else None
        )
    except UrlExistsError as error_message:
        return make_response(jsonify({"error": str(error_message)}), 409)

    return jsonify(
        {"result": "success", "url": DEPLOY_URL + short_url, "short_url": short_url}
    )


@app.route("/api/delete", methods=["DELETE"])
def delete_shorturl():
    """API for deleting a specific short URL"""
    try:
        url = request.json["shorturl"]
    except KeyError:
        return "body parameter 'shorturl' is required, please supply one and try again"

    conn = get_db()
    cur = get_db().cursor()
    cur.execute("SELECT * FROM urls where shorturl=:shorturl", {"shorturl": url})
    if not cur.fetchone():
        return make_response(
            jsonify({"error": "No short URL found with that value"}), 404
        )

    cur.execute("DELETE FROM urls where shorturl=:shorturl", {"shorturl": url})
    conn.commit()
    return jsonify({"deleted": "success"})


@app.route("/api/analytics/<short_url>")
def analytics_api(short_url):
    """API for returning analytics information about a given URL"""
    cur = get_db().cursor()
    cur.execute("SELECT * from urls where shorturl=:queryurl", {"queryurl": short_url})
    data = cur.fetchone()
    return jsonify(
        {
            "created_utc": data[1],
            "expiry": data[2],
            "source_url": data[3],
            "views": data[5],
        }
    )


@app.route("/<shorturl>")
def redirect_to_source(shorturl):
    """Redirect the user to the source URL given a short URL. Increment the view count"""
    conn = get_db()
    cur = get_db().cursor()
    cur.execute(
        "SELECT url, expiry from urls where shorturl=:queryurl", {"queryurl": shorturl}
    )
    try:
        result = cur.fetchone()
        source_url = result[0]
        expiry = result[1]
        if expiry and arrow.get(expiry) < arrow.utcnow().shift(hours=-8):
            return make_response(jsonify({"error": "sorry, that URL has expired"}), 410)
        cur.execute(
            "UPDATE urls set views=views+1 where shorturl=:queryurl ",
            {"queryurl": shorturl},
        )
        conn.commit()
    except TypeError:
        return "sorry, that URL doesn't exist"
    # return sourceUrl
    return redirect(source_url)


@app.route("/analytics/")
def analytics_overview():
    """Analytics web interface overview for entire system"""
    cur = get_db().cursor()
    cur.execute("SELECT count(*) from urls")
    url_count = cur.fetchone()[0]
    cur.execute("SELECT sum(views) from urls")
    total_views = cur.fetchone()[0]
    return render_template(
        "analytics-overview.html", url_count=url_count, total_views=total_views
    )


@app.route("/analytics/<short_url>")
def analytics(short_url):
    """More detailed analytics web interface for a specific short URL"""
    cur = get_db().cursor()
    cur.execute("SELECT * from urls where shorturl=:queryurl", {"queryurl": short_url})
    data = cur.fetchone()
    return render_template("analytics.html", short_url=short_url, data=data)


if __name__ == "__main__":
    app.run(debug=True)
