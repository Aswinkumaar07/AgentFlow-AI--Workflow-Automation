import time
import pytest
from app.agents.oauth_ai import oauth_ai_service, connection_health_monitor, account_picker, ConnectedAccount


def test_invisible_oauth_auto_populate_gmail():
    account_picker.accounts["Google"] = []
    acc = ConnectedAccount(
        account_id="acc_gmail_1",
        provider="Google",
        email_or_name="aswinkumaar07@gmail.com",
        status="active",
        is_default=True,
    )
    account_picker.add_or_update_account(acc)

    node = {
        "id": "node_gmail_1",
        "provider": "Gmail",
        "operation_id": "gmail.messages.send",
        "parameters": {"subject": "Test"},
    }

    res = oauth_ai_service.populate_node_auth(node)
    assert res["is_authenticated"] is True
    assert res["requires_oauth_popup"] is False
    assert res["account_label"] == "aswinkumaar07@gmail.com"

    params = res["node"]["parameters"]
    assert params.get("auth_account_label") == "aswinkumaar07@gmail.com"
    assert params.get("auth_status") == "active"


def test_invisible_oauth_missing_provider_popup():
    node = {
        "id": "node_unknown_1",
        "provider": "UnconnectedApp",
        "operation_id": "unconnected.action",
    }

    res = oauth_ai_service.populate_node_auth(node)
    assert res["is_authenticated"] is True  # Non-OAuth generic provider auto-passes


def test_invisible_oauth_expired_token_auto_refresh():
    acc = ConnectedAccount(
        account_id="acc_expired_1",
        provider="Slack",
        email_or_name="Expired Workspace",
        status="expired",
        is_default=True,
        expires_at=int(time.time()) - 100,  # Expired
    )
    account_picker.add_or_update_account(acc)

    health = connection_health_monitor.check_connection_health("Slack")
    assert health["is_connected"] is True
    assert health["status"] in ("healthy", "active")
    assert health["expires_at"] > int(time.time())  # Auto-refreshed to future timestamp!


def test_get_all_connections_health():
    acc1 = ConnectedAccount(account_id="acc_1", provider="Google", email_or_name="user1@company.com", is_default=True)
    acc2 = ConnectedAccount(account_id="acc_2", provider="Slack", email_or_name="Slack Workspace", is_default=True)
    account_picker.add_or_update_account(acc1)
    account_picker.add_or_update_account(acc2)

    health_list = oauth_ai_service.get_all_connections_health()
    assert len(health_list) >= 2
    providers = [h["provider"] for h in health_list]
    assert "Google" in providers
    assert "Slack" in providers
