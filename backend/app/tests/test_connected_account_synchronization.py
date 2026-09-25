import pytest
import time
from app.oauth.manager import oauth_manager
from app.agents.oauth_ai.account_picker import account_picker, ConnectedAccount


@pytest.mark.asyncio
async def test_no_placeholder_account_returns_none_when_unconnected():
    acc = await oauth_manager.get_connected_account(user_id="usr_unconnected_test", provider="Gmail")
    assert acc is None


@pytest.mark.asyncio
async def test_account_synchronization_displays_full_metadata():
    user_id = "usr_sync_test"
    provider = "Gmail"

    # Simulate callback binding real account
    conn = await oauth_manager.handle_callback(user_id=user_id, provider=provider, code="test_code_xyz")
    assert conn is not None

    acc = await oauth_manager.get_connected_account(user_id=user_id, provider=provider)
    assert acc is not None
    assert "email" in acc
    assert "avatar" in acc
    assert "provider" in acc
    assert "scopes" in acc
    assert "expires_at" in acc
    assert "status" in acc

    assert acc["provider"] == "Google"
    assert acc["status"] == "CONNECTED"
    assert len(acc["scopes"]) >= 1


def test_account_picker_multi_account_and_auto_select_logic():
    provider = "Slack"
    account_picker.accounts[provider] = []

    # 0 Accounts -> returns None
    assert account_picker.get_default_account(provider) is None

    # 1 Account -> auto select
    acc1 = ConnectedAccount(
        account_id="conn_1",
        provider=provider,
        email_or_name="real_user_1@gmail.com",
        status="active",
        is_default=True,
    )
    account_picker.add_or_update_account(acc1)

    selected = account_picker.get_default_account(provider)
    assert selected is not None
    assert selected.email_or_name == "real_user_1@gmail.com"

    # 2 Accounts -> multi account list available
    acc2 = ConnectedAccount(
        account_id="conn_2",
        provider=provider,
        email_or_name="real_user_2@gmail.com",
        status="active",
        is_default=False,
    )
    account_picker.add_or_update_account(acc2)

    accounts = account_picker.list_accounts(provider)
    assert len(accounts) == 2

    # Switch default account
    account_picker.set_default(provider, "conn_2")
    new_selected = account_picker.get_default_account(provider)
    assert new_selected.email_or_name == "real_user_2@gmail.com"
