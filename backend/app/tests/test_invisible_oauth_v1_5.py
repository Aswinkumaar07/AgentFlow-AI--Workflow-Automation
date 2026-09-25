import pytest
from app.agents.oauth_ai.oauth_manager import zero_touch_oauth_manager
from app.agents.oauth_ai.account_picker import account_picker, ConnectedAccount
from app.core.security import create_access_token


def test_invisible_oauth_auto_bind_single_account():
    account_picker.accounts["Slack"] = []
    acc = ConnectedAccount(
        account_id="acc_slack_1",
        provider="Slack",
        email_or_name="Engineering Workspace (#general)",
        status="active",
        is_default=True,
    )
    account_picker.add_or_update_account(acc)

    node = {
        "id": "step_slack",
        "provider": "Slack",
        "operation_id": "slack.chat.postMessage",
        "parameters": {},
    }
    result = zero_touch_oauth_manager.ensure_node_authenticated(node)
    assert result["is_authenticated"] is True
    assert result["auto_bound"] is True
    assert result["account_label"] == "Engineering Workspace (#general)"
    assert node["parameters"]["auth_status"] == "active"


def test_invisible_oauth_multiple_accounts_prompt():
    account_picker.accounts["Gmail"] = []
    acc1 = ConnectedAccount(
        account_id="acc_gmail_1",
        provider="Gmail",
        email_or_name="aswin@company.com",
        status="active",
        is_default=True,
    )
    acc2 = ConnectedAccount(
        account_id="acc_gmail_2",
        provider="Gmail",
        email_or_name="notifications@company.com",
        status="active",
        is_default=False,
    )
    account_picker.add_or_update_account(acc1)
    account_picker.add_or_update_account(acc2)

    node = {
        "id": "step_gmail",
        "provider": "Gmail",
        "operation_id": "gmail.messages.send",
        "parameters": {},
    }
    result = zero_touch_oauth_manager.ensure_node_authenticated(node)
    assert result["multiple_accounts"] is True
    assert len(result["accounts"]) == 2
    assert result["is_authenticated"] is True
    assert result["account_label"] == "aswin@company.com"


def test_invisible_oauth_zero_account_popup_trigger():
    account_picker.accounts["Stripe"] = []
    node = {
        "id": "step_custom",
        "provider": "Stripe",
        "operation_id": "stripe.charges.create",
        "parameters": {},
    }

    result = zero_touch_oauth_manager.ensure_node_authenticated(node)
    assert result["requires_oauth_popup"] is True
    assert result["is_authenticated"] is False


@pytest.mark.asyncio
async def test_populate_node_api_endpoint(async_client):
    account_picker.accounts["Slack"] = []
    acc = ConnectedAccount(
        account_id="acc_slack_api",
        provider="Slack",
        email_or_name="Engineering Workspace",
        status="active",
        is_default=True,
    )
    account_picker.add_or_update_account(acc)

    token = create_access_token("usr_1")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "node": {
            "id": "step_slack_1",
            "provider": "Slack",
            "operation_id": "slack.chat.postMessage",
            "parameters": {},
        }
    }

    res = await async_client.post("/api/v1/oauth-ai/populate-node", json=payload, headers=headers)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["success"] is True
    data = res_data["data"]
    assert data["is_authenticated"] is True
    assert data["node"]["parameters"]["auth_status"] == "active"
