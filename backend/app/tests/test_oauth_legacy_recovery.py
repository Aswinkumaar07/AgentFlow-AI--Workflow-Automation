import pytest
import os
from unittest.mock import patch
from app.oauth.manager import OAuthManager, oauth_manager, recover_legacy_account_label
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
async def test_legacy_google_recovery_null_label():
    """
    A. Legacy Google recovery:
    Credential with account_label=None is repaired to aswinkumaar07@gmail.com
    from local persisted storage artifacts.
    """
    user_id = "usr_legacy_null"
    provider = "Google"
    access_tok = "secret_access_token_123"
    refresh_tok = "secret_refresh_token_456"

    cred = ConnectorCredentialModel(
        tenant_id=user_id,
        provider=provider,
        auth_type="OAuth2",
        access_token=access_tok,
        refresh_token=refresh_tok,
        token_expires_at=9999999999.0,
        scopes=["gmail.readonly"],
        account_label=None,
    )
    await secret_manager.set_secret(user_id, provider, cred)

    manager = OAuthManager()
    conns = await manager.get_user_connections(user_id)
    assert len(conns) == 1
    recovered_conn = conns[0]
    assert recovered_conn.account_label == "aswinkumaar07@gmail.com"

    # Verify secret_manager persisted label
    updated_secret = await secret_manager.get_secret(user_id, provider)
    assert updated_secret is not None
    assert updated_secret.account_label == "aswinkumaar07@gmail.com"


@pytest.mark.asyncio
async def test_synthetic_label_recovery():
    """
    B. Synthetic-label recovery:
    A credential labeled usr_1@google.com is repaired when a trustworthy
    locally persisted auth_account_label exists.
    """
    user_id = "usr_1"
    provider = "Google"

    cred = ConnectorCredentialModel(
        tenant_id=user_id,
        provider=provider,
        auth_type="OAuth2",
        access_token="tok_synthetic_google",
        refresh_token="ref_synthetic_google",
        account_label="usr_1@google.com",
    )
    await secret_manager.set_secret(user_id, provider, cred)

    manager = OAuthManager()
    acc_info = await manager.get_connected_account(user_id, provider)
    assert acc_info is not None
    assert acc_info["email"] == "aswinkumaar07@gmail.com"


@pytest.mark.asyncio
async def test_token_integrity_preserved():
    """
    C. Token integrity:
    access_token and refresh_token values are byte-for-byte unchanged before/after repair.
    """
    user_id = "usr_token_integrity"
    provider = "Google"
    raw_access = "EXACT_RAW_ACCESS_TOKEN_XYZ_987!"
    raw_refresh = "EXACT_RAW_REFRESH_TOKEN_ABC_321!"

    cred = ConnectorCredentialModel(
        tenant_id=user_id,
        provider=provider,
        auth_type="OAuth2",
        access_token=raw_access,
        refresh_token=raw_refresh,
        account_label=None,
    )
    await secret_manager.set_secret(user_id, provider, cred)

    manager = OAuthManager()
    await manager.get_user_connections(user_id)

    updated_secret = await secret_manager.get_secret(user_id, provider)
    assert updated_secret is not None
    assert updated_secret.access_token == raw_access
    assert updated_secret.refresh_token == raw_refresh


@pytest.mark.asyncio
async def test_recovery_idempotency():
    """
    D. Idempotency:
    Running recovery twice produces no duplicate credentials and no unnecessary modifications.
    """
    user_id = "usr_idempotence"
    provider = "Google"

    cred = ConnectorCredentialModel(
        tenant_id=user_id,
        provider=provider,
        auth_type="OAuth2",
        access_token="tok_idem",
        refresh_token="ref_idem",
        account_label=None,
    )
    await secret_manager.set_secret(user_id, provider, cred)

    manager1 = OAuthManager()
    conns_pass1 = await manager1.get_user_connections(user_id)
    assert len(conns_pass1) == 1

    manager2 = OAuthManager()
    conns_pass2 = await manager2.get_user_connections(user_id)
    assert len(conns_pass2) == 1
    assert conns_pass2[0].account_label == "aswinkumaar07@gmail.com"


@pytest.mark.asyncio
async def test_no_network_guarantee():
    """
    E. No-network guarantee:
    Recovery must not make network or external API requests.
    """
    user_id = "usr_no_net"
    provider = "Google"

    cred = ConnectorCredentialModel(
        tenant_id=user_id,
        provider=provider,
        auth_type="OAuth2",
        access_token="tok_nonet",
        account_label=None,
    )
    await secret_manager.set_secret(user_id, provider, cred)

    with patch("httpx.AsyncClient.post") as mock_post, patch("httpx.AsyncClient.get") as mock_get:
        manager = OAuthManager()
        await manager.get_user_connections(user_id)
        mock_post.assert_not_called()
        mock_get.assert_not_called()


@pytest.mark.asyncio
async def test_slack_safety_no_fake_email():
    """
    F. Slack safety:
    No fake Slack email or account identity is created from channel names (#general).
    Truthful display fallback "Slack Workspace" is used when no specific email label exists.
    """
    user_id = "usr_slack_safety"
    provider = "Slack"

    cred = ConnectorCredentialModel(
        tenant_id=user_id,
        provider=provider,
        auth_type="OAuth2",
        access_token="xoxb-test-token-12345",
        account_label="usr_1@slack.com",
    )
    await secret_manager.set_secret(user_id, provider, cred)

    # 1. Verify recover_legacy_account_label does NOT use #general or invent email
    lbl = recover_legacy_account_label("Slack")
    assert lbl is None or not lbl.startswith("#")

    # 2. Verify get_connected_account uses "Slack Workspace" truthful display fallback
    manager = OAuthManager()
    conn_info = await manager.get_connected_account(user_id, provider)
    assert conn_info is not None
    assert conn_info["email"] == "Slack Workspace"
    assert not conn_info["email"].startswith("#general")
    assert not conn_info["email"].startswith("usr_1@")

    # 3. Verify access_token remains byte-for-byte unchanged
    updated_secret = await secret_manager.get_secret(user_id, provider)
    assert updated_secret is not None
    assert updated_secret.access_token == "xoxb-test-token-12345"


@pytest.mark.asyncio
async def test_settings_api_identity_exposure():
    """
    G. Settings/API identity:
    After recovery, CredentialResolver and get_user_connections expose the real Google account label.
    """
    user_id = "usr_settings_api"
    provider = "Google"

    cred = ConnectorCredentialModel(
        tenant_id=user_id,
        provider=provider,
        auth_type="OAuth2",
        access_token="tok_settings_test",
        account_label="usr_1@google.com",
    )
    await secret_manager.set_secret(user_id, provider, cred)

    resolver = CredentialResolver()
    res = await resolver.resolve(provider, user_id=user_id)
    assert res["is_authenticated"] is True
    assert res["auth_account_label"] == "aswinkumaar07@gmail.com"
