from flask import Flask, request, render_template, flash, redirect, jsonify, make_response, url_for
import os
import base64
import sqlite3
import arrow

app = Flask(__name__)
app.config['SECRET_KEY']="verysecret"
DEPLOY_URL=os.getenv('DEPLOY_URL') if os.getenv('DEPLOY_URL') else 'http://localhost:5000/'


class UrlExistsError(Exception):
  pass


def create_short_url(url, userShortUrl=None, userExpiry=None):
  # Create a random 6 character URL if none is supplied
  # Decode to ascii from bytes so we can use equality rather than like in SQLite
  shortUrl = base64.urlsafe_b64encode(os.urandom(6)).decode("ascii")
  if userShortUrl:
    shortUrl = userShortUrl
  try:
    expiry = arrow.get(userExpiry).format("YYYY-MM-DD HH:mm:ss") if userExpiry else None
  except arrow.ParserError:
    return make_response(jsonify({"error": "date input malformed, please use ISO 8601"}), 400)

  conn = sqlite3.connect('app.db')
  cur = conn.cursor()
  try:
    cur.execute('INSERT INTO urls (url, shorturl, expiry) VALUES (?,?,?)', (url, shortUrl, expiry))
  except sqlite3.IntegrityError:
    # TODO: auto-regenerate a new random one if there is none supplied and try again
    conn.close()
    raise UrlExistsError("that short URL already exists, please try a different one")
  conn.commit()
  conn.close()
  return shortUrl


@app.route('/', methods=['GET', 'POST'])
def index():
  if request.method == 'POST':
    try:
      shortUrl = create_short_url(request.form["url"], request.form["short"] if request.form["short"] else None)
      flash(DEPLOY_URL + shortUrl, 'success')
      return redirect(url_for('index'))
    except UrlExistsError as error_message:
      flash(error_message, 'error')

  return render_template('index.html')


@app.route('/api/create', methods=['POST'])
def create_shorturl():
  # TODO: better error handling for bad body input (non-json etc.)
  # Check for required payload (the source url)
  try:
    url = request.json['url']
  except KeyError:
    return make_response(jsonify({"error": "body parameter 'url' is required, please supply one and try again"}), 400)

  # Create a random 6 character URL if none is supplied
  # Decode to ascii from bytes so we can use equality rather than like in SQLite
  shortUrl = base64.urlsafe_b64encode(os.urandom(6)).decode("ascii")
  if 'shorturl' in request.json:
    shortUrl = request.json['shorturl']
  if 'expiry' in request.json:
    userExpiry = request.json['expiry']

  try:
    shortUrl = create_short_url(url, shortUrl, userExpiry if userExpiry else None)
  except UrlExistsError as error_message:
    return make_response(jsonify({"error": str(error_message)}), 409)

  return jsonify({"result": "success", "url": DEPLOY_URL + shortUrl})


@app.route('/api/delete', methods=["DELETE"])
def delete_shorturl():
  try:
    url = request.json['shorturl']
  except KeyError:
    return "body parameter 'shorturl' is required, please supply one and try again"

  conn = sqlite3.connect('app.db')
  cur = conn.cursor()
  cur.execute('SELECT * FROM urls where shorturl=:shorturl', {"shorturl": url})
  if not cur.fetchone():
    conn.close()
    return make_response(jsonify({"error": "No short URL found with that value"}), 404)
  
  cur.execute('DELETE FROM urls where shorturl=:shorturl', {"shorturl": url})
  conn.commit()
  conn.close()
  return jsonify({"deleted": "success"})
  

@app.route("/<shorturl>")
def redirect_to_source(shorturl):
  conn = sqlite3.connect('app.db')
  cur = conn.cursor()
  cur.execute("SELECT url, expiry from urls where shorturl=:queryurl", {"queryurl": shorturl})
  try:
    result = cur.fetchone()
    sourceUrl = result[0]
    expiry = result[1]
    if expiry and arrow.get(expiry) < arrow.utcnow().shift(hours=-8):
      return make_response(jsonify({"error": "sorry, that URL has expired"}), 410)
    cur.execute("UPDATE urls set views=views+1 where shorturl=:queryurl ", {"queryurl": shorturl})
    conn.commit()
  except TypeError:
    return "sorry, that URL doesn't exist"
  # return sourceUrl
  return redirect(sourceUrl)


# TODO: write template for analytics
@app.route('/analytics/<shortUrl>')
def analytics(shortUrl):
  conn = sqlite3.connect('app.db')
  cur = conn.cursor()
  cur.execute("SELECT views from urls where shorturl=:queryurl", {"queryurl": shortUrl})
  views = cur.fetchone()[0]
  conn.close()
  return "Views: " + str(views)


if __name__ == '__main__':
    app.run(debug=True)
