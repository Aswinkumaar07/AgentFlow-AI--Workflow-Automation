import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from app.connectors.providers.generic_rest.adapter import GenericRESTAdapter
from app.connectors.models import ConnectorRequestModel
from app.connectors.cache.connection_pool import connection_pool
from app.agents.api_discovery.parser.spec_parser import EnterpriseSpecParser
from app.agents.api_discovery.dynamic_discovery import DynamicAPIDiscoveryEngine


@pytest.fixture
def adapter():
    return GenericRESTAdapter()


# TEST 1: POST + required query parameter + JSON body
def test_post_with_required_query_param_and_body(adapter):
    req = ConnectorRequestModel(
        operation_id="createUser",
        parameters={
            "url": "https://example.com/users",
            "http_method": "POST",
            "is_dynamic_api": True,
            "query_params": ["notify"],
            "notify": True,
            "name": "Alice",
            "email": "alice@example.com",
            "allow_http_for_tests": True,
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"status": "created"}
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is True
        mock_req.assert_called_once()
        args, kwargs = mock_req.call_args
        assert args[0] == "POST"
        assert args[1] == "https://example.com/users"
        assert kwargs["params"] == {"notify": True}
        assert kwargs["json_data"] == {"name": "Alice", "email": "alice@example.com"}


# TEST 2: POST + optional query parameter + JSON body
def test_post_with_optional_query_param_and_body(adapter):
    req = ConnectorRequestModel(
        operation_id="createUserOptional",
        parameters={
            "url": "https://example.com/users",
            "http_method": "POST",
            "is_dynamic_api": True,
            "query_params": ["source"],
            "source": "web",
            "name": "Bob",
            "allow_http_for_tests": True,
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"status": "created"}
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is True
        _, kwargs = mock_req.call_args
        assert kwargs["params"] == {"source": "web"}
        assert kwargs["json_data"] == {"name": "Bob"}


# TEST 3: PUT + query parameter + JSON body
def test_put_with_query_param_and_body(adapter):
    req = ConnectorRequestModel(
        operation_id="updateUser",
        parameters={
            "url": "https://example.com/users",
            "http_method": "PUT",
            "is_dynamic_api": True,
            "query_params": ["sync"],
            "sync": True,
            "status": "active",
            "allow_http_for_tests": True,
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"status": "updated"}
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is True
        args, kwargs = mock_req.call_args
        assert args[0] == "PUT"
        assert kwargs["params"] == {"sync": True}
        assert kwargs["json_data"] == {"status": "active"}


# TEST 4: PATCH + query parameter + JSON body
def test_patch_with_query_param_and_body(adapter):
    req = ConnectorRequestModel(
        operation_id="patchUser",
        parameters={
            "url": "https://example.com/users",
            "http_method": "PATCH",
            "is_dynamic_api": True,
            "query_params": ["dry_run"],
            "dry_run": False,
            "role": "admin",
            "allow_http_for_tests": True,
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"status": "patched"}
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is True
        args, kwargs = mock_req.call_args
        assert args[0] == "PATCH"
        assert kwargs["params"] == {"dry_run": False}
        assert kwargs["json_data"] == {"role": "admin"}


# TEST 5: POST without query parameters
def test_post_without_query_params(adapter):
    req = ConnectorRequestModel(
        operation_id="createItemSimple",
        parameters={
            "url": "https://example.com/items",
            "http_method": "POST",
            "is_dynamic_api": True,
            "title": "New Item",
            "allow_http_for_tests": True,
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"status": "ok"}
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is True
        _, kwargs = mock_req.call_args
        assert kwargs["params"] is None
        assert kwargs["json_data"] == {"title": "New Item"}


# TEST 6: POST with path parameter + query parameter + JSON body
def test_post_with_path_param_query_param_and_body(adapter):
    req = ConnectorRequestModel(
        operation_id="updateUserById",
        parameters={
            "url": "https://example.com/users/{userId}",
            "http_method": "POST",
            "is_dynamic_api": True,
            "userId": "usr_999",
            "query_params": ["notify"],
            "notify": True,
            "name": "Charlie",
            "allow_http_for_tests": True,
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"status": "ok"}
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is True
        args, kwargs = mock_req.call_args
        assert args[1] == "https://example.com/users/usr_999"
        assert kwargs["params"] == {"notify": True}
        assert kwargs["json_data"] == {"name": "Charlie"}
        # userId must NOT appear in params or json_data
        assert "userId" not in (kwargs.get("params") or {})
        assert "userId" not in (kwargs.get("json_data") or {})


# TEST 7: Internal control keys do not appear in params or json_data
def test_internal_control_keys_never_leak(adapter):
    req = ConnectorRequestModel(
        operation_id="testControlKeys",
        parameters={
            "url": "https://example.com/action",
            "http_method": "POST",
            "method": "POST",
            "is_dynamic_api": True,
            "instruction": "Do something",
            "auth_provider": "Generic_rest",
            "credential_id": "c1",
            "auth_account_label": "lbl",
            "auth_status": "unbound",
            "validate_url": True,
            "allow_http_for_tests": True,
            "query_params": ["verbose"],
            "verbose": True,
            "payload_data": "sample",
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {}
        asyncio.run(adapter.execute_operation(req))
        _, kwargs = mock_req.call_args
        sent_params = kwargs.get("params") or {}
        sent_body = kwargs.get("json_data") or {}

        assert sent_params == {"verbose": True}
        assert sent_body == {"payload_data": "sample"}

        internal_keys = ["url", "http_method", "method", "is_dynamic_api", "instruction", "auth_provider", "credential_id", "auth_account_label", "auth_status", "validate_url", "allow_http_for_tests", "query_params"]
        for key in internal_keys:
            assert key not in sent_params
            assert key not in sent_body


# TEST 8: Explicit request.body remains unchanged
def test_explicit_request_body_preserved(adapter):
    req = ConnectorRequestModel(
        operation_id="explicitBodyOp",
        parameters={
            "url": "https://example.com/custom",
            "http_method": "POST",
            "query_params": ["flag"],
            "flag": "yes",
            "allow_http_for_tests": True,
        },
        body={"custom_field": 123}
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {}
        asyncio.run(adapter.execute_operation(req))
        _, kwargs = mock_req.call_args
        assert kwargs["params"] == {"flag": "yes"}
        assert kwargs["json_data"] == {"custom_field": 123}


# TEST 9: GET behavior remains unchanged
def test_get_behavior_unchanged(adapter):
    req = ConnectorRequestModel(
        operation_id="getUsers",
        parameters={
            "url": "https://example.com/users",
            "http_method": "GET",
            "limit": 20,
            "allow_http_for_tests": True,
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {}
        asyncio.run(adapter.execute_operation(req))
        args, kwargs = mock_req.call_args
        assert args[0] == "GET"
        assert kwargs["params"] == {"limit": 20}
        assert kwargs["json_data"] is None


# TEST 10: DELETE behavior remains unchanged
def test_delete_behavior_unchanged(adapter):
    req = ConnectorRequestModel(
        operation_id="deleteUser",
        parameters={
            "url": "https://example.com/users/{userId}",
            "http_method": "DELETE",
            "userId": 456,
            "force": True,
            "allow_http_for_tests": True,
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {}
        asyncio.run(adapter.execute_operation(req))
        args, kwargs = mock_req.call_args
        assert args[0] == "DELETE"
        assert args[1] == "https://example.com/users/456"
        assert kwargs["params"] == {"force": True}
        assert kwargs["json_data"] is None


# TEST 11: Multiple query parameters + multiple body fields
def test_multiple_query_params_and_body_fields(adapter):
    req = ConnectorRequestModel(
        operation_id="multiQueryAndBody",
        parameters={
            "url": "https://example.com/api/v1/posts",
            "http_method": "POST",
            "query_params": ["notify", "format"],
            "notify": True,
            "format": "json",
            "title": "Post Title",
            "content": "Post Body Content",
            "tags": ["tech", "ai"],
            "allow_http_for_tests": True,
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"id": 101}
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is True
        _, kwargs = mock_req.call_args
        assert kwargs["params"] == {"notify": True, "format": "json"}
        assert kwargs["json_data"] == {
            "title": "Post Title",
            "content": "Post Body Content",
            "tags": ["tech", "ai"],
        }


# TEST 12: Required query parameter is preserved through parser/discovery metadata
def test_parser_and_discovery_preserve_query_params():
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Query Test API", "version": "1.0.0"},
        "paths": {
            "/users": {
                "post": {
                    "operationId": "createUserWithQuery",
                    "parameters": [
                        {"name": "notify", "in": "query", "required": True, "schema": {"type": "boolean"}}
                    ],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["name"],
                                    "properties": {
                                        "name": {"type": "string"},
                                        "email": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(spec)
    assert len(endpoints) == 1
    ep = endpoints[0]
    assert ep.query_params == ["notify"]
    assert "notify" in ep.required_params
    assert "name" in ep.required_params

    engine = DynamicAPIDiscoveryEngine()
    result = engine.discover_and_register_api(spec)
    assert result.success is True
    op = result.connector_spec.operations[0]
    assert op.get("query_params") == ["notify"]
    assert op["parameters"].get("query_params") == ["notify"]


# TEST 13: RequestBody property is NOT classified as query parameter
def test_request_body_property_not_query_param():
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Body Test API", "version": "1.0.0"},
        "paths": {
            "/items": {
                "post": {
                    "operationId": "createItem",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "sku": {"type": "string"},
                                        "price": {"type": "number"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(spec)
    assert len(endpoints) == 1
    ep = endpoints[0]
    assert ep.query_params == []


# TEST 14: Path parameter is NOT classified as query parameter
def test_path_param_not_query_param():
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Path Test API", "version": "1.0.0"},
        "paths": {
            "/items/{itemId}": {
                "post": {
                    "operationId": "updateItem",
                    "parameters": [
                        {"name": "itemId", "in": "path", "required": True, "schema": {"type": "string"}},
                        {"name": "verbose", "in": "query", "required": False, "schema": {"type": "boolean"}}
                    ],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"name": {"type": "string"}}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(spec)
    assert len(endpoints) == 1
    ep = endpoints[0]
    assert ep.query_params == ["verbose"]
    assert "itemId" not in ep.query_params


# TEST 15: Native/non-dynamic Generic REST behavior remains unchanged
def test_native_generic_rest_unchanged(adapter):
    req = ConnectorRequestModel(
        operation_id="generic.http.request",
        parameters={
            "url": "https://api.github.com/zen",
            "http_method": "GET",
            "allow_http_for_tests": True,
        }
    )
    with patch.object(connection_pool, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = "Design for failure."
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is True
        mock_req.assert_called_once()
