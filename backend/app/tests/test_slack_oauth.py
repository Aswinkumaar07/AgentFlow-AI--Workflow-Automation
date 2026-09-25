import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException
from app.core.config import settings
from app.oauth.manager import OAuthManager, oauth_manager
from app.connectors.providers.slack.adapter import SlackAdapter
from app.connectors.models import ConnectorRequestModel, ConnectorCredentialModel
from app.runtime.credential_resolver import CredentialResolver
from app.connectors.security.secret_manager import secret_manager
from app.agents.oauth_ai.account_picker import account_picker

@pytest.fixture(autouse=True)
def reset_slack_oauth_state():
    account_picker.accounts.clear()
    oauth_manager._connections.clear()
    secret_manager._store.clear()
    yield
    account_picker.accounts.clear()
    oauth_manager._connections.clear()
    secret_manager._store.clear()

@pytest.mark.asyncio
async def test_slack_oauth_missing_client_id_raises_error():
    """Test A: When SLACK_CLIENT_ID is missing/empty, get_login_url must raise HTTPException 500."""
    with patch.object(settings, "SLACK_CLIENT_ID", ""):
        with pytest.raises(HTTPException) as exc_info:
            oauth_manager.get_login_url("slack", user_id="usr_1")
        assert exc_info.value.status_code == 500
        assert "Slack OAuth is not configured" in exc_info.value.detail
        assert "SLACK_CLIENT_ID" in exc_info.value.detail

@pytest.mark.asyncio
async def test_slack_oauth_valid_config_generates_correct_url():
    """Test B: Valid Slack configuration uses SLACK_CLIENT_ID and SLACK_REDIRECT_URI."""
    test_client_id = "123456789.987654321"
    test_redirect_uri = "http://127.0.0.1:8000/api/v1/oauth/slack/callback"
    
    with patch.object(settings, "SLACK_CLIENT_ID", test_client_id), \
         patch.object(settings, "SLACK_REDIRECT_URI", test_redirect_uri), \
         patch.object(settings, "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/oauth/google/callback"):
        
        url = oauth_manager.get_login_url("slack", user_id="usr_1")
        assert url.startswith("https://slack.com/oauth/v2/authorize?")
        assert f"client_id={test_client_id}" in url
        assert "redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Fapi%2Fv1%2Foauth%2Fslack%2Fcallback" in url
        assert "google" not in url.lower()
        assert "scope=chat%3Awrite%2Cchannels%3Aread" in url

@pytest.mark.asyncio
async def test_google_oauth_regression_remains_unchanged():
    """Test C: Google OAuth URL generation remains completely unchanged."""
    url = oauth_manager.get_login_url("google", user_id="usr_1")
    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "client_id=" in url
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fapi%2Fv1%2Foauth%2Fgoogle%2Fcallback" in url

@pytest.mark.asyncio
async def test_slack_oauth_callback_success_stores_credentials():
    """Test D: Successful Slack OAuth callback stores real access token and resolves cleanly."""
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "ok": True,
        "access_token": "xoxb-test-real-token-12345",
        "team": {"id": "T12345", "name": "Agentflow Slack Team"}
    }
    
    with patch.object(settings, "SLACK_CLIENT_ID", "test-slack-id"), \
         patch.object(settings, "SLACK_CLIENT_SECRET", "test-slack-secret"), \
         patch.object(settings, "SLACK_REDIRECT_URI", "http://127.0.0.1:8000/api/v1/oauth/slack/callback"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_res):
        
        conn = await oauth_manager.handle_callback(user_id="usr_test_slack_success", provider="slack", code="valid_slack_code")
        assert conn.provider == "Slack"
        assert conn.access_token == "xoxb-test-real-token-12345"
        assert conn.status == "CONNECTED"
        assert conn.scopes == ["chat:write", "channels:read"]
        
        # Check AccountPicker
        acc = account_picker.get_default_account("Slack")
        assert acc is not None
        assert acc.access_token == "xoxb-test-real-token-12345"
        
        # Check CredentialResolver
        resolver = CredentialResolver()
        resolved = await resolver.resolve("Slack", user_id="usr_test_slack_success")
        assert resolved["is_authenticated"] is True
        assert resolved["auth_status"] == "active"
        assert resolved["auth_provider"] == "Slack"

        # Clean up test state
        account_picker.accounts["Slack"] = []
        await secret_manager.delete_secret("usr_test_slack_success", "Slack")

@pytest.mark.asyncio
async def test_slack_oauth_callback_failure_raises_400_and_no_dummy_token():
    """Test E: When Slack returns ok=False (e.g. invalid_client_secret), callback fails with 400 and NO dummy token is stored."""
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "ok": False,
        "error": "invalid_client_secret"
    }
    
    with patch.object(settings, "SLACK_CLIENT_ID", "test-slack-id"), \
         patch.object(settings, "SLACK_CLIENT_SECRET", ""), \
         patch.object(settings, "SLACK_REDIRECT_URI", "http://127.0.0.1:8000/api/v1/oauth/slack/callback"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_res):
        
        with pytest.raises(HTTPException) as exc_info:
            await oauth_manager.handle_callback(user_id="usr_failed_slack", provider="slack", code="invalid_code")
        
        assert exc_info.value.status_code == 400
        assert "Slack OAuth token exchange failed" in exc_info.value.detail

        secret = await secret_manager.get_secret("usr_failed_slack", "Slack")
        assert secret is None

@pytest.mark.asyncio
async def test_slack_oauth_callback_missing_access_token_raises_400():
    """Test F: When Slack returns ok=True but access_token is empty, callback raises 400 and does NOT persist credentials."""
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "ok": True,
        "access_token": "",
        "team": {}
    }
    
    with patch.object(settings, "SLACK_CLIENT_ID", "test-slack-id"), \
         patch.object(settings, "SLACK_CLIENT_SECRET", "test-slack-secret"), \
         patch.object(settings, "SLACK_REDIRECT_URI", "http://127.0.0.1:8000/api/v1/oauth/slack/callback"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_res):
        
        with pytest.raises(HTTPException) as exc_info:
            await oauth_manager.handle_callback(user_id="usr_empty_token", provider="slack", code="code_empty_token")
        
        assert exc_info.value.status_code == 400
        assert "Slack OAuth token exchange failed" in exc_info.value.detail

        secret = await secret_manager.get_secret("usr_empty_token", "Slack")
        assert secret is None

@pytest.mark.asyncio
async def test_slack_adapter_missing_credential_fails():
    """Test PART 5.F: Missing credential causes SlackAdapter to return success=False (no fake success)."""
    account_picker.accounts["Slack"] = []
    adapter = SlackAdapter()
    req = ConnectorRequestModel(
        provider="Slack",
        operation_id="slack.chat.postMessage",
        tenant_id="usr_no_slack_token",
        parameters={"channel": "#general", "text": "Hello"}
    )
    res = await adapter.execute_operation(req, credentials=None)
    assert res.success is False
    assert res.status_code == 401
    assert "Missing access token" in res.error_message or "not connected" in res.error_message
    assert res.data.get("ok") is False

@pytest.mark.asyncio
async def test_slack_adapter_api_error_fails():
    """Test PART 5.B: When Slack API returns ok=False, adapter returns success=False without mock fallback."""
    adapter = SlackAdapter()
    cred = ConnectorCredentialModel(
        tenant_id="usr_1",
        provider="Slack",
        auth_type="OAuth2",
        access_token="xoxb-test-invalid-token",
        scopes=["chat:write", "channels:read"]
    )
    req = ConnectorRequestModel(
        provider="Slack",
        operation_id="slack.chat.postMessage",
        tenant_id="usr_1",
        parameters={"channel": "C12345678", "text": "Test"}
    )
    
    with patch("app.connectors.providers.slack.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": False, "error": "invalid_auth"}
        res = await adapter.execute_operation(req, credentials=cred)
        assert res.success is False
        assert res.status_code == 401
        assert "invalid_auth" in res.error_message
        assert res.data.get("ok") is False

@pytest.mark.asyncio
async def test_slack_adapter_channel_resolution_success_with_and_without_hash():
    """Test PART 5.A, D, E: #all-agentflow-ai and all-agentflow-ai resolve to C999888777 via conversations.list(types=public_channel)."""
    adapter = SlackAdapter()
    cred = ConnectorCredentialModel(
        tenant_id="usr_1",
        provider="Slack",
        auth_type="OAuth2",
        access_token="xoxb-valid-test-token",
        scopes=["chat:write", "channels:read"]
    )

    requested_params_list = []

    async def mock_connection_request(method, url, headers, json_data=None, params=None, timeout=30.0):
        if "auth.test" in url:
            return {"ok": True, "team": "Test Team", "team_id": "T123", "user": "Test User", "user_id": "U123"}
        if "conversations.list" in url:
            requested_params_list.append(params)
            return {
                "ok": True,
                "channels": [
                    {"id": "C999888777", "name": "all-agentflow-ai", "is_member": True, "is_archived": False},
                    {"id": "C111222333", "name": "general", "is_member": True, "is_archived": False}
                ]
            }
        if "chat.postMessage" in url:
            return {
                "ok": True,
                "channel": json_data.get("channel"),
                "ts": "1726100000.000200",
                "message": {"text": json_data.get("text")}
            }
        return {"ok": False, "error": "unknown_endpoint"}

    with patch("app.connectors.providers.slack.adapter.connection_pool.request", side_effect=mock_connection_request):
        # Test input with '#'
        req_with_hash = ConnectorRequestModel(
            provider="Slack",
            operation_id="slack.chat.postMessage",
            tenant_id="usr_1",
            parameters={"channel": "#all-agentflow-ai", "text": "Resolved test with hash"}
        )
        res_with_hash = await adapter.execute_operation(req_with_hash, credentials=cred)
        assert res_with_hash.success is True
        assert res_with_hash.data.get("channel") == "C999888777"

        # Test input without '#'
        req_no_hash = ConnectorRequestModel(
            provider="Slack",
            operation_id="slack.chat.postMessage",
            tenant_id="usr_1",
            parameters={"channel": "all-agentflow-ai", "text": "Resolved test without hash"}
        )
        res_no_hash = await adapter.execute_operation(req_no_hash, credentials=cred)
        assert res_no_hash.success is True
        assert res_no_hash.data.get("channel") == "C999888777"

        # Verify conversations.list requested types=public_channel only
        for p in requested_params_list:
            assert p.get("types") == "public_channel"
            assert p.get("limit") == 200

@pytest.mark.asyncio
async def test_slack_adapter_channel_resolution_pagination_found_on_later_page():
    """Test pagination: channel found on page 2 using response_metadata.next_cursor."""
    adapter = SlackAdapter()
    cred = ConnectorCredentialModel(
        tenant_id="usr_1",
        provider="Slack",
        auth_type="OAuth2",
        access_token="xoxb-valid-test-token",
        scopes=["chat:write", "channels:read"]
    )
    req = ConnectorRequestModel(
        provider="Slack",
        operation_id="slack.chat.postMessage",
        tenant_id="usr_1",
        parameters={"channel": "#all-agentflow-ai", "text": "Pagination test"}
    )

    page_requests = []

    async def mock_connection_request(method, url, headers, json_data=None, params=None, timeout=30.0):
        if "auth.test" in url:
            return {"ok": True, "team": "Test Team", "team_id": "T123"}
        if "conversations.list" in url:
            page_requests.append(params.get("cursor", ""))
            if not params.get("cursor"):
                return {
                    "ok": True,
                    "channels": [{"id": "C111", "name": "general", "is_member": True, "is_archived": False}],
                    "response_metadata": {"next_cursor": "cursor_page_2"}
                }
            elif params.get("cursor") == "cursor_page_2":
                return {
                    "ok": True,
                    "channels": [{"id": "C222", "name": "all-agentflow-ai", "is_member": False, "is_archived": False}],
                    "response_metadata": {"next_cursor": ""}
                }
        if "chat.postMessage" in url:
            return {
                "ok": True,
                "channel": json_data.get("channel"),
                "ts": "1726100000.000201"
            }
        return {"ok": False, "error": "unknown_endpoint"}

    with patch("app.connectors.providers.slack.adapter.connection_pool.request", side_effect=mock_connection_request):
        res = await adapter.execute_operation(req, credentials=cred)
        assert res.success is True
        assert res.data.get("channel") == "C222"
        assert page_requests == ["", "cursor_page_2"]

@pytest.mark.asyncio
async def test_slack_adapter_channel_resolution_missing_channel_fails_cleanly():
    """Test PART 5.B: When public channel does not exist, adapter fails cleanly with status_code=400 and DOES NOT attempt postMessage."""
    adapter = SlackAdapter()
    cred = ConnectorCredentialModel(
        tenant_id="usr_1",
        provider="Slack",
        auth_type="OAuth2",
        access_token="xoxb-valid-test-token",
        scopes=["chat:write", "channels:read"]
    )
    req = ConnectorRequestModel(
        provider="Slack",
        operation_id="slack.chat.postMessage",
        tenant_id="usr_1",
        parameters={"channel": "#non-existent-channel", "text": "Will fail resolution"}
    )

    post_message_called = False

    async def mock_connection_request(method, url, headers, json_data=None, params=None, timeout=30.0):
        nonlocal post_message_called
        if "auth.test" in url:
            return {"ok": True, "team": "Test Team"}
        if "conversations.list" in url:
            return {
                "ok": True,
                "channels": [{"id": "C111222333", "name": "general"}],
                "response_metadata": {"next_cursor": ""}
            }
        if "chat.postMessage" in url:
            post_message_called = True
            return {"ok": True, "ts": "12345"}
        return {"ok": False, "error": "unknown_endpoint"}

    with patch("app.connectors.providers.slack.adapter.connection_pool.request", side_effect=mock_connection_request):
        res = await adapter.execute_operation(req, credentials=cred)
        assert res.success is False
        assert res.status_code == 400
        assert "Slack channel not found: non-existent-channel" in res.error_message
        assert post_message_called is False

@pytest.mark.asyncio
async def test_slack_adapter_channel_resolution_missing_scope_fails_cleanly_without_fallback():
    """Test PART 5.C: When conversations.list returns missing_scope, adapter fails cleanly with status_code=400 and DOES NOT fall back to raw channel name."""
    adapter = SlackAdapter()
    cred = ConnectorCredentialModel(
        tenant_id="usr_1",
        provider="Slack",
        auth_type="OAuth2",
        access_token="xoxb-valid-test-token",
        scopes=["chat:write", "channels:read"]
    )
    req = ConnectorRequestModel(
        provider="Slack",
        operation_id="slack.chat.postMessage",
        tenant_id="usr_1",
        parameters={"channel": "#all-agentflow-ai", "text": "Scope failure test"}
    )

    post_message_called = False

    async def mock_connection_request(method, url, headers, json_data=None, params=None, timeout=30.0):
        nonlocal post_message_called
        if "auth.test" in url:
            return {"ok": True, "team": "Test Team"}
        if "conversations.list" in url:
            return {
                "ok": False,
                "error": "missing_scope",
                "needed": "groups:read"
            }
        if "chat.postMessage" in url:
            post_message_called = True
            return {"ok": True, "ts": "12345"}
        return {"ok": False, "error": "unknown_endpoint"}

    with patch("app.connectors.providers.slack.adapter.connection_pool.request", side_effect=mock_connection_request):
        res = await adapter.execute_operation(req, credentials=cred)
        assert res.success is False
        assert res.status_code == 400
        assert "Slack channel resolution failed: missing_scope" in res.error_message
        assert post_message_called is False

@pytest.mark.asyncio
async def test_slack_adapter_channel_resolution_direct_channel_id_bypasses_resolution():
    """Test direct channel ID (e.g. C081234567) bypasses conversations.list and dispatches postMessage directly."""
    adapter = SlackAdapter()
    cred = ConnectorCredentialModel(
        tenant_id="usr_1",
        provider="Slack",
        auth_type="OAuth2",
        access_token="xoxb-valid-test-token",
        scopes=["chat:write", "channels:read"]
    )
    req = ConnectorRequestModel(
        provider="Slack",
        operation_id="slack.chat.postMessage",
        tenant_id="usr_1",
        parameters={"channel": "C081234567", "text": "Direct ID test"}
    )

    conv_list_called = False

    async def mock_connection_request(method, url, headers, json_data=None, params=None, timeout=30.0):
        nonlocal conv_list_called
        if "conversations.list" in url:
            conv_list_called = True
            return {"ok": True, "channels": []}
        if "chat.postMessage" in url:
            return {
                "ok": True,
                "channel": json_data.get("channel"),
                "ts": "1726100000.000300"
            }
        return {"ok": False, "error": "unknown_endpoint"}

    with patch("app.connectors.providers.slack.adapter.connection_pool.request", side_effect=mock_connection_request):
        res = await adapter.execute_operation(req, credentials=cred)
        assert res.success is True
        assert res.data.get("channel") == "C081234567"
        assert conv_list_called is False


@pytest.mark.asyncio
async def test_slack_adapter_real_token_channel_resolution_no_name_error():
    """Regression test: Ensures real/non-test tokens reach _resolve_channel_id without NameError."""
    adapter = SlackAdapter()
    real_token_format = "xoxb-1234567890-9876543210-realprodtoken"
    cred = ConnectorCredentialModel(
        tenant_id="usr_1",
        provider="Slack",
        auth_type="OAuth2",
        access_token=real_token_format,
        scopes=["chat:write", "channels:read"]
    )
    req = ConnectorRequestModel(
        provider="Slack",
        operation_id="slack.chat.postMessage",
        tenant_id="usr_1",
        parameters={"channel": "#all-agentflow-ai", "text": "Real token test message"}
    )

    async def mock_connection_request(method, url, headers, json_data=None, params=None, timeout=30.0):
        if "auth.test" in url:
            return {"ok": True, "team": "Agentflow Team", "user": "bot_user"}
        if "conversations.list" in url:
            return {
                "ok": True,
                "channels": [
                    {"id": "C08REAL123", "name": "all-agentflow-ai", "is_member": True, "is_archived": False}
                ]
            }
        if "chat.postMessage" in url:
            return {
                "ok": True,
                "channel": json_data.get("channel"),
                "ts": "1726100000.000400"
            }
        return {"ok": False, "error": "unknown_endpoint"}

    with patch("app.connectors.providers.slack.adapter.connection_pool.request", side_effect=mock_connection_request):
        res = await adapter.execute_operation(req, credentials=cred)
        assert res.success is True
        assert res.data.get("channel") == "C08REAL123"

