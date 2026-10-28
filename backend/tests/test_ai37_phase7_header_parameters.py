import pytest
from unittest.mock import patch, AsyncMock
from app.agents.api_discovery.parser.spec_parser import EnterpriseSpecParser
from app.agents.api_discovery.dynamic_discovery import DynamicAPIDiscoveryEngine
from app.agents.connector_ai.operation_ranker import OperationResult, OperationRanker
from app.connectors.providers.generic_rest.adapter import GenericRESTAdapter
from app.connectors.models import ConnectorRequestModel


SPEC_WITH_HEADERS = {
    "openapi": "3.0.0",
    "info": {"title": "Header Test API", "version": "1.0.0"},
    "paths": {
        "/users/{userId}": {
            "post": {
                "operationId": "create_user_with_headers",
                "summary": "Create user with header params",
                "parameters": [
                    {
                        "name": "userId",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    },
                    {
                        "name": "notify",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "boolean"}
                    },
                    {
                        "name": "X-Required-Header",
                        "in": "header",
                        "required": True,
                        "schema": {"type": "string"}
                    },
                    {
                        "name": "X-Optional-Header",
                        "in": "header",
                        "required": False,
                        "schema": {"type": "string"}
                    }
                ],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["name"],
                                "properties": {
                                    "name": {"type": "string"},
                                    "role": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}


def test_01_parser_identifies_required_header_parameter():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(SPEC_WITH_HEADERS)
    assert len(endpoints) == 1
    ep = endpoints[0]
    assert "X-Required-Header" in ep.header_params
    assert "X-Required-Header" in ep.required_params


def test_02_parser_identifies_optional_header_parameter():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(SPEC_WITH_HEADERS)
    ep = endpoints[0]
    assert "X-Optional-Header" in ep.header_params
    assert "X-Optional-Header" in ep.optional_params


def test_03_header_parameter_is_not_classified_as_query_parameter():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(SPEC_WITH_HEADERS)
    ep = endpoints[0]
    assert "X-Required-Header" not in ep.query_params
    assert "X-Optional-Header" not in ep.query_params
    assert ep.query_params == ["notify"]


def test_04_header_parameter_is_not_classified_as_body_property():
    parser = EnterpriseSpecParser()
    endpoints = parser.parse_spec(SPEC_WITH_HEADERS)
    ep = endpoints[0]
    body_props = ep.request_schema.get("properties", {}).keys()
    assert "X-Required-Header" not in body_props
    assert "X-Optional-Header" not in body_props


def test_05_dynamic_discovery_preserves_header_params():
    engine = DynamicAPIDiscoveryEngine()
    result = engine.discover_and_register_api(SPEC_WITH_HEADERS)
    assert result.success is True
    ops = result.connector_spec.operations
    assert len(ops) == 1
    op = ops[0]
    assert "header_params" in op
    assert op["header_params"] == ["X-Required-Header", "X-Optional-Header"]
    assert "header_params" in op["parameters"]
    assert op["parameters"]["header_params"] == ["X-Required-Header", "X-Optional-Header"]


def test_06_operation_result_preserves_header_params():
    op_res = OperationResult(
        provider="Header Test API",
        operation="create_user_with_headers",
        parameters={"url": "https://example.com", "header_params": ["X-Test-Header"]},
        header_params=["X-Test-Header"],
        query_params=["id"],
    )
    assert op_res.header_params == ["X-Test-Header"]


@pytest.mark.asyncio
async def test_07_post_header_parameter_routes_to_headers():
    adapter = GenericRESTAdapter()
    req = ConnectorRequestModel(
        provider="generic_rest",
        operation_id="test_post",
        parameters={
            "url": "https://example.com/api",
            "http_method": "POST",
            "is_dynamic_api": True,
            "header_params": ["X-Test-Header"],
            "X-Test-Header": "header_val",
            "body_field": "body_val"
        }
    )
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_pool:
        mock_pool.return_value = {"status": "ok"}
        res = await adapter.execute_operation(req)
        assert res.success is True
        mock_pool.assert_called_once()
        kwargs = mock_pool.call_args.kwargs
        assert kwargs["headers"] == {"X-Test-Header": "header_val"}
        assert kwargs["json_data"] == {"body_field": "body_val"}


@pytest.mark.asyncio
async def test_08_put_header_parameter_routes_to_headers():
    adapter = GenericRESTAdapter()
    req = ConnectorRequestModel(
        provider="generic_rest",
        operation_id="test_put",
        parameters={
            "url": "https://example.com/api",
            "http_method": "PUT",
            "is_dynamic_api": True,
            "header_params": ["X-Custom-Header"],
            "X-Custom-Header": "put_header_val",
            "item_name": "updated_item"
        }
    )
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_pool:
        mock_pool.return_value = {"status": "ok"}
        res = await adapter.execute_operation(req)
        assert res.success is True
        kwargs = mock_pool.call_args.kwargs
        assert kwargs["headers"] == {"X-Custom-Header": "put_header_val"}
        assert kwargs["json_data"] == {"item_name": "updated_item"}


@pytest.mark.asyncio
async def test_09_patch_header_parameter_routes_to_headers():
    adapter = GenericRESTAdapter()
    req = ConnectorRequestModel(
        provider="generic_rest",
        operation_id="test_patch",
        parameters={
            "url": "https://example.com/api",
            "http_method": "PATCH",
            "is_dynamic_api": True,
            "header_params": ["X-Patch-Header"],
            "X-Patch-Header": "patch_header_val",
            "status": "active"
        }
    )
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_pool:
        mock_pool.return_value = {"status": "ok"}
        res = await adapter.execute_operation(req)
        assert res.success is True
        kwargs = mock_pool.call_args.kwargs
        assert kwargs["headers"] == {"X-Patch-Header": "patch_header_val"}
        assert kwargs["json_data"] == {"status": "active"}


@pytest.mark.asyncio
async def test_10_get_header_parameter_routes_to_headers():
    adapter = GenericRESTAdapter()
    req = ConnectorRequestModel(
        provider="generic_rest",
        operation_id="test_get",
        parameters={
            "url": "https://example.com/api",
            "http_method": "GET",
            "is_dynamic_api": True,
            "header_params": ["X-Get-Header"],
            "X-Get-Header": "get_header_val",
            "filter": "active"
        }
    )
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_pool:
        mock_pool.return_value = {"status": "ok"}
        res = await adapter.execute_operation(req)
        assert res.success is True
        kwargs = mock_pool.call_args.kwargs
        assert kwargs["headers"] == {"X-Get-Header": "get_header_val"}
        assert kwargs["params"] == {"filter": "active"}
        assert kwargs["json_data"] is None


@pytest.mark.asyncio
async def test_11_delete_header_parameter_routes_to_headers():
    adapter = GenericRESTAdapter()
    req = ConnectorRequestModel(
        provider="generic_rest",
        operation_id="test_delete",
        parameters={
            "url": "https://example.com/api",
            "http_method": "DELETE",
            "is_dynamic_api": True,
            "header_params": ["X-Delete-Token"],
            "X-Delete-Token": "del_token_123"
        }
    )
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_pool:
        mock_pool.return_value = {"status": "ok"}
        res = await adapter.execute_operation(req)
        assert res.success is True
        kwargs = mock_pool.call_args.kwargs
        assert kwargs["headers"] == {"X-Delete-Token": "del_token_123"}
        assert kwargs["params"] is None
        assert kwargs["json_data"] is None


@pytest.mark.asyncio
async def test_12_post_query_header_body_simultaneously():
    adapter = GenericRESTAdapter()
    req = ConnectorRequestModel(
        provider="generic_rest",
        operation_id="test_simultaneous",
        parameters={
            "url": "https://example.com/resource",
            "http_method": "POST",
            "is_dynamic_api": True,
            "query_params": ["id"],
            "header_params": ["X-Test-Header"],
            "id": "123",
            "X-Test-Header": "abc",
            "name": "Alice"
        }
    )
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_pool:
        mock_pool.return_value = {"status": "ok"}
        res = await adapter.execute_operation(req)
        assert res.success is True
        kwargs = mock_pool.call_args.kwargs
        assert kwargs["params"] == {"id": "123"}
        assert kwargs["headers"] == {"X-Test-Header": "abc"}
        assert kwargs["json_data"] == {"name": "Alice"}


@pytest.mark.asyncio
async def test_13_path_query_header_body_simultaneously():
    adapter = GenericRESTAdapter()
    req = ConnectorRequestModel(
        provider="generic_rest",
        operation_id="test_path_query_header_body",
        parameters={
            "url": "https://example.com/users/{userId}",
            "http_method": "POST",
            "is_dynamic_api": True,
            "query_params": ["notify"],
            "header_params": ["X-Test-Header"],
            "userId": "999",
            "notify": "true",
            "X-Test-Header": "abc",
            "name": "Alice"
        }
    )
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_pool:
        mock_pool.return_value = {"status": "ok"}
        res = await adapter.execute_operation(req)
        assert res.success is True
        args = mock_pool.call_args.args
        kwargs = mock_pool.call_args.kwargs
        assert args[1] == "https://example.com/users/999"
        assert kwargs["params"] == {"notify": "true"}
        assert kwargs["headers"] == {"X-Test-Header": "abc"}
        assert kwargs["json_data"] == {"name": "Alice"}


@pytest.mark.asyncio
async def test_14_internal_control_keys_do_not_leak_into_headers():
    adapter = GenericRESTAdapter()
    req = ConnectorRequestModel(
        provider="generic_rest",
        operation_id="test_control_keys_headers",
        parameters={
            "url": "https://example.com/api",
            "http_method": "POST",
            "is_dynamic_api": True,
            "header_params": ["is_dynamic_api", "url", "X-Valid-Header"],
            "X-Valid-Header": "valid_value"
        }
    )
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_pool:
        mock_pool.return_value = {"status": "ok"}
        res = await adapter.execute_operation(req)
        assert res.success is True
        kwargs = mock_pool.call_args.kwargs
        assert "is_dynamic_api" not in kwargs["headers"]
        assert "url" not in kwargs["headers"]
        assert kwargs["headers"] == {"X-Valid-Header": "valid_value"}


@pytest.mark.asyncio
async def test_15_internal_control_keys_do_not_leak_into_params():
    adapter = GenericRESTAdapter()
    req = ConnectorRequestModel(
        provider="generic_rest",
        operation_id="test_control_keys_params",
        parameters={
            "url": "https://example.com/api",
            "http_method": "GET",
            "is_dynamic_api": True,
            "header_params": ["X-Header-1"],
            "X-Header-1": "h_val",
            "search": "test"
        }
    )
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_pool:
        mock_pool.return_value = {"status": "ok"}
        res = await adapter.execute_operation(req)
        assert res.success is True
        kwargs = mock_pool.call_args.kwargs
        assert kwargs["params"] == {"search": "test"}
        assert "url" not in kwargs["params"]
        assert "http_method" not in kwargs["params"]
        assert "is_dynamic_api" not in kwargs["params"]
        assert "header_params" not in kwargs["params"]


@pytest.mark.asyncio
async def test_16_internal_control_keys_do_not_leak_into_json_data():
    adapter = GenericRESTAdapter()
    req = ConnectorRequestModel(
        provider="generic_rest",
        operation_id="test_control_keys_json",
        parameters={
            "url": "https://example.com/api",
            "http_method": "POST",
            "is_dynamic_api": True,
            "header_params": ["X-Header-1"],
            "X-Header-1": "h_val",
            "query_params": ["q"],
            "q": "search_val",
            "title": "Document Title"
        }
    )
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_pool:
        mock_pool.return_value = {"status": "ok"}
        res = await adapter.execute_operation(req)
        assert res.success is True
        kwargs = mock_pool.call_args.kwargs
        json_body = kwargs["json_data"]
        assert json_body == {"title": "Document Title"}
        for control_key in ["url", "http_method", "is_dynamic_api", "query_params", "header_params"]:
            assert control_key not in json_body


@pytest.mark.asyncio
async def test_17_explicit_request_body_remains_unchanged():
    adapter = GenericRESTAdapter()
    req = ConnectorRequestModel(
        provider="generic_rest",
        operation_id="test_explicit_body",
        parameters={
            "url": "https://example.com/api",
            "http_method": "POST",
            "is_dynamic_api": True,
            "header_params": ["X-Auth-Header"],
            "X-Auth-Header": "auth_val"
        },
        body={"explicit": "body_override"}
    )
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_pool:
        mock_pool.return_value = {"status": "ok"}
        res = await adapter.execute_operation(req)
        assert res.success is True
        kwargs = mock_pool.call_args.kwargs
        assert kwargs["json_data"] == {"explicit": "body_override"}
        assert kwargs["headers"] == {"X-Auth-Header": "auth_val"}


@pytest.mark.asyncio
async def test_18_existing_explicit_headers_remain_functional():
    adapter = GenericRESTAdapter()
    req = ConnectorRequestModel(
        provider="generic_rest",
        operation_id="test_explicit_headers",
        parameters={
            "url": "https://example.com/api",
            "http_method": "POST",
            "is_dynamic_api": True,
            "headers": {"Authorization": "Bearer token123"},
            "header_params": ["X-Tenant-ID"],
            "X-Tenant-ID": "tenant_456"
        }
    )
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_pool:
        mock_pool.return_value = {"status": "ok"}
        res = await adapter.execute_operation(req)
        assert res.success is True
        kwargs = mock_pool.call_args.kwargs
        assert kwargs["headers"] == {
            "Authorization": "Bearer token123",
            "X-Tenant-ID": "tenant_456"
        }


@pytest.mark.asyncio
async def test_19_multiple_headers_multiple_queries_body():
    adapter = GenericRESTAdapter()
    req = ConnectorRequestModel(
        provider="generic_rest",
        operation_id="test_multi_param_types",
        parameters={
            "url": "https://example.com/api",
            "http_method": "POST",
            "is_dynamic_api": True,
            "query_params": ["page", "limit"],
            "header_params": ["X-Correlation-ID", "X-Client-ID"],
            "page": "1",
            "limit": "50",
            "X-Correlation-ID": "corr-777",
            "X-Client-ID": "client-888",
            "username": "bob",
            "email": "bob@example.com"
        }
    )
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_pool:
        mock_pool.return_value = {"status": "ok"}
        res = await adapter.execute_operation(req)
        assert res.success is True
        kwargs = mock_pool.call_args.kwargs
        assert kwargs["params"] == {"page": "1", "limit": "50"}
        assert kwargs["headers"] == {"X-Correlation-ID": "corr-777", "X-Client-ID": "client-888"}
        assert kwargs["json_data"] == {"username": "bob", "email": "bob@example.com"}


@pytest.mark.asyncio
async def test_20_existing_non_dynamic_generic_rest_behavior_unchanged():
    adapter = GenericRESTAdapter()
    req = ConnectorRequestModel(
        provider="generic_rest",
        operation_id="generic.http.request",
        parameters={
            "url": "https://httpbin.org/post",
            "method": "POST",
            "foo": "bar"
        }
    )
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_pool:
        mock_pool.return_value = {"status": "ok"}
        res = await adapter.execute_operation(req)
        assert res.success is True
        kwargs = mock_pool.call_args.kwargs
        assert kwargs["headers"] is None
        assert kwargs["params"] is None
        assert kwargs["json_data"] == {"foo": "bar"}
