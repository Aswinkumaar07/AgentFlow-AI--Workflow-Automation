import pytest
from app.runtime.credential_resolver import credential_resolver
from app.agents.planner.planner_v4 import intelligent_planner_v4
from app.connectors.security.secret_manager import secret_manager
from app.connectors.models import ConnectorCredentialModel
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_credential_resolver_google():
    # Setup active Google credential in SecretManager
    cred = ConnectorCredentialModel(
        tenant_id="usr_1",
        provider="Google",
        auth_type="OAuth2",
        access_token="valid_access_token_123",
        account_label="aswinkumaar07@gmail.com",
    )
    await secret_manager.set_secret("usr_1", "Google", cred)

    resolved = await credential_resolver.resolve("Gmail", "usr_1")
    assert resolved["is_authenticated"] is True
    assert resolved["auth_provider"] == "Google"
    assert resolved["auth_account_label"] == "aswinkumaar07@gmail.com"
    assert resolved["auth_status"] == "active"
    assert resolved["credential_id"] is not None


def test_planner_v4_prepopulates_oauth_node_parameters():
    prompt = "Send good night email to john@example.com"
    plan_res = intelligent_planner_v4.plan(prompt)
    assert plan_res.workflow_graph is not None

    nodes = plan_res.workflow_graph.get("nodes", [])
    assert len(nodes) >= 1

    gmail_node = nodes[0]
    params = gmail_node.get("parameters", {})

    assert params.get("to") == "john@example.com"
    assert "Good Night" in params.get("subject", "")
    assert params.get("auth_provider") == "Google"
    assert params.get("auth_account_label") == "aswinkumaar07@gmail.com"
    assert params.get("auth_status") == "active"
    assert params.get("credential_id") is not None


@pytest.mark.asyncio
async def test_ai_generate_endpoint_prepopulates_oauth(async_client):
    token = create_access_token("usr_1")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"prompt": "Send good night email to john@example.com"}
    res = await async_client.post("/api/v1/ai/generate", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]

    wf_json = data.get("workflow_json", {})
    nodes = wf_json.get("nodes", [])
    assert len(nodes) >= 1

    node_params = nodes[0].get("parameters", {})
    assert node_params.get("auth_provider") == "Google"
    assert node_params.get("auth_account_label") == "aswinkumaar07@gmail.com"
    assert node_params.get("auth_status") == "active"
