import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.connectors.security.secret_manager import secret_manager
from app.agents.oauth_ai.account_picker import account_picker
from app.oauth.manager import oauth_manager

client = TestClient(app, follow_redirects=False)


@pytest.fixture(autouse=True)
def reset_oauth_state():
    account_picker.accounts.clear()
    oauth_manager._connections.clear()
    yield
    account_picker.accounts.clear()
    oauth_manager._connections.clear()


def test_google_callback_success_redirects_to_ui():
    """Test A: Google callback with valid code issues 302 redirect to frontend success page."""
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "access_token": "ya29.test-google-token",
        "refresh_token": "1//test-google-refresh",
        "expires_in": 3600,
    }

    mock_uinfo = MagicMock()
    mock_uinfo.status_code = 200
    mock_uinfo.json.return_value = {
        "email": "testuser@gmail.com",
        "name": "Test User",
        "picture": "https://lh3.googleusercontent.com/avatar.jpg",
    }

    async def mock_post(*args, **kwargs):
        return mock_res

    async def mock_get(*args, **kwargs):
        return mock_uinfo

    with patch("httpx.AsyncClient.post", side_effect=mock_post), \
         patch("httpx.AsyncClient.get", side_effect=mock_get), \
         patch.object(settings, "GOOGLE_CLIENT_ID", "test-google-id"), \
         patch.object(settings, "GOOGLE_CLIENT_SECRET", "test-google-secret"), \
         patch.object(settings, "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/oauth/google/callback"):

        res = client.get("/api/v1/oauth/google/callback?code=valid_google_code_123")
        assert res.status_code == 302
        location = res.headers.get("location", "")
        assert location == "http://localhost:5173/oauth/result?provider=google&status=success"

        # Security check: Ensure no token/secret in URL
        assert "access_token" not in location
        assert "refresh_token" not in location
        assert "client_secret" not in location
        assert "valid_google_code_123" not in location


def test_google_callback_failure_redirects_to_error_ui():
    """Test B: Google callback with error param redirects to frontend error page."""
    res = client.get("/api/v1/oauth/google/callback?error=access_denied")
    assert res.status_code == 302
    location = res.headers.get("location", "")
    assert location == "http://localhost:5173/oauth/result?provider=google&status=error"


def test_slack_callback_success_redirects_to_ui():
    """Test C: Slack callback with valid code issues 302 redirect to frontend success page."""
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "ok": True,
        "access_token": "xoxb-test-slack-token-999",
        "team": {"id": "T123456", "name": "AgentFlow Workspace"},
    }

    async def mock_post(*args, **kwargs):
        return mock_res

    with patch("httpx.AsyncClient.post", side_effect=mock_post), \
         patch.object(settings, "SLACK_CLIENT_ID", "test-slack-id"), \
         patch.object(settings, "SLACK_CLIENT_SECRET", "test-slack-secret"), \
         patch.object(settings, "SLACK_REDIRECT_URI", "http://127.0.0.1:8000/api/v1/oauth/slack/callback"):

        res = client.get("/api/v1/oauth/slack/callback?code=valid_slack_code_456")
        assert res.status_code == 302
        location = res.headers.get("location", "")
        assert location == "http://localhost:5173/oauth/result?provider=slack&status=success"

        # Security check: Ensure no token/secret in URL
        assert "xoxb-test-slack-token-999" not in location
        assert "test-slack-secret" not in location


def test_slack_callback_failure_redirects_to_error_ui():
    """Test D: Slack callback with invalid code or failure response redirects to frontend error page."""
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "ok": False,
        "error": "invalid_code",
    }

    async def mock_post(*args, **kwargs):
        return mock_res

    with patch("httpx.AsyncClient.post", side_effect=mock_post), \
         patch.object(settings, "SLACK_CLIENT_ID", "test-slack-id"), \
         patch.object(settings, "SLACK_CLIENT_SECRET", "test-slack-secret"):

        res = client.get("/api/v1/oauth/slack/callback?code=bad_slack_code")
        assert res.status_code == 302
        location = res.headers.get("location", "")
        assert location == "http://localhost:5173/oauth/result?provider=slack&status=error"


def test_no_code_param_redirects_to_error_ui():
    """Test E: Calling callback without code parameter redirects cleanly to error page."""
    res = client.get("/api/v1/oauth/google/callback")
    assert res.status_code == 302
    location = res.headers.get("location", "")
    assert location == "http://localhost:5173/oauth/result?provider=google&status=error"
