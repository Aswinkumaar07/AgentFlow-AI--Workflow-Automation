import pytest
from app.core.config import settings
from app.oauth.manager import oauth_manager
from app.agents.oauth_ai.account_picker import account_picker


def test_oauth_environment_config_loaded():
    assert settings.GOOGLE_CLIENT_ID is not None
    assert settings.GOOGLE_REDIRECT_URI == "http://localhost:8000/api/v1/oauth/google/callback"


def test_google_oauth_url_generation():
    url = oauth_manager.get_login_url("Google", user_id="usr_test_1")
    assert "https://accounts.google.com/o/oauth2/v2/auth" in url
    assert "response_type=code" in url
    assert "access_type=offline" in url
    assert "prompt=consent" in url
    assert "redirect_uri=" in url
    assert "scope=" in url


@pytest.mark.asyncio
async def test_oauth_callback_token_exchange_and_storage():
    user_id = "usr_phase2_2"
    conn = await oauth_manager.handle_callback(user_id=user_id, provider="Gmail", code="auth_code_xyz123")
    assert conn.provider == "Google"
    assert conn.access_token.startswith("access_")
    assert conn.status == "CONNECTED"

    accs = account_picker.list_accounts("Google")
    assert len(accs) >= 1
    default_acc = account_picker.get_default_account("Google")
    assert default_acc is not None


@pytest.mark.asyncio
async def test_get_connected_account_and_scope_validation():
    user_id = "usr_prod_oauth"
    await oauth_manager.handle_callback(user_id=user_id, provider="Gmail", code="code_oauth_prod_999")

    # Fetch connected account
    acc = await oauth_manager.get_connected_account(user_id, "Gmail")
    assert acc is not None
    assert "email" in acc
    assert "display_name" in acc
    assert "avatar" in acc
    assert "expires_at" in acc
    assert "scopes" in acc
    assert acc["provider"] == "Google"
    assert acc["status"] == "CONNECTED"

    # Validate scopes
    scope_res = oauth_manager.validate_scopes(user_id, "Gmail", ["gmail.readonly"])
    assert scope_res["valid"] is True
    assert len(scope_res["missing_scopes"]) == 0

    # Unconnected account returns None
    unconn_acc = await oauth_manager.get_connected_account("unconnected_user", "Gmail")
    assert unconn_acc is None


@pytest.mark.asyncio
async def test_oauth_token_auto_refresh():
    user_id = "usr_phase2_2"
    conn = await oauth_manager.handle_callback(user_id=user_id, provider="Slack", code="slack_code_123")

    # Force expire token
    conn.expires_at = 0.0

    refreshed = await oauth_manager.refresh_connection(user_id=user_id, provider="Slack")
    assert refreshed is not None
    assert refreshed.expires_at > 0.0
    assert refreshed.status == "CONNECTED"


@pytest.mark.asyncio
async def test_oauth_live_connection_health_check():
    user_id = "usr_phase2_2"
    await oauth_manager.handle_callback(user_id=user_id, provider="GitHub", code="github_code_456")

    res = await oauth_manager.test_live_connection(user_id, "GitHub")
    assert "is_connected" in res
    assert "latency_ms" in res
