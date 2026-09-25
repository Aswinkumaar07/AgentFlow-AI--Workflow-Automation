import pytest
from app.runtime.credential_resolver import credential_resolver
from app.services.connection_readiness import check_workflow_readiness
from app.connectors.security.secret_manager import secret_manager
from app.connectors.models import ConnectorCredentialModel


@pytest.mark.asyncio
async def test_slack_unbound_with_target_channel_not_connected():
    """Requirement 6A & 6H: Slack node with channel #all-agentflow-ai and null credential is UNBOUND, not connected."""
    user_id = "usr_test_vis_1"

    # Ensure no secrets exist
    await secret_manager.delete_secret(user_id, "Slack")
    await secret_manager.delete_secret(user_id, "GitHub")

    res_slack = await credential_resolver.resolve("slack", user_id)
    assert res_slack["auth_status"] == "unbound"
    assert res_slack["credential_id"] is None
    assert res_slack["is_authenticated"] is False

    readiness = await check_workflow_readiness(["github", "slack"], user_id=user_id)
    assert readiness["ready"] is False
    assert set(readiness["missing_connections"]) == {"github", "slack"}


@pytest.mark.asyncio
async def test_case_insensitive_provider_resolution():
    """Requirement 6B: Lowercase 'slack' and Capitalized 'Slack' both resolve accurately."""
    user_id = "usr_test_vis_2"

    res_lower = await credential_resolver.resolve("slack", user_id)
    res_upper = await credential_resolver.resolve("Slack", user_id)

    assert res_lower["auth_status"] == "unbound"
    assert res_upper["auth_status"] == "unbound"
    assert res_lower["auth_provider"] == "Slack"
    assert res_upper["auth_provider"] == "Slack"


@pytest.mark.asyncio
async def test_real_connected_account_resolution():
    """Requirement 6C & 6G: Connected Slack account with valid secret returns active status."""
    user_id = "usr_test_vis_connected"

    cred = ConnectorCredentialModel(
        credential_id="conn_slack_real_123",
        provider="Slack",
        access_token="xoxb-test-token",
        account_label="#all-agentflow-ai",
        scopes=["slack.chat:write"]
    )
    await secret_manager.set_secret(user_id, "Slack", cred)

    try:
        res = await credential_resolver.resolve("slack", user_id)
        assert res["auth_status"] == "active"
        assert res["credential_id"] == f"conn_slack_{user_id}"
        assert res["is_authenticated"] is True
    finally:
        await secret_manager.delete_secret(user_id, "Slack")


@pytest.mark.asyncio
async def test_github_unbound_resolution():
    """Requirement 6D: GitHub with no credential returns unbound / missing connection."""
    user_id = "usr_test_vis_gh"

    await secret_manager.delete_secret(user_id, "GitHub")
    res = await credential_resolver.resolve("github", user_id)

    assert res["auth_status"] == "unbound"
    assert res["credential_id"] is None
    assert res["is_authenticated"] is False


@pytest.mark.asyncio
async def test_existing_gmail_connected_resolution():
    """Requirement 6F: Connected Gmail account with valid secret returns active status."""
    user_id = "usr_test_vis_gmail"

    cred = ConnectorCredentialModel(
        credential_id="conn_gmail_real_456",
        provider="Google",
        access_token="ya29.test_token",
        account_label="aswinkumaar07@gmail.com",
        scopes=["gmail.readonly"]
    )
    await secret_manager.set_secret(user_id, "Google", cred)

    try:
        res = await credential_resolver.resolve("gmail", user_id)
        assert res["auth_status"] == "active"
        assert res["is_authenticated"] is True
        assert res["auth_account_label"] == "aswinkumaar07@gmail.com"
    finally:
        await secret_manager.delete_secret(user_id, "Google")
