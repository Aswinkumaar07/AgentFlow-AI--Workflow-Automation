import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.connectors.providers.generic_rest.adapter import GenericRESTAdapter
from app.connectors.models import ConnectorRequestModel
from app.connectors.cache.connection_pool import connection_pool

@pytest.fixture
def adapter():
    return GenericRESTAdapter()

def test_basic_path_parameter_substitution(adapter):
    req = ConnectorRequestModel(
        operation_id="getUser",
        parameters={
            "url": "https://example.com/users/{id}",
            "http_method": "GET",
            "id": 123,
            "allow_http_for_tests": True
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"status": "ok"}
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is True
        mock_req.assert_called_once()
        args, kwargs = mock_req.call_args
        assert args[0] == "GET"
        assert args[1] == "https://example.com/users/123"

def test_string_path_parameter_substitution(adapter):
    req = ConnectorRequestModel(
        operation_id="getUserByName",
        parameters={
            "url": "https://example.com/users/{username}",
            "http_method": "GET",
            "username": "johndoe",
            "allow_http_for_tests": True
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"status": "ok"}
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is True
        args, kwargs = mock_req.call_args
        assert args[1] == "https://example.com/users/johndoe"

def test_path_encoding_for_reserved_characters(adapter):
    req = ConnectorRequestModel(
        operation_id="getUserByNameSpecial",
        parameters={
            "url": "https://example.com/users/{username}",
            "http_method": "GET",
            "username": "john/doe",
            "allow_http_for_tests": True
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"status": "ok"}
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is True
        args, kwargs = mock_req.call_args
        # 'john/doe' encoded to 'john%2Fdoe' so it remains a single path segment
        assert args[1] == "https://example.com/users/john%2Fdoe"

def test_path_parameter_removed_from_query(adapter):
    req = ConnectorRequestModel(
        operation_id="getUserWithQuery",
        parameters={
            "url": "https://example.com/users/{id}",
            "http_method": "GET",
            "id": 123,
            "status": "active",
            "allow_http_for_tests": True
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"status": "ok"}
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is True
        args, kwargs = mock_req.call_args
        assert args[1] == "https://example.com/users/123"
        # 'id' must NOT be in query parameters, but 'status' MUST be present
        assert kwargs["params"] == {"status": "active"}

def test_multiple_path_parameters(adapter):
    req = ConnectorRequestModel(
        operation_id="getUserOrder",
        parameters={
            "url": "https://example.com/users/{userId}/orders/{orderId}",
            "http_method": "GET",
            "userId": 42,
            "orderId": 99,
            "allow_http_for_tests": True
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"status": "ok"}
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is True
        args, kwargs = mock_req.call_args
        assert args[1] == "https://example.com/users/42/orders/99"
        assert kwargs["params"] is None

def test_missing_required_path_parameter(adapter):
    req = ConnectorRequestModel(
        operation_id="getUserMissingParam",
        parameters={
            "url": "https://example.com/users/{id}",
            "http_method": "GET",
            # 'id' parameter is intentionally omitted
            "allow_http_for_tests": True
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is False
        assert res.status_code == 400
        assert "Missing required path parameter 'id'" in res.data["error"]
        # Must NOT dispatch network request
        mock_req.assert_not_called()

def test_static_url_regression(adapter):
    req = ConnectorRequestModel(
        operation_id="getItems",
        parameters={
            "url": "https://example.com/api/items",
            "http_method": "GET",
            "allow_http_for_tests": True
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"status": "ok"}
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is True
        args, kwargs = mock_req.call_args
        assert args[1] == "https://example.com/api/items"

def test_internal_control_filtering_regression(adapter):
    req = ConnectorRequestModel(
        operation_id="testControlFiltering",
        parameters={
            "url": "https://example.com/api/items",
            "http_method": "GET",
            "method": "GET",
            "is_dynamic_api": True,
            "instruction": "get items",
            "auth_provider": "none",
            "credential_id": "c1",
            "auth_account_label": "lbl",
            "auth_status": "valid",
            "validate_url": True,
            "allow_http_for_tests": True,
            "filter": "electronics"
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"status": "ok"}
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is True
        args, kwargs = mock_req.call_args
        assert kwargs["params"] == {"filter": "electronics"}

def test_ssrf_validation_remains_active(adapter):
    req = ConnectorRequestModel(
        operation_id="testSSRFPath",
        parameters={
            "url": "http://169.254.169.254/user/{id}",
            "http_method": "GET",
            "id": 123,
            "is_dynamic_api": True
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is False
        assert res.status_code == 400
        assert "SSRF Blocked" in res.data["error"]
        mock_req.assert_not_called()

def test_existing_dynamic_delete_scenario(adapter):
    req = ConnectorRequestModel(
        operation_id="deleteUser",
        parameters={
            "url": "https://petstore3.swagger.io/api/v3/user/{username}",
            "http_method": "DELETE",
            "method": "DELETE",
            "username": "johndoe",
            "is_dynamic_api": True
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"message": "User deleted"}
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is True
        args, kwargs = mock_req.call_args
        assert args[0] == "DELETE"
        assert args[1] == "https://petstore3.swagger.io/api/v3/user/johndoe"
        assert kwargs["params"] is None
