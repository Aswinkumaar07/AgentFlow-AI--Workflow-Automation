import pytest
from unittest.mock import AsyncMock, patch
from app.connectors.models import ConnectorRequestModel, ConnectorCredentialModel
from app.connectors.providers.generic_rest.adapter import GenericRESTAdapter


@pytest.mark.asyncio
async def test_01_unauthenticated_operation_proceeds_without_auth():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="test_op",
        parameters={
            "url": "https://api.example.com/data",
            "http_method": "GET",
            "security_schemes": {},
            "security_requirements": [],
            "allow_http_for_tests": True,
        }
    )
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"success": True}
        resp = await adapter.execute_operation(request)
        assert resp.success is True
        assert resp.status_code == 200
        mock_req.assert_called_once_with("GET", "https://api.example.com/data", headers=None, json_data=None, params=None, timeout=30.0)


@pytest.mark.asyncio
async def test_02_apikey_header_injection():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="test_op",
        parameters={
            "url": "https://api.example.com/data",
            "http_method": "GET",
            "security_schemes": {
                "ApiKeyHeader": {"type": "apiKey", "name": "X-API-Key", "in": "header"}
            },
            "security_requirements": [{"ApiKeyHeader": []}],
            "allow_http_for_tests": True,
        }
    )
    credentials = ConnectorCredentialModel(provider="Generic REST API", api_key="secret_key_123")
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"data": "ok"}
        resp = await adapter.execute_operation(request, credentials=credentials)
        assert resp.success is True
        mock_req.assert_called_once_with("GET", "https://api.example.com/data", headers={"X-API-Key": "secret_key_123"}, json_data=None, params=None, timeout=30.0)


@pytest.mark.asyncio
async def test_03_apikey_query_injection():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="test_op",
        parameters={
            "url": "https://api.example.com/data",
            "http_method": "GET",
            "security_schemes": {
                "ApiKeyQuery": {"type": "apiKey", "name": "api_key", "in": "query"}
            },
            "security_requirements": [{"ApiKeyQuery": []}],
            "allow_http_for_tests": True,
        }
    )
    credentials = ConnectorCredentialModel(provider="Generic REST API", api_key="query_secret_456")
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"data": "ok"}
        resp = await adapter.execute_operation(request, credentials=credentials)
        assert resp.success is True
        mock_req.assert_called_once_with("GET", "https://api.example.com/data", headers=None, json_data=None, params={"api_key": "query_secret_456"}, timeout=30.0)


@pytest.mark.asyncio
async def test_04_bearer_header_injection():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="test_op",
        parameters={
            "url": "https://api.example.com/user",
            "http_method": "GET",
            "security_schemes": {
                "BearerAuth": {"type": "http", "scheme": "bearer"}
            },
            "security_requirements": [{"BearerAuth": []}],
            "allow_http_for_tests": True,
        }
    )
    credentials = ConnectorCredentialModel(provider="Generic REST API", access_token="bearer_token_xyz")
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"user": "alice"}
        resp = await adapter.execute_operation(request, credentials=credentials)
        assert resp.success is True
        mock_req.assert_called_once_with("GET", "https://api.example.com/user", headers={"Authorization": "Bearer bearer_token_xyz"}, json_data=None, params=None, timeout=30.0)


@pytest.mark.asyncio
async def test_05_or_security_requirements_first_satisfied():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="test_op",
        parameters={
            "url": "https://api.example.com/resource",
            "http_method": "GET",
            "security_schemes": {
                "ApiKeyHeader": {"type": "apiKey", "name": "X-API-Key", "in": "header"},
                "BearerAuth": {"type": "http", "scheme": "bearer"}
            },
            "security_requirements": [{"ApiKeyHeader": []}, {"BearerAuth": []}],
            "allow_http_for_tests": True,
        }
    )
    credentials = ConnectorCredentialModel(provider="Generic REST API", api_key="hdr_key_999")
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True}
        resp = await adapter.execute_operation(request, credentials=credentials)
        assert resp.success is True
        mock_req.assert_called_once_with("GET", "https://api.example.com/resource", headers={"X-API-Key": "hdr_key_999"}, json_data=None, params=None, timeout=30.0)


@pytest.mark.asyncio
async def test_06_or_security_requirements_second_satisfied():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="test_op",
        parameters={
            "url": "https://api.example.com/resource",
            "http_method": "GET",
            "security_schemes": {
                "ApiKeyHeader": {"type": "apiKey", "name": "X-API-Key", "in": "header"},
                "BearerAuth": {"type": "http", "scheme": "bearer"}
            },
            "security_requirements": [{"ApiKeyHeader": []}, {"BearerAuth": []}],
            "allow_http_for_tests": True,
        }
    )
    credentials = ConnectorCredentialModel(provider="Generic REST API", access_token="tok_second_choice")
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True}
        resp = await adapter.execute_operation(request, credentials=credentials)
        assert resp.success is True
        mock_req.assert_called_once_with("GET", "https://api.example.com/resource", headers={"Authorization": "Bearer tok_second_choice"}, json_data=None, params=None, timeout=30.0)


@pytest.mark.asyncio
async def test_07_and_security_requirements_satisfied():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="test_op",
        parameters={
            "url": "https://api.example.com/resource",
            "http_method": "GET",
            "security_schemes": {
                "ApiKeyHeader": {"type": "apiKey", "name": "X-API-Key", "in": "header"},
                "BearerAuth": {"type": "http", "scheme": "bearer"}
            },
            "security_requirements": [{"ApiKeyHeader": [], "BearerAuth": []}],
            "allow_http_for_tests": True,
        }
    )
    credentials = ConnectorCredentialModel(provider="Generic REST API", api_key="key_combo", access_token="tok_combo")
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True}
        resp = await adapter.execute_operation(request, credentials=credentials)
        assert resp.success is True
        mock_req.assert_called_once_with("GET", "https://api.example.com/resource", headers={"X-API-Key": "key_combo", "Authorization": "Bearer tok_combo"}, json_data=None, params=None, timeout=30.0)


@pytest.mark.asyncio
async def test_08_and_security_requirements_partially_missing_fails():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="test_op",
        parameters={
            "url": "https://api.example.com/resource",
            "http_method": "GET",
            "security_schemes": {
                "ApiKeyHeader": {"type": "apiKey", "name": "X-API-Key", "in": "header"},
                "BearerAuth": {"type": "http", "scheme": "bearer"}
            },
            "security_requirements": [{"ApiKeyHeader": [], "BearerAuth": []}],
            "allow_http_for_tests": True,
        }
    )
    credentials = ConnectorCredentialModel(provider="Generic REST API", api_key="key_combo_only")
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        resp = await adapter.execute_operation(request, credentials=credentials)
        assert resp.success is False
        assert resp.status_code == 401
        assert "Authentication Failed" in resp.data["error"]
        mock_req.assert_not_called()


@pytest.mark.asyncio
async def test_09_missing_credentials_returns_401_pre_network():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="test_op",
        parameters={
            "url": "https://api.example.com/secure",
            "http_method": "GET",
            "security_schemes": {
                "ApiKeyHeader": {"type": "apiKey", "name": "X-API-Key", "in": "header"}
            },
            "security_requirements": [{"ApiKeyHeader": []}],
            "allow_http_for_tests": True,
        }
    )
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        resp = await adapter.execute_operation(request, credentials=None)
        assert resp.success is False
        assert resp.status_code == 401
        assert resp.data["error"] == "Authentication Failed: Missing required credentials for operation security requirements."
        mock_req.assert_not_called()


@pytest.mark.asyncio
async def test_10_missing_api_key_returns_401_pre_network():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="test_op",
        parameters={
            "url": "https://api.example.com/secure",
            "http_method": "GET",
            "security_schemes": {
                "ApiKeyQuery": {"type": "apiKey", "name": "api_key", "in": "query"}
            },
            "security_requirements": [{"ApiKeyQuery": []}],
            "allow_http_for_tests": True,
        }
    )
    credentials = ConnectorCredentialModel(provider="Generic REST API", access_token="wrong_credential_type")
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        resp = await adapter.execute_operation(request, credentials=credentials)
        assert resp.success is False
        assert resp.status_code == 401
        mock_req.assert_not_called()


@pytest.mark.asyncio
async def test_11_missing_bearer_token_returns_401_pre_network():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="test_op",
        parameters={
            "url": "https://api.example.com/secure",
            "http_method": "GET",
            "security_schemes": {
                "BearerAuth": {"type": "http", "scheme": "bearer"}
            },
            "security_requirements": [{"BearerAuth": []}],
            "allow_http_for_tests": True,
        }
    )
    credentials = ConnectorCredentialModel(provider="Generic REST API", api_key="wrong_credential_type")
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        resp = await adapter.execute_operation(request, credentials=credentials)
        assert resp.success is False
        assert resp.status_code == 401
        mock_req.assert_not_called()


@pytest.mark.asyncio
async def test_12_unsupported_auth_scheme_returns_401():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="test_op",
        parameters={
            "url": "https://api.example.com/secure",
            "http_method": "GET",
            "security_schemes": {
                "BasicAuth": {"type": "http", "scheme": "basic"}
            },
            "security_requirements": [{"BasicAuth": []}],
            "allow_http_for_tests": True,
        }
    )
    credentials = ConnectorCredentialModel(provider="Generic REST API", api_key="some_key", access_token="some_tok")
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        resp = await adapter.execute_operation(request, credentials=credentials)
        assert resp.success is False
        assert resp.status_code == 401
        mock_req.assert_not_called()


@pytest.mark.asyncio
async def test_13_header_conflict_with_explicit_headers_returns_409():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="test_op",
        parameters={
            "url": "https://api.example.com/data",
            "http_method": "GET",
            "headers": {"X-API-Key": "explicit_key_value"},
            "security_schemes": {
                "ApiKeyHeader": {"type": "apiKey", "name": "X-API-Key", "in": "header"}
            },
            "security_requirements": [{"ApiKeyHeader": []}],
            "allow_http_for_tests": True,
        }
    )
    credentials = ConnectorCredentialModel(provider="Generic REST API", api_key="runtime_cred_value")
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        resp = await adapter.execute_operation(request, credentials=credentials)
        assert resp.success is False
        assert resp.status_code == 409
        assert "Authentication Conflict" in resp.data["error"]
        mock_req.assert_not_called()


@pytest.mark.asyncio
async def test_14_header_conflict_case_insensitive_returns_409():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="test_op",
        parameters={
            "url": "https://api.example.com/data",
            "http_method": "GET",
            "headers": {"x-api-key": "lowercase_explicit_val"},
            "security_schemes": {
                "ApiKeyHeader": {"type": "apiKey", "name": "X-API-Key", "in": "header"}
            },
            "security_requirements": [{"ApiKeyHeader": []}],
            "allow_http_for_tests": True,
        }
    )
    credentials = ConnectorCredentialModel(provider="Generic REST API", api_key="runtime_cred_value")
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        resp = await adapter.execute_operation(request, credentials=credentials)
        assert resp.success is False
        assert resp.status_code == 409
        mock_req.assert_not_called()


@pytest.mark.asyncio
async def test_15_header_conflict_with_request_parameters_returns_409():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="test_op",
        parameters={
            "url": "https://api.example.com/data",
            "http_method": "GET",
            "X-API-Key": "param_explicit_val",
            "security_schemes": {
                "ApiKeyHeader": {"type": "apiKey", "name": "X-API-Key", "in": "header"}
            },
            "security_requirements": [{"ApiKeyHeader": []}],
            "allow_http_for_tests": True,
        }
    )
    credentials = ConnectorCredentialModel(provider="Generic REST API", api_key="runtime_cred_value")
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        resp = await adapter.execute_operation(request, credentials=credentials)
        assert resp.success is False
        assert resp.status_code == 409
        mock_req.assert_not_called()


@pytest.mark.asyncio
async def test_16_query_conflict_returns_409():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="test_op",
        parameters={
            "url": "https://api.example.com/data",
            "http_method": "GET",
            "api_key": "conflicting_query_val",
            "security_schemes": {
                "ApiKeyQuery": {"type": "apiKey", "name": "api_key", "in": "query"}
            },
            "security_requirements": [{"ApiKeyQuery": []}],
            "allow_http_for_tests": True,
        }
    )
    credentials = ConnectorCredentialModel(provider="Generic REST API", api_key="runtime_cred_value")
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        resp = await adapter.execute_operation(request, credentials=credentials)
        assert resp.success is False
        assert resp.status_code == 409
        assert "api_key" in resp.data["error"]
        mock_req.assert_not_called()


@pytest.mark.asyncio
async def test_17_matching_explicit_header_does_not_conflict():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="test_op",
        parameters={
            "url": "https://api.example.com/data",
            "http_method": "GET",
            "headers": {"X-API-Key": "same_cred_val"},
            "security_schemes": {
                "ApiKeyHeader": {"type": "apiKey", "name": "X-API-Key", "in": "header"}
            },
            "security_requirements": [{"ApiKeyHeader": []}],
            "allow_http_for_tests": True,
        }
    )
    credentials = ConnectorCredentialModel(provider="Generic REST API", api_key="same_cred_val")
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True}
        resp = await adapter.execute_operation(request, credentials=credentials)
        assert resp.success is True
        mock_req.assert_called_once()


@pytest.mark.asyncio
async def test_18_matching_explicit_query_param_does_not_conflict():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="test_op",
        parameters={
            "url": "https://api.example.com/data",
            "http_method": "GET",
            "api_key": "same_cred_val",
            "security_schemes": {
                "ApiKeyQuery": {"type": "apiKey", "name": "api_key", "in": "query"}
            },
            "security_requirements": [{"ApiKeyQuery": []}],
            "allow_http_for_tests": True,
        }
    )
    credentials = ConnectorCredentialModel(provider="Generic REST API", api_key="same_cred_val")
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True}
        resp = await adapter.execute_operation(request, credentials=credentials)
        assert resp.success is True
        mock_req.assert_called_once()


@pytest.mark.asyncio
async def test_19_ssrf_check_runs_before_authentication():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="test_op",
        parameters={
            "url": "http://127.0.0.1/private",
            "is_dynamic_api": True,
            "security_schemes": {
                "ApiKeyHeader": {"type": "apiKey", "name": "X-API-Key", "in": "header"}
            },
            "security_requirements": [{"ApiKeyHeader": []}],
        }
    )
    # Even with missing credentials, SSRF check should fire first and return 400
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        resp = await adapter.execute_operation(request, credentials=None)
        assert resp.success is False
        assert resp.status_code == 400
        assert "SSRF Blocked" in resp.data["error"]
        mock_req.assert_not_called()


@pytest.mark.asyncio
async def test_20_query_apikey_does_not_leak_into_json_body():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="post_op",
        parameters={
            "url": "https://api.example.com/items",
            "http_method": "POST",
            "item_name": "Widget",
            "security_schemes": {
                "ApiKeyQuery": {"type": "apiKey", "name": "api_key", "in": "query"}
            },
            "security_requirements": [{"ApiKeyQuery": []}],
            "allow_http_for_tests": True,
        }
    )
    credentials = ConnectorCredentialModel(provider="Generic REST API", api_key="secret_query_val")
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"created": True}
        resp = await adapter.execute_operation(request, credentials=credentials)
        assert resp.success is True
        mock_req.assert_called_once_with(
            "POST",
            "https://api.example.com/items",
            headers=None,
            json_data={"item_name": "Widget"},
            params={"api_key": "secret_query_val"},
            timeout=30.0
        )


@pytest.mark.asyncio
async def test_21_internal_control_keys_exclude_security_metadata():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="post_op",
        parameters={
            "url": "https://api.example.com/items",
            "http_method": "POST",
            "data_field": "hello",
            "security_schemes": {"Dummy": {"type": "http", "scheme": "bearer"}},
            "security_requirements": [{"Dummy": []}],
            "allow_http_for_tests": True,
        }
    )
    credentials = ConnectorCredentialModel(provider="Generic REST API", access_token="tok_123")
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True}
        resp = await adapter.execute_operation(request, credentials=credentials)
        assert resp.success is True
        # Verify security_schemes and security_requirements were not passed in json_data body
        mock_req.assert_called_once_with(
            "POST",
            "https://api.example.com/items",
            headers={"Authorization": "Bearer tok_123"},
            json_data={"data_field": "hello"},
            params=None,
            timeout=30.0
        )


@pytest.mark.asyncio
async def test_22_empty_dict_requirement_allows_unauthenticated():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="test_op",
        parameters={
            "url": "https://api.example.com/public",
            "http_method": "GET",
            "security_schemes": {
                "ApiKeyHeader": {"type": "apiKey", "name": "X-API-Key", "in": "header"}
            },
            "security_requirements": [{}],
            "allow_http_for_tests": True,
        }
    )
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"public": True}
        resp = await adapter.execute_operation(request, credentials=None)
        assert resp.success is True
        mock_req.assert_called_once_with("GET", "https://api.example.com/public", headers=None, json_data=None, params=None, timeout=30.0)


@pytest.mark.asyncio
async def test_23_zero_secret_leakage_in_error_messages():
    adapter = GenericRESTAdapter()
    secret_value = "super_secret_token_value_9999"
    request = ConnectorRequestModel(
        operation_id="test_op",
        parameters={
            "url": "https://api.example.com/data",
            "http_method": "GET",
            "headers": {"X-API-Key": "explicit_wrong"},
            "security_schemes": {
                "ApiKeyHeader": {"type": "apiKey", "name": "X-API-Key", "in": "header"}
            },
            "security_requirements": [{"ApiKeyHeader": []}],
            "allow_http_for_tests": True,
        }
    )
    credentials = ConnectorCredentialModel(provider="Generic REST API", api_key=secret_value)
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        resp = await adapter.execute_operation(request, credentials=credentials)
        assert resp.success is False
        assert secret_value not in str(resp.data)
        assert secret_value not in resp.data.get("error", "")


@pytest.mark.asyncio
async def test_24_swagger2_apikey_header_runtime_injection():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="swag_op",
        parameters={
            "url": "https://api.swagger.io/v2/items",
            "http_method": "GET",
            "security_schemes": {
                "HeaderKey": {"type": "apiKey", "name": "X-Swagger-Key", "in": "header"}
            },
            "security_requirements": [{"HeaderKey": []}],
            "allow_http_for_tests": True,
        }
    )
    credentials = ConnectorCredentialModel(provider="Generic REST API", api_key="swagger_key_val")
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"swag": "ok"}
        resp = await adapter.execute_operation(request, credentials=credentials)
        assert resp.success is True
        mock_req.assert_called_once_with(
            "GET",
            "https://api.swagger.io/v2/items",
            headers={"X-Swagger-Key": "swagger_key_val"},
            json_data=None,
            params=None,
            timeout=30.0
        )


@pytest.mark.asyncio
async def test_25_swagger2_apikey_query_runtime_injection():
    adapter = GenericRESTAdapter()
    request = ConnectorRequestModel(
        operation_id="swag_op2",
        parameters={
            "url": "https://api.swagger.io/v2/items",
            "http_method": "GET",
            "security_schemes": {
                "QueryKey": {"type": "apiKey", "name": "key", "in": "query"}
            },
            "security_requirements": [{"QueryKey": []}],
            "allow_http_for_tests": True,
        }
    )
    credentials = ConnectorCredentialModel(provider="Generic REST API", api_key="swagger_query_key_val")
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"swag": "ok"}
        resp = await adapter.execute_operation(request, credentials=credentials)
        assert resp.success is True
        mock_req.assert_called_once_with(
            "GET",
            "https://api.swagger.io/v2/items",
            headers=None,
            json_data=None,
            params={"key": "swagger_query_key_val"},
            timeout=30.0
        )
