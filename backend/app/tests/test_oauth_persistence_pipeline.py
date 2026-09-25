import pytest
import asyncio
from app.oauth.manager import oauth_manager
from app.connectors.security.secret_manager import secret_manager
from app.api.v1.credentials import list_user_credentials
from app.models.users import User


@pytest.mark.asyncio
async def test_oauth_persistence_pipeline_end_to_end(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "")

    user_id = "usr_test_persistence"
    provider = "Gmail"
    auth_code = "4/0AeaYSHC_test_code_12345"

    # 1. OAuth Callback execution
    conn = await oauth_manager.handle_callback(user_id=user_id, provider=provider, code=auth_code)
    assert conn is not None
    assert conn.status == "CONNECTED"
    assert conn.access_token is not None
    assert conn.refresh_token is not None

    # 2. Verify SecretManager Database Store row inserted and committed under 'google'
    all_secrets = await secret_manager.list_all_secrets(user_id)
    assert "google" in all_secrets
    secret = all_secrets["google"]
    assert secret.access_token == conn.access_token
    assert secret.refresh_token == conn.refresh_token

    # 3. Verify GET /api/v1/credentials endpoint returns exactly ONE Google credential
    test_user = User(id=user_id, email="aswin@company.com", is_active=True)
    res = await list_user_credentials(current_user=test_user)
    
    assert res.get("success") is True
    safe_creds = res.get("data", [])
    assert len(safe_creds) == 1

    google_cred = safe_creds[0]
    assert google_cred["provider"] == "Google"
    assert google_cred["account_label"] == "aswinkumaar07@gmail.com"
    assert google_cred["is_connected"] is True
    assert google_cred["status"] in ["healthy", "active"]
    assert google_cred["is_expired"] is False
    assert google_cred["expires_in_seconds"] > 0
