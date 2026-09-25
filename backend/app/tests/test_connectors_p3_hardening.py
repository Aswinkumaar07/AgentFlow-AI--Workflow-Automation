import time
import pytest
from app.connectors.manager import connector_manager
from app.connectors.models import ConnectorCredentialModel
from app.connectors.auth.oauth2 import oauth2_engine
from app.connectors.auth.refresh_manager import token_refresh_manager


@pytest.mark.asyncio
async def test_p3_all_6_target_connectors_execution():
    connectors = [
        ("Gmail", "gmail.messages.list", {"q": "is:unread"}),
        ("Google Drive", "drive.files.list", {"q": "name contains 'Invoice'"}),
        ("Google Sheets", "sheets.spreadsheets.values.get", {"spreadsheet_id": "sh_101", "range": "Sheet1!A1:B10"}),
        ("Slack", "slack.chat.postMessage", {"channel": "#dev-alerts", "text": "Hello Slack"}),
        ("GitHub", "github.issues.create", {"owner": "AgentFlow-AI", "repo": "TERRAWATCH", "title": "Test Issue"}),
        ("Generic REST API", "generic.http.request", {"url": "https://api.example.com/data", "method": "GET"}),
    ]

    for provider, op_id, params in connectors:
        res = await connector_manager.execute(
            provider=provider,
            operation_id=op_id,
            parameters=params,
            tenant_id="usr_p3_test",
        )
        assert res.success is True
        assert res.operation_id == op_id
        assert res.latency_ms >= 0.0
        assert res.status_code in [200, 201]


@pytest.mark.asyncio
async def test_p3_oauth_token_expiration_and_refresh():
    # Expired credential model
    expired_creds = ConnectorCredentialModel(
        tenant_id="usr_oauth_test",
        provider="Gmail",
        access_token="expired_token_123",
        refresh_token="valid_refresh_token_789",
        token_expires_at=time.time() - 100.0,
    )

    assert oauth2_engine.is_token_expired(expired_creds) is True

    valid_creds = await token_refresh_manager.get_valid_credentials(expired_creds)
    assert valid_creds.access_token.startswith("refreshed_")
    assert valid_creds.token_expires_at > time.time()
    assert oauth2_engine.is_token_expired(valid_creds) is False


@pytest.mark.asyncio
async def test_p3_pagination_token_handling():
    # Test Gmail pagination parameter pass-through
    res_gmail = await connector_manager.execute(
        provider="Gmail",
        operation_id="gmail.messages.list",
        parameters={"pageToken": "token_page_2", "maxResults": 10},
    )
    assert res_gmail.success is True

    # Test Slack pagination parameter pass-through
    res_slack = await connector_manager.execute(
        provider="Slack",
        operation_id="slack.conversations.list",
        parameters={"cursor": "cursor_next_page", "limit": 20},
    )
    assert res_slack.success is True


@pytest.mark.asyncio
async def test_p3_connector_telemetry_accuracy():
    res = await connector_manager.execute(
        provider="Generic REST API",
        operation_id="generic.http.request",
        parameters={"url": "https://api.example.com/test", "method": "POST"},
    )

    assert res.latency_ms >= 0.0
    assert isinstance(res.retries_used, int)
    assert res.operation_id == "generic.http.request"
