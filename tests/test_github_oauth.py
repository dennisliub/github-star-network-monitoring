import pytest
from unittest.mock import patch, MagicMock
from auth.github_oauth import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_oauth(monkeypatch):
    mock = MagicMock()
    mock.authorization_url.return_value = ('https://github.com/login/oauth/authorize', 'state')
    mock.fetch_token.return_value = {'access_token': 'mock_token'}
    monkeypatch.setattr('auth.github_oauth.OAuth2Session', lambda *args, **kwargs: mock)
    return mock

@pytest.fixture
def mock_env_variables(monkeypatch):
    monkeypatch.setenv('GITHUB_CLIENT_ID', 'mock_client_id')
    monkeypatch.setenv('GITHUB_CLIENT_SECRET', 'mock_client_secret')

def test_login(client, mock_oauth, mock_env_variables):
    response = client.get('/login')
    assert response.status_code == 302
    assert response.location == 'https://github.com/login/oauth/authorize'

def test_callback(client, mock_oauth, mock_env_variables):
    with client.session_transaction() as session:
        session['oauth_state'] = 'test_state'
    
    response = client.get('/callback?code=test_code&state=test_state')
    assert response.status_code == 302
    assert response.location == '/dashboard'

def test_dashboard(client):
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b"Logged in successfully!" in response.data
