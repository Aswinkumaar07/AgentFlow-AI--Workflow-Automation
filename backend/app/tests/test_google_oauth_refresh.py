import time
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from app.oauth.manager import oauth_manager
from app.connectors.security.secret_manager import secret_manager
from app.connectors.models import ConnectorCredentialModel, ConnectorRequestModel
from app.connectors.providers.gmail.adapter import GmailAdapter
from app.core.config import settings


@pytest.mark.asyncio
async def test_refresh_access_token_calls_google_token_endpoint():
    """Requirement 4A & 4B & 4C: refresh_access_token() calls Google token endpoint, updates access_token & expires_at, preserves refresh_token."""
    user_id = "test_user_refresh_1"
    provider = "Google"

    # Setup initial credential with expired access token and valid refresh token
    initial_cred = ConnectorCredentialModel(
        tenant_id=user_id,
        provider=provider,
        auth_type="OAuth2",
        access_token="old_access_token_123",
        refresh_token="valid_refresh_token_xyz",
        token_expires_at=time.time() - 3600.0,
        scopes=["gmail.readonly"],
    )
    await secret_manager.set_secret(user_id, provider, initial_cred)

    # Mock settings
    settings.GOOGLE_CLIENT_ID = "mock_client_id"
    settings.GOOGLE_CLIENT_SECRET = "mock_client_secret"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "access_token": "new_refreshed_access_token_999",
        "expires_in": 3600,
        "token_type": "Bearer",
    }

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        refreshed_conn = await oauth_manager.refresh_access_token(user_id, provider)

        # A. Assert POST to Google token endpoint was made with correct payload
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[0][0] == "https://oauth2.googleapis.com/token"
        payload = call_kwargs[1].get("data", {})
        assert payload["grant_type"] == "refresh_token"
        assert payload["client_id"] == "mock_client_id"
        assert payload["client_secret"] == "mock_client_secret"
        assert payload["refresh_token"] == "valid_refresh_token_xyz"

        # B. Assert valid refresh response updates access_token and expires_at
        assert refreshed_conn is not None
        assert refreshed_conn.access_token == "new_refreshed_access_token_999"
        assert refreshed_conn.expires_at > time.time() + 3000.0

        # C. Assert refresh_token is preserved
        updated_secret = await secret_manager.get_secret(user_id, provider)
        assert updated_secret is not None
        assert updated_secret.access_token == "new_refreshed_access_token_999"
        assert updated_secret.refresh_token == "valid_refresh_token_xyz"


@pytest.mark.asyncio
async def test_expired_access_token_triggers_refresh_before_gmail_execution():
    """Requirement 4D: Expired access token triggers refresh before Gmail execution."""
    user_id = "test_user_refresh_exp"
    provider = "Google"

    # Setup credential near expiry (exp_at in 30s <= 60s window)
    initial_cred = ConnectorCredentialModel(
        tenant_id=user_id,
        provider=provider,
        auth_type="OAuth2",
        access_token="expiring_token_001",
        refresh_token="ref_tok_exp_001",
        token_expires_at=time.time() + 30.0,
        scopes=["gmail.readonly"],
    )
    await secret_manager.set_secret(user_id, provider, initial_cred)

    adapter = GmailAdapter()
    req = ConnectorRequestModel(
        tenant_id=user_id,
        connector_id="gmail",
        operation_id="gmail.messages.list",
        parameters={"max_results": 5},
    )

    with patch.object(oauth_manager, "refresh_access_token", new_callable=AsyncMock) as mock_refresh:
        mock_refresh.return_value = MagicMock(access_token="fresh_token_after_precheck")

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            mock_profile_res = MagicMock()
            mock_profile_res.status_code = 200
            mock_profile_res.json.return_value = {"emailAddress": "user@example.com"}
            mock_profile_res.is_success = True

            mock_op_res = MagicMock()
            mock_op_res.status_code = 200
            mock_op_res.json.return_value = {"messages": []}
            mock_op_res.is_success = True
            mock_op_res.headers = {}

            mock_req.side_effect = [mock_profile_res, mock_op_res]

            res = await adapter.execute(req)

            # Proactive refresh should have been triggered before execution
            mock_refresh.assert_called_once_with(user_id, "Google")
            assert res.success is True


@pytest.mark.asyncio
async def test_http_401_triggers_at_most_one_refresh_and_retry():
    """Requirement 4E: HTTP 401 triggers at most one refresh-and-retry."""
    user_id = "test_user_401_retry"
    provider = "Google"

    cred = ConnectorCredentialModel(
        tenant_id=user_id,
        provider=provider,
        auth_type="OAuth2",
        access_token="stale_token_401",
        refresh_token="valid_ref_token_401",
        token_expires_at=time.time() + 3600.0,
    )
    await secret_manager.set_secret(user_id, provider, cred)

    adapter = GmailAdapter()
    req = ConnectorRequestModel(
        tenant_id=user_id,
        connector_id="gmail",
        operation_id="gmail.messages.list",
        parameters={},
    )

    with patch.object(oauth_manager, "refresh_access_token", new_callable=AsyncMock) as mock_refresh:
        mock_refresh.return_value = MagicMock(access_token="token_after_401")

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            # First attempt returns 401, second attempt after refresh returns 200
            res_401 = MagicMock()
            res_401.status_code = 401
            res_401.text = "Unauthorized"

            res_200 = MagicMock()
            res_200.status_code = 200
            res_200.json.return_value = {"emailAddress": "user@example.com"}
            res_200.is_success = True

            res_list_200 = MagicMock()
            res_list_200.status_code = 200
            res_list_200.json.return_value = {"messages": []}
            res_list_200.is_success = True
            res_list_200.headers = {}

            mock_req.side_effect = [res_401, res_200, res_list_200]

            res = await adapter.execute(req)

            assert mock_refresh.call_count == 1
            assert res.success is True


@pytest.mark.asyncio
async def test_failed_refresh_returns_real_authentication_failure():
    """Requirement 4F & 4G: Failed refresh returns real auth failure and redacts secrets from error message."""
    user_id = "test_user_failed_ref"
    provider = "Google"

    cred = ConnectorCredentialModel(
        tenant_id=user_id,
        provider=provider,
        auth_type="OAuth2",
        access_token="secret_token_12345",
        refresh_token="secret_refresh_67890",
        token_expires_at=time.time() - 100.0,
    )
    await secret_manager.set_secret(user_id, provider, cred)

    adapter = GmailAdapter()
    req = ConnectorRequestModel(
        tenant_id=user_id,
        connector_id="gmail",
        operation_id="gmail.messages.list",
        parameters={},
    )

    with patch.object(oauth_manager, "refresh_access_token", new_callable=AsyncMock) as mock_refresh:
        mock_refresh.return_value = None  # Refresh failed

        with patch.object(httpx.AsyncClient, "request", new_callable=AsyncMock) as mock_req:
            res_401 = MagicMock()
            res_401.status_code = 401
            res_401.text = "Google OAuth token verification failed: Invalid Credentials"
            mock_req.return_value = res_401

            res = await adapter.execute(req)

            assert res.success is False
            assert res.status_code == 401
            # 4G: Redaction confirmation
            assert "secret_token_12345" not in res.error_message
            assert "secret_refresh_67890" not in res.error_message
            assert "Bearer" not in res.error_message
