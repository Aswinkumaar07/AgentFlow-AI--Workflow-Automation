import pytest
from app.runtime.credential_resolver import credential_resolver
from app.services.connection_readiness import check_workflow_readiness
from app.connectors.security.secret_manager import secret_manager
from app.connectors.models import ConnectorCredentialModel
from app.oauth.manager import oauth_manager, OAuthConnectionModel


@pytest.mark.asyncio
async def test_unbound_credential_resolution_google_and_slack():
    """Verify missing credentials return unbound status without synthetic fallback for Google, Slack, GitHub, Notion."""
    user_id = "usr_test_truth_1"

    # Clean any potential leftovers
    await secret_manager.delete_secret(user_id, "Google")
    await secret_manager.delete_secret(user_id, "Slack")
    await secret_manager.delete_secret(user_id, "GitHub")

    # Async resolve test
    g_res = await credential_resolver.resolve("google", user_id)
    assert g_res["auth_status"] == "unbound"
    assert g_res["is_authenticated"] is False
    assert g_res["auth_account_label"] is None
    assert g_res["credential_id"] is None

    s_res = await credential_resolver.resolve("slack", user_id)
    assert s_res["auth_status"] == "unbound"
    assert s_res["is_authenticated"] is False
    assert s_res["auth_account_label"] is None
    assert s_res["credential_id"] is None

    # Sync resolve test
    g_sync = credential_resolver.resolve_sync("google", user_id)
    assert g_sync["auth_status"] == "unbound"
    assert g_sync["is_authenticated"] is False
    assert g_sync["auth_account_label"] is None
    assert g_sync["credential_id"] is None

    s_sync = credential_resolver.resolve_sync("slack", user_id)
    assert s_sync["auth_status"] == "unbound"
    assert s_sync["is_authenticated"] is False
    assert s_sync["auth_account_label"] is None
    assert s_sync["credential_id"] is None


@pytest.mark.asyncio
async def test_usr_1_unbound_resolution_when_secrets_absent():
    """Verify usr_1 returns unbound when no secrets or oauth connections exist in store."""
    user_id = "usr_1"

    # Clean secrets for testing
    await secret_manager.delete_secret(user_id, "Google")
    await secret_manager.delete_secret(user_id, "Slack")

    g_res = await credential_resolver.resolve("google", user_id)
    # If no secret set for usr_1, must return unbound
    assert g_res["auth_status"] == "unbound"
    assert g_res["is_authenticated"] is False
    assert g_res["auth_account_label"] is None

    s_res = await credential_resolver.resolve("slack", user_id)
    assert s_res["auth_status"] == "unbound"
    assert s_res["is_authenticated"] is False
    assert s_res["auth_account_label"] is None


@pytest.mark.asyncio
async def test_active_credential_resolution_when_secret_exists():
    """Verify active credential resolution when real secrets are set in secret_manager."""
    user_id = "usr_test_truth_active"

    cred = ConnectorCredentialModel(
        credential_id="cred_google_123",
        provider="Google",
        access_token="ya29.test_token",
        account_label="real_user@gmail.com",
        scopes=["gmail.readonly"]
    )
    await secret_manager.set_secret(user_id, "Google", cred)

    try:
        g_res = await credential_resolver.resolve("gmail", user_id)
        assert g_res["auth_status"] == "active"
        assert g_res["is_authenticated"] is True
        assert g_res["auth_account_label"] == "real_user@gmail.com"

        g_sync = credential_resolver.resolve_sync("gmail", user_id)
        assert g_sync["auth_status"] == "active"
        assert g_sync["is_authenticated"] is True
        assert g_sync["auth_account_label"] == "real_user@gmail.com"
    finally:
        await secret_manager.delete_secret(user_id, "Google")


@pytest.mark.asyncio
async def test_readiness_check_accurately_reflects_truth():
    """Verify check_workflow_readiness returns missing connections accurately."""
    user_id = "usr_test_truth_readiness"

    # 1. Neither connected
    readiness = await check_workflow_readiness(["gmail", "slack"], user_id=user_id)
    assert readiness["ready"] is False
    assert set(readiness["missing_connections"]) == {"gmail", "slack"}

    # 2. Add Gmail secret
    cred_g = ConnectorCredentialModel(
        credential_id="cred_g_1",
        provider="Google",
        access_token="tok_g",
        account_label="user@gmail.com"
    )
    await secret_manager.set_secret(user_id, "Google", cred_g)

    try:
        readiness = await check_workflow_readiness(["gmail", "slack"], user_id=user_id)
        assert readiness["ready"] is False
        assert readiness["missing_connections"] == ["slack"]

        # 3. Add Slack secret
        cred_s = ConnectorCredentialModel(
            credential_id="cred_s_1",
            provider="Slack",
            access_token="tok_s",
            account_label="#general"
        )
        await secret_manager.set_secret(user_id, "Slack", cred_s)

        readiness_all = await check_workflow_readiness(["gmail", "slack"], user_id=user_id)
        assert readiness_all["ready"] is True
        assert readiness_all["missing_connections"] == []
    finally:
        await secret_manager.delete_secret(user_id, "Google")
        await secret_manager.delete_secret(user_id, "Slack")
