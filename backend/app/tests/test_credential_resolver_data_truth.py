import pytest
import pytest_asyncio
from app.runtime.credential_resolver import credential_resolver
from app.connectors.security.secret_manager import secret_manager
from app.oauth.manager import oauth_manager, OAuthConnectionModel
from app.agents.oauth_ai.account_picker import account_picker, ConnectedAccount
from app.connectors.models import ConnectorCredentialModel


@pytest.fixture(autouse=True)
def cleanup_oauth_stores():
    """Clear in-memory stores before and after each test."""
    secret_manager._store.clear()
    oauth_manager._connections.clear()
    oauth_manager._user_metadata.clear()
    account_picker.accounts.clear()
    yield
    secret_manager._store.clear()
    oauth_manager._connections.clear()
    oauth_manager._user_metadata.clear()
    account_picker.accounts.clear()


@pytest.mark.asyncio
async def test_a_stale_account_picker_entry_returns_unbound():
    """Requirement A & C: Stale AccountPicker entry without SecretManager/OAuthManager credential MUST return unbound."""
    # Seed stale AccountPicker entry
    stale_acc = ConnectedAccount(
        account_id="conn_stale_12345",
        provider="Google",
        email_or_name="stale_user@gmail.com",
        status="active",
        is_default=True,
    )
    account_picker.add_or_update_account(stale_acc)

    # SecretManager & OAuthManager remain empty
    res_async = await credential_resolver.resolve("Google", "usr_1")
    res_sync = credential_resolver.resolve_sync("Google", "usr_1")

    # Assert account_picker entry is NEVER treated as authenticated
    assert res_async["is_authenticated"] is False
    assert res_async["auth_status"] == "unbound"
    assert res_async["credential_id"] is None
    assert res_async["auth_account_label"] is None

    assert res_sync["is_authenticated"] is False
    assert res_sync["auth_status"] == "unbound"
    assert res_sync["credential_id"] is None
    assert res_sync["auth_account_label"] is None


@pytest.mark.asyncio
async def test_b_valid_secret_manager_credential_returns_active():
    """Requirement B: Valid SecretManager credential returns ACTIVE and correct credential_id."""
    cred = ConnectorCredentialModel(
        tenant_id="usr_1",
        provider="Google",
        auth_type="OAuth2",
        access_token="valid_access_token_abc",
        refresh_token="valid_refresh_token_xyz",
        account_label="real_user@gmail.com",
    )
    await secret_manager.set_secret("usr_1", "Google", cred)

    res_async = await credential_resolver.resolve("Google", "usr_1")
    res_sync = credential_resolver.resolve_sync("Google", "usr_1")

    assert res_async["is_authenticated"] is True
    assert res_async["auth_status"] == "active"
    assert res_async["credential_id"] == "conn_google_usr_1"
    assert res_async["auth_account_label"] == "real_user@gmail.com"

    assert res_sync["is_authenticated"] is True
    assert res_sync["auth_status"] == "active"
    assert res_sync["credential_id"] == "conn_google_usr_1"
    assert res_sync["auth_account_label"] == "real_user@gmail.com"


@pytest.mark.asyncio
async def test_b2_valid_oauth_manager_connection_returns_active():
    """Requirement B: Valid OAuthManager connection returns ACTIVE."""
    conn = OAuthConnectionModel(
        id="conn_live_999",
        user_id="usr_1",
        provider="Google",
        access_token="live_token_123",
        expires_at=9999999999.0,
        scopes=["gmail.readonly"],
        status="CONNECTED",
    )
    oauth_manager._connections["usr_1:Google"] = conn
    oauth_manager._user_metadata["usr_1:Google"] = {"email": "live_user@gmail.com"}

    res_async = await credential_resolver.resolve("Google", "usr_1")
    res_sync = credential_resolver.resolve_sync("Google", "usr_1")

    assert res_async["is_authenticated"] is True
    assert res_async["auth_status"] == "active"
    assert res_async["credential_id"] == "conn_live_999"
    assert res_async["auth_account_label"] == "live_user@gmail.com"

    assert res_sync["is_authenticated"] is True
    assert res_sync["auth_status"] == "active"
    assert res_sync["credential_id"] == "conn_live_999"
    assert res_sync["auth_account_label"] == "live_user@gmail.com"


@pytest.mark.asyncio
async def test_d_async_and_sync_resolver_consistency():
    """Requirement D: resolve() and resolve_sync() behave 100% consistently across unbound, secret, and memory states."""
    # 1. Unbound state
    r1_async = await credential_resolver.resolve("Slack", "usr_1")
    r1_sync = credential_resolver.resolve_sync("Slack", "usr_1")
    assert r1_async == r1_sync

    # 2. Add stale AccountPicker entry only
    account_picker.add_or_update_account(ConnectedAccount(account_id="acc_slack", provider="Slack", email_or_name="slack_stale"))
    r2_async = await credential_resolver.resolve("Slack", "usr_1")
    r2_sync = credential_resolver.resolve_sync("Slack", "usr_1")
    assert r2_async == r2_sync
    assert r2_async["auth_status"] == "unbound"


@pytest.mark.asyncio
async def test_e_ai_generated_gmail_workflow_with_no_oauth_has_null_credential():
    """Requirement E: AI-generated Gmail workflow with no OAuth has credential_id null and auth_status unbound."""
    from app.api.v1.ai import generate_workflow
    from app.schemas.ai import AIGenerateRequest

    req = AIGenerateRequest(prompt="Get my latest Gmail email and summarize it")
    res = await generate_workflow(req, current_user=None)

    data = res.get("data") or {}
    wf_json = data.get("workflow_json") or {}
    nodes = wf_json.get("nodes") or []

    assert len(nodes) > 0
    gmail_nodes = [n for n in nodes if n.get("provider") in ["gmail", "Google"] or "gmail" in (n.get("operation") or "")]
    assert len(gmail_nodes) > 0

    for n in gmail_nodes:
        params = n.get("parameters") or (n.get("data", {}) if isinstance(n.get("data"), dict) else {}).get("parameters") or {}
        assert params.get("auth_status") == "unbound"
        assert params.get("credential_id") is None
        assert params.get("auth_account_label") is None
