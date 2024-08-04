import os
import logging
from flask import Flask, request, redirect, session, jsonify
from requests_oauthlib import OAuth2Session

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

logging.basicConfig(level=logging.DEBUG)

# GitHub OAuth settings
client_id = os.environ.get("GITHUB_CLIENT_ID")
client_secret = os.environ.get("GITHUB_CLIENT_SECRET")
authorization_base_url = 'https://github.com/login/oauth/authorize'
token_url = 'https://github.com/login/oauth/access_token'

# Check if client_id and client_secret are set
if not client_id or not client_secret:
    raise ValueError("GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET must be set in environment variables")

@app.route("/login")
def login():
    if not client_id:
        return "Error: GitHub Client ID is not set. Please configure the application correctly.", 500
    
    github = OAuth2Session(client_id)
    authorization_url, state = github.authorization_url(authorization_base_url)
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route("/callback")
def callback():
    try:
        app.logger.info(f"Callback received. URL: {request.url}")
        app.logger.info(f"Session state: {session.get('oauth_state')}")
        
        github = OAuth2Session(client_id, state=session.get('oauth_state'))
        token = github.fetch_token(token_url, client_secret=client_secret,
                                   authorization_response=request.url)
        session['oauth_token'] = token
        app.logger.info(f"OAuth token received: {token}")
        return redirect("/dashboard")
    except Exception as e:
        app.logger.error(f"Error in callback: {str(e)}", exc_info=True)
        return jsonify({"error": str(e), "url": request.url, "state": session.get('oauth_state')}), 500

# Add this new route to handle the root URL
@app.route("/")
def home():
    return "Welcome to the GitHub Star Network Monitoring app! <a href='/login'>Login with GitHub</a>"

@app.route("/dashboard")
def dashboard():
    token = session.get('oauth_token')
    if not token:
        app.logger.warning("No OAuth token found in session")
        return redirect("/login")
    return f"Logged in successfully! Token: {token}"

@app.route("/debug")
def debug():
    return jsonify({
        "session": dict(session),
        "request": {
            "url": request.url,
            "headers": dict(request.headers),
            "cookies": request.cookies,
            "args": dict(request.args)
        },
        "environment": {
            "GITHUB_CLIENT_ID": os.environ.get("GITHUB_CLIENT_ID"),
            "GITHUB_CLIENT_SECRET": "***" if os.environ.get("GITHUB_CLIENT_SECRET") else None
        }
    })

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

