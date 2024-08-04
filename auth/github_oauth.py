import os
import logging
from flask import Flask, request, redirect, session, jsonify
from requests_oauthlib import OAuth2Session

# Check if we're in a development environment
if os.environ.get('FLASK_ENV') == 'development':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    print("OAUTHLIB_INSECURE_TRANSPORT set to 1")
else:
    print("FLASK_ENV is not set to 'development'")

print(f"OAUTHLIB_INSECURE_TRANSPORT: {os.environ.get('OAUTHLIB_INSECURE_TRANSPORT')}")
print(f"FLASK_ENV: {os.environ.get('FLASK_ENV')}")

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
redirect_uri = os.environ.get("GITHUB_REDIRECT_URI", "http://127.0.0.1:5000/callback")

# Check if client_id and client_secret are set
if not client_id or not client_secret:
    raise ValueError("GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET must be set in environment variables")

@app.route("/login")
def login():
    app.logger.info("Login route accessed")
    app.logger.info(f"Client ID: {client_id}")
    app.logger.info(f"Authorization base URL: {authorization_base_url}")
    app.logger.info(f"Request URL: {request.url}")
    app.logger.info(f"Request headers: {dict(request.headers)}")
    app.logger.info(f"Request method: {request.method}")
    app.logger.info(f"Request args: {dict(request.args)}")
    app.logger.info(f"Environment variables: {dict(os.environ)}")
    app.logger.info(f"Redirect URI: {redirect_uri}")
    
    if not client_id:
        app.logger.error("GitHub Client ID is not set")
        return "Error: GitHub Client ID is not set. Please configure the application correctly.", 500
    
    try:
        app.logger.info("Creating OAuth2Session")
        github = OAuth2Session(client_id, redirect_uri=redirect_uri)
        app.logger.info(f"OAuth2Session created successfully with redirect_uri: {redirect_uri}")
        
        app.logger.info("Generating authorization URL")
        authorization_url, state = github.authorization_url(authorization_base_url)
        app.logger.info(f"Authorization URL generated: {authorization_url}")
        
        session['oauth_state'] = state
        app.logger.info(f"OAuth state stored in session: {state}")
        
        app.logger.info("Preparing to redirect to authorization URL")
        response = redirect(authorization_url)
        app.logger.info(f"Redirect response created: {response}")
        app.logger.info(f"Redirect status code: {response.status_code}")
        app.logger.info(f"Redirect headers: {dict(response.headers)}")
        
        # Log all session data (be careful with sensitive information)
        app.logger.info(f"Session data: {dict(session)}")
        
        app.logger.info("About to return response")
        app.logger.info(f"Final response object: {response}")
        app.logger.info(f"Final response headers: {dict(response.headers)}")
        app.logger.info(f"Final response status: {response.status}")
        
        return response
    except Exception as e:
        app.logger.error(f"Error in login route: {str(e)}", exc_info=True)
        return f"An error occurred: {str(e)}", 500

@app.route("/callback")
def callback():
    app.logger.info("Callback route accessed")
    app.logger.info(f"Full request URL: {request.url}")
    app.logger.info(f"Request method: {request.method}")
    app.logger.info(f"Request headers: {dict(request.headers)}")
    app.logger.info(f"Request args: {dict(request.args)}")
    app.logger.info(f"Session state: {session.get('oauth_state')}")
    app.logger.info(f"Client ID: {client_id}")
    app.logger.info(f"Token URL: {token_url}")
    app.logger.info(f"Redirect URI: {redirect_uri}")
    app.logger.info(f"OAUTHLIB_INSECURE_TRANSPORT: {os.environ.get('OAUTHLIB_INSECURE_TRANSPORT')}")
    app.logger.info(f"FLASK_ENV: {os.environ.get('FLASK_ENV')}")

    # Check if there's an error in the callback
    if 'error' in request.args:
        error_description = request.args.get('error_description', 'No description provided')
        app.logger.error(f"Error in GitHub callback: {request.args['error']} - {error_description}")
        return jsonify({"error": request.args['error'], "description": error_description}), 400

    # Check if the code is present in the request args
    if 'code' not in request.args:
        app.logger.error("No code found in the callback request")
        return jsonify({"error": "No code provided in the callback"}), 400

    # Verify state
    if request.args.get('state') != session.get('oauth_state'):
        app.logger.error("State mismatch. Possible CSRF attack.")
        app.logger.error(f"Received state: {request.args.get('state')}")
        app.logger.error(f"Stored state: {session.get('oauth_state')}")
        return jsonify({"error": "State mismatch. Possible CSRF attack."}), 400

    try:
        github = OAuth2Session(client_id, state=session.get('oauth_state'))
        app.logger.info("Fetching token from GitHub")
        app.logger.info(f"Authorization response URL: {request.url}")
        token = github.fetch_token(token_url, client_secret=client_secret,
                                   authorization_response=request.url)
        app.logger.info("Token successfully fetched")
        app.logger.info(f"Token type: {type(token)}")
        app.logger.info(f"Token keys: {token.keys()}")
        session['oauth_token'] = token
        app.logger.info(f"OAuth token received and stored in session")
        
        # Fetch user information
        user_url = 'https://api.github.com/user'
        github = OAuth2Session(client_id, token=token)
        user_response = github.get(user_url)
        user_info = user_response.json()
        app.logger.info(f"User info fetched: {user_info}")
        
        app.logger.info("Redirecting to /dashboard")
        return redirect("/dashboard")
    except Exception as e:
        app.logger.error(f"Error in callback: {str(e)}", exc_info=True)
        app.logger.error(f"Full exception details: {repr(e)}")
        return jsonify({"error": str(e), "url": request.url, "state": session.get('oauth_state')}), 500

@app.after_request
def after_request(response):
    app.logger.info(f"After request: status code {response.status_code}")
    app.logger.info(f"Response headers: {dict(response.headers)}")
    return response

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
    
    github = OAuth2Session(client_id, token=token)
    user_url = 'https://api.github.com/user'
    user_response = github.get(user_url)
    user_info = user_response.json()
    
    return f"""
    <h1>Welcome, {user_info['login']}!</h1>
    <img src="{user_info['avatar_url']}" width="100">
    <p>Name: {user_info['name']}</p>
    <p>Followers: {user_info['followers']}</p>
    <p>Following: {user_info['following']}</p>
    <p>Public Repos: {user_info['public_repos']}</p>
    <a href="/starred">View Starred Repositories</a>
    """

@app.route("/starred")
def starred_repos():
    token = session.get('oauth_token')
    if not token:
        app.logger.warning("No OAuth token found in session")
        return redirect("/login")
    
    github = OAuth2Session(client_id, token=token)
    starred_url = 'https://api.github.com/user/starred'
    starred_response = github.get(starred_url)
    starred_repos = starred_response.json()
    
    repo_list = "<ul>"
    for repo in starred_repos[:10]:  # Limit to first 10 repos
        repo_list += f"<li><a href='{repo['html_url']}'>{repo['full_name']}</a></li>"
    repo_list += "</ul>"
    
    return f"""
    <h1>Your Starred Repositories</h1>
    {repo_list}
    <a href="/dashboard">Back to Dashboard</a>
    """

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

@app.route("/raw_callback")
def raw_callback():
    return jsonify({
        "url": request.url,
        "args": dict(request.args),
        "headers": dict(request.headers),
        "method": request.method
    })

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

