import pytest
from unittest.mock import patch, AsyncMock
from app.oauth.manager import OAuthManager, oauth_manager
from app.agents.oauth_ai.account_picker import account_picker
from app.connectors.models import ConnectorCredentialModel
from app.connectors.security.secret_manager import secret_manager
from app.runtime.credential_resolver import CredentialResolver


@pytest.fixture(autouse=True)
def reset_stores():
    oauth_manager._connections.clear()
    oauth_manager._user_metadata.clear()
    account_picker.accounts.clear()
    yield
    oauth_manager._connections.clear()
    oauth_manager._user_metadata.clear()
    account_picker.accounts.clear()


@pytest.mark.asyncio
async def test_oauth_callback_persists_account_label():
    """
    A. Test OAuth callback persistence:
    Given a successful OAuth callback returning a real user email,
    ConnectorCredentialModel.account_label is persisted with that email.
    """
    manager = OAuthManager()
    user_id = "test_user_a"
    provider = "Google"
    code = "code_test_auth_callback"

    with patch("httpx.AsyncClient.post") as mock_post, patch("httpx.AsyncClient.get") as mock_get:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json = lambda: {
            "access_token": "mock_acc_tok",
            "refresh_token": "mock_ref_tok",
            "expires_in": 3600,
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json = lambda: {
            "email": "user_a@example.com",
            "name": "User A",
        }

        conn = await manager.handle_callback(user_id=user_id, provider=provider, code=code)
        assert conn is not None
        assert conn.account_label == "user_a@example.com"

        secret = await secret_manager.get_secret(user_id, provider)
        assert secret is not None
        assert secret.account_label == "user_a@example.com"


@pytest.mark.asyncio
async def test_restart_persistence_returns_real_email():
    """
    B. Test restart persistence:
    Persist a credential with account_label="real@example.com".
    Reinitialize OAuthManager.
    Verify get_user_connections()/get_connected_account() returns "real@example.com".
    """
    user_id = "test_user_b"
    provider = "Google"

    cred = ConnectorCredentialModel(
        tenant_id=user_id,
        provider=provider,
        auth_type="OAuth2",
        access_token="tok_real_b",
        refresh_token="ref_real_b",
        token_expires_at=9999999999.0,
        scopes=["email"],
        account_label="real@example.com",
    )
    await secret_manager.set_secret(user_id, provider, cred)

    fresh_manager = OAuthManager()
    acc_info = await fresh_manager.get_connected_account(user_id, provider)
    assert acc_info is not None
    assert acc_info["email"] == "real@example.com"

    conns = await fresh_manager.get_user_connections(user_id)
    assert len(conns) >= 1
    target_conn = next(c for c in conns if c.provider.lower() == provider.lower())
    assert target_conn.account_label == "real@example.com"


@pytest.mark.asyncio
async def test_credential_resolver_prefers_persisted_account_label():
    """
    C. Test CredentialResolver:
    Verify resolve() returns the persisted account label rather than usr_1@provider.com.
    """
    user_id = "test_user_c"
    provider = "Slack"

    cred = ConnectorCredentialModel(
        tenant_id=user_id,
        provider=provider,
        auth_type="OAuth2",
        access_token="tok_slack_c",
        scopes=["chat:write"],
        account_label="workspace_c@slack.com",
    )
    await secret_manager.set_secret(user_id, provider, cred)

    resolver = CredentialResolver()
    res = await resolver.resolve(provider, user_id=user_id)
    assert res["is_authenticated"] is True
    assert res["auth_account_label"] == "workspace_c@slack.com"

    res_sync = resolver.resolve_sync(provider, user_id=user_id)
    assert res_sync["is_authenticated"] is True
    assert res_sync["auth_account_label"] == "workspace_c@slack.com"


@pytest.mark.asyncio
async def test_missing_label_compatibility_fallback():
    """
    D. Test missing-label compatibility:
    Verify credentials without account_label still use the existing fallback behavior and do not break.
    """
    user_id = "test_user_d"
    provider = "Stripe"

    cred = ConnectorCredentialModel(
        tenant_id=user_id,
        provider=provider,
        auth_type="OAuth2",
        access_token="tok_no_label",
        account_label=None,
    )
    await secret_manager.set_secret(user_id, provider, cred)

    resolver = CredentialResolver()
    res = await resolver.resolve(provider, user_id=user_id)
    assert res["is_authenticated"] is True
    assert res["auth_account_label"] == f"{user_id}@stripe.com"


@pytest.mark.asyncio
async def test_no_duplicate_credentials_on_hydration():
    """
    E. Test no duplicate credentials:
    Verify hydration does not create another OAuth connection or duplicate entries.
    """
    user_id = "test_user_e"
    provider = "Google"

    cred = ConnectorCredentialModel(
        tenant_id=user_id,
        provider=provider,
        auth_type="OAuth2",
        access_token="tok_dup_test",
        account_label="dup_test@example.com",
    )
    await secret_manager.set_secret(user_id, provider, cred)

    fresh_manager = OAuthManager()
    await fresh_manager.get_user_connections(user_id)
    conns_1 = await fresh_manager.get_user_connections(user_id)
    conns_2 = await fresh_manager.get_user_connections(user_id)

    google_conns = [c for c in conns_2 if c.provider.lower() == "google" and c.user_id == user_id]
    assert len(google_conns) == 1
