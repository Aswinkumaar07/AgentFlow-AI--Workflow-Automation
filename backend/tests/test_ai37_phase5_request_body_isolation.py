import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.connectors.providers.generic_rest.adapter import GenericRESTAdapter
from app.connectors.models import ConnectorRequestModel
from app.connectors.cache.connection_pool import connection_pool

@pytest.fixture
def adapter():
    return GenericRESTAdapter()

def test_dynamic_post_parameters_filtered(adapter):
    req = ConnectorRequestModel(
        operation_id="createPet",
        parameters={
            "url": "https://example.com/api/v3/pet",
            "http_method": "POST",
            "method": "POST",
            "is_dynamic_api": True,
            "instruction": "Add a new pet",
            "auth_provider": "Generic_rest",
            "credential_id": "c1",
            "auth_account_label": "lbl",
            "auth_status": "unbound",
            "validate_url": True,
            "allow_http_for_tests": True,
            "username": "johndoe",
            "age": 25
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"status": "created"}
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is True
        mock_req.assert_called_once()
        args, kwargs = mock_req.call_args
        assert args[0] == "POST"
        assert args[1] == "https://example.com/api/v3/pet"
        assert kwargs["params"] is None
        assert kwargs["json_data"] == {"username": "johndoe", "age": 25}

def test_path_parameter_excluded_from_post_body(adapter):
    req = ConnectorRequestModel(
        operation_id="updateUser",
        parameters={
            "url": "https://example.com/user/{userId}",
            "http_method": "POST",
            "userId": 123,
            "name": "Alice",
            "allow_http_for_tests": True
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"status": "ok"}
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is True
        args, kwargs = mock_req.call_args
        assert args[1] == "https://example.com/user/123"
        assert kwargs["params"] is None
        # 'userId' was substituted into the URL path and MUST NOT appear in json_data
        assert kwargs["json_data"] == {"name": "Alice"}

def test_explicit_request_body_preserved(adapter):
    req = ConnectorRequestModel(
        operation_id="createUserExplicit",
        parameters={
            "url": "https://example.com/user/{userId}",
            "http_method": "POST",
            "userId": 123,
            "allow_http_for_tests": True
        },
        body={"name": "Alice", "userId": 123, "role": "admin"}
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"status": "ok"}
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is True
        args, kwargs = mock_req.call_args
        # Explicit request.body must be preserved exactly as provided
        assert kwargs["json_data"] == {"name": "Alice", "userId": 123, "role": "admin"}

def test_post_with_only_internal_or_path_params(adapter):
    req = ConnectorRequestModel(
        operation_id="triggerAction",
        parameters={
            "url": "https://example.com/item/{itemId}/trigger",
            "http_method": "POST",
            "itemId": 456,
            "is_dynamic_api": True,
            "instruction": "Trigger action",
            "allow_http_for_tests": True
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"status": "triggered"}
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is True
        args, kwargs = mock_req.call_args
        assert args[1] == "https://example.com/item/456/trigger"
        # No extra business body fields remain, json_data must evaluate to None
        assert kwargs["json_data"] is None

def test_put_and_patch_request_body_isolation(adapter):
    for method in ["PUT", "PATCH"]:
        req = ConnectorRequestModel(
            operation_id=f"updateItem_{method}",
            parameters={
                "url": "https://example.com/item/{itemId}",
                "http_method": method,
                "itemId": 789,
                "is_dynamic_api": True,
                "title": "Updated Title",
                "allow_http_for_tests": True
            }
        )
        with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"status": "updated"}
            res = asyncio.run(adapter.execute_operation(req))
            assert res.success is True
            args, kwargs = mock_req.call_args
            assert args[0] == method
            assert args[1] == "https://example.com/item/789"
            assert kwargs["params"] is None
            assert kwargs["json_data"] == {"title": "Updated Title"}

def test_existing_get_delete_query_isolation_unchanged(adapter):
    req_get = ConnectorRequestModel(
        operation_id="getItem",
        parameters={
            "url": "https://example.com/items/{itemId}",
            "http_method": "GET",
            "itemId": 101,
            "category": "electronics",
            "is_dynamic_api": True,
            "allow_http_for_tests": True
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"status": "ok"}
        res = asyncio.run(adapter.execute_operation(req_get))
        assert res.success is True
        args, kwargs = mock_req.call_args
        assert args[0] == "GET"
        assert args[1] == "https://example.com/items/101"
        assert kwargs["params"] == {"category": "electronics"}
        assert kwargs["json_data"] is None

def test_ssrf_validation_active_for_post_requests(adapter):
    req = ConnectorRequestModel(
        operation_id="postSSRF",
        parameters={
            "url": "http://169.254.169.254/latest/meta-data",
            "http_method": "POST",
            "is_dynamic_api": True,
            "payload": "data"
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is False
        assert res.status_code == 400
        assert "SSRF Blocked" in res.data["error"]
        mock_req.assert_not_called()
