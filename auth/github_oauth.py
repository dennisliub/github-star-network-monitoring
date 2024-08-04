import os
import logging
import json
from datetime import date, datetime, timedelta
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
    <a href="/similar_users?num_users=20">Find Users with Similar Interests</a>
    <br>
    <a href="/similar_repos">View Repositories You've Starred</a>
    <br>
    <a href="/similar_users_repos">View Repositories Starred by Users with Similar Interests</a>
    """


@app.route("/similar_users")
def similar_users():
    token = session.get('oauth_token')
    if not token:
        app.logger.warning("No OAuth token found in session")
        return redirect("/login")
    
    num_users = int(request.args.get('num_users', 20))
    github = OAuth2Session(client_id, token=token)
    
    # Get user's starred repositories
    starred_url = 'https://api.github.com/user/starred'
    starred_response = github.get(starred_url)
    starred_repos = starred_response.json()
    
    # Get users who starred the same repositories
    similar_users = {}
    for repo in starred_repos[:5]:  # Limit to first 5 repos to avoid rate limiting
        stargazers_url = f"{repo['url']}/stargazers"
        stargazers_response = github.get(stargazers_url)
        stargazers = stargazers_response.json()
        
        for user in stargazers[:num_users]:  # Limit to specified number of users
            if user['login'] not in similar_users:
                similar_users[user['login']] = {
                    'avatar_url': user['avatar_url'],
                    'html_url': user['html_url'],
                    'common_repos': []
                }
            similar_users[user['login']]['common_repos'].append(repo['full_name'])
    
    # Sort users by number of common repositories
    sorted_users = sorted(similar_users.items(), key=lambda x: len(x[1]['common_repos']), reverse=True)
    
    user_list = ""
    for username, user_data in sorted_users[:num_users]:
        user_list += f"""
        <li>
            <img src="{user_data['avatar_url']}" width="50">
            <a href="{user_data['html_url']}">{username}</a>
            <br>Common repos: {', '.join(user_data['common_repos'])}
        </li>
        """
    
    return f"""
    <h1>Users with Similar Interests</h1>
    <ul>
    {user_list}
    </ul>
    <a href="/dashboard">Back to Dashboard</a>
    """

@app.route("/similar_repos")
def similar_repos():
    token = session.get('oauth_token')
    if not token:
        app.logger.warning("No OAuth token found in session")
        return redirect("/login")
    
    github = OAuth2Session(client_id, token=token)
    
    # Get user's starred repositories
    starred_url = 'https://api.github.com/user/starred'
    starred_response = github.get(starred_url)
    starred_repos = starred_response.json()
    
    repo_stats = {}
    
    # For each starred repo, get its star count
    for repo in starred_repos:
        repo_name = repo['full_name']
        repo_url = repo['html_url']
        star_count = repo['stargazers_count']
        
        repo_stats[repo_name] = {
            'url': repo_url,
            'stars': star_count
        }
    
    # Sort repos by star count
    sorted_repos = sorted(repo_stats.items(), key=lambda x: x[1]['stars'], reverse=True)
    
    table_rows = ""
    for repo_name, stats in sorted_repos:
        table_rows += f"<tr><td><a href='{stats['url']}'>{repo_name}</a></td><td>{stats['stars']}</td></tr>"
    
    return f"""
    <h1>Repositories You've Starred</h1>
    <p>Here are the repositories you've starred, sorted by their star count:</p>
    <table border="1">
        <tr>
            <th>Repository</th>
            <th>Stars</th>
        </tr>
        {table_rows}
    </table>
    <a href="/dashboard">Back to Dashboard</a>
    """

def cache_user_stars(github, username):
    cache_dir = 'cache'
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    today = date.today().isoformat()
    cache_file = os.path.join(cache_dir, f"{username}_{today}.json")
    
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)
    
    user_starred_url = f'https://api.github.com/users/{username}/starred'
    params = {'sort': 'created', 'direction': 'desc', 'per_page': 100}
    user_starred_response = github.get(user_starred_url, params=params)
    user_starred_repos = user_starred_response.json()

    for repo in user_starred_repos:
        # Use 'created_at' as a proxy for 'starred_at'
        repo['starred_at'] = repo['created_at']

    with open(cache_file, 'w') as f:
        json.dump(user_starred_repos, f)
    
    return user_starred_repos

@app.route("/similar_users_repos")
def similar_users_repos():
    token = session.get('oauth_token')
    if not token:
        app.logger.warning("No OAuth token found in session")
        return redirect("/login")
    
    github = OAuth2Session(client_id, token=token)
    
    # Get user's starred repositories
    starred_url = 'https://api.github.com/user/starred'
    starred_response = github.get(starred_url)
    starred_repos = starred_response.json()
    
    # Get users who starred the same repositories
    similar_users = {}
    for repo in starred_repos[:10]:  # Increased to 10 repos to get more users
        stargazers_url = f"{repo['url']}/stargazers"
        params = {'per_page': 100}
        stargazers_response = github.get(stargazers_url, params=params)
        stargazers = stargazers_response.json()
        
        for user in stargazers:
            if user['login'] not in similar_users and len(similar_users) < 500:
                similar_users[user['login']] = set()
            if len(similar_users) >= 500:
                break
        if len(similar_users) >= 500:
            break
    
    # Get starred repos for each similar user
    all_repos = {}
    for username in similar_users.keys():
        user_starred_repos = cache_user_stars(github, username)
        
        for repo in user_starred_repos:
            repo_name = repo['full_name']
            starred_at = repo.get('starred_at')
            if starred_at:
                starred_at = datetime.strptime(starred_at, "%Y-%m-%dT%H:%M:%SZ")
                age_weight = calculate_age_weight(starred_at)
            else:
                age_weight = 0.2  # Default to lowest weight if no date available
            
            if repo_name not in all_repos:
                all_repos[repo_name] = {
                    'url': repo['html_url'],
                    'stars': repo['stargazers_count'],
                    'count': 1,
                    'weighted_count': age_weight
                }
            else:
                all_repos[repo_name]['count'] += 1
                all_repos[repo_name]['weighted_count'] += age_weight
    
    # Sort repos by weighted count
    sorted_repos = sorted(all_repos.items(), key=lambda x: (x[1]['weighted_count'], x[1]['stars']), reverse=True)
    
    table_rows = ""
    for repo_name, stats in sorted_repos[:100]:  # Show top 100 repos
        table_rows += f"<tr><td><a href='{stats['url']}'>{repo_name}</a></td><td>{stats['stars']}</td><td>{stats['count']}</td><td>{stats['weighted_count']:.2f}</td></tr>"
    
    return f"""
    <h1>Repositories Starred by Users with Similar Interests</h1>
    <p>Here are the top repositories starred by users with similar interests to you, weighted by recency:</p>
    <table border="1">
        <tr>
            <th>Repository</th>
            <th>Total Stars</th>
            <th>Similar Users Who Starred</th>
            <th>Weighted Count</th>
        </tr>
        {table_rows}
    </table>
    <a href="/dashboard">Back to Dashboard</a>
    """

def calculate_age_weight(starred_at):
    now = datetime.utcnow()
    age = now - starred_at
    if age <= timedelta(days=30):
        return 1.0
    elif age <= timedelta(days=90):
        return 0.8
    elif age <= timedelta(days=180):
        return 0.6
    elif age <= timedelta(days=365):
        return 0.4
    else:
        return 0.2

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

