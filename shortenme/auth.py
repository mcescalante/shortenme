from flask import request, jsonify, current_app
import functools


def check_auth(username, password):
    """Check that the username and password match the app config"""
    return (
        username == current_app.config["ADMIN_USERNAME"]
        and password == current_app.config["ADMIN_PASSWORD"]
    )


def requires_authorization(f):
    """Wrapper to check authorization"""

    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


def authenticate():
    """User authentication prompt"""
    message = {"message": "Authenticate for administrative analytics"}
    resp = jsonify(message)

    resp.status_code = 401
    resp.headers["WWW-Authenticate"] = "Basic"

    return resp
