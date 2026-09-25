import pytest
from fastapi import HTTPException
from app.core.config import settings
from app.oauth.manager import OAuthManager, oauth_manager


@pytest.mark.asyncio
async def test_oauth_providers():
    providers = OAuthManager.get_supported_providers()
    assert len(providers) >= 6
    provider_ids = [p["id"] for p in providers]
    assert "google" in provider_ids
    assert "slack" in provider_ids
    assert "github" in provider_ids


@pytest.mark.asyncio
async def test_oauth_login_url():
    url = oauth_manager.get_login_url("google", "test_user")
    assert "accounts.google.com" in url
    assert "test_user" in url
    assert settings.GOOGLE_CLIENT_ID in url
    assert "redirect_uri=" in url
    assert "scope=" in url


@pytest.mark.asyncio
async def test_oauth_login_url_missing_config_raises_500():
    orig_client_id = settings.GOOGLE_CLIENT_ID
    try:
        settings.GOOGLE_CLIENT_ID = ""
        with pytest.raises(HTTPException) as exc_info:
            oauth_manager.get_login_url("google", "test_user")
        assert exc_info.value.status_code == 500
        assert "Google OAuth is not configured" in exc_info.value.detail
    finally:
        settings.GOOGLE_CLIENT_ID = orig_client_id


@pytest.mark.asyncio
async def test_oauth_callback_and_disconnect():
    from unittest.mock import patch, AsyncMock, MagicMock
    user_id = "user_oauth_test"

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "ok": True,
        "access_token": "xoxb-mock-test-token-123",
        "team": {"id": "T_TEST", "name": "Test Workspace"},
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_res):
        conn = await oauth_manager.handle_callback(user_id, "Slack", "code_slack_123")

        assert conn.provider == "Slack"
        assert conn.status == "CONNECTED"

        # Check connection list
        conns = await oauth_manager.get_user_connections(user_id)
        assert len(conns) == 1
        assert conns[0].provider == "Slack"

        # Disconnect
        disconnected = await oauth_manager.disconnect(user_id, "Slack")
        assert disconnected is True

        # Check connection list after disconnect
        conns_after = await oauth_manager.get_user_connections(user_id)
        assert len(conns_after) == 0
