import json
from unittest.mock import AsyncMock, patch

import pytest

from app.agents.api_discovery.dynamic_discovery import (
    DynamicConnectorSpec,
    DynamicDiscoveryResult,
)
from app.agents.api_discovery.fetcher import (
    HTTPFetchError,
    SpecFetcher,
    SpecFetchResult,
    SSRFBlockedError,
)
from app.agents.api_discovery.service import APIDiscoveryAgent, api_discovery_agent
from app.agents.connector_ai.connector_selector import connector_selector
from app.agents.connector_ai.operation_ranker import operation_ranker


@pytest.fixture
def agent():
    return APIDiscoveryAgent()


@pytest.mark.asyncio
async def test_valid_remote_openapi_json_discovery_bridge(agent):
    valid_openapi = {
        "openapi": "3.0.0",
        "info": {"title": "Weather Service API", "version": "v1"},
        "paths": {
            "/v1/forecast": {
                "get": {
                    "summary": "Get weather forecast for location",
                    "operationId": "weather_service.forecast.get",
                    "parameters": [{"name": "location", "required": True}],
                }
            }
        },
    }
    json_content = json.dumps(valid_openapi)

    mock_fetcher = AsyncMock(spec=SpecFetcher)
    mock_fetcher.fetch.return_value = SpecFetchResult(
        requested_url="https://api.weather-service.com/openapi.json",
        final_url="https://api.weather-service.com/openapi.json",
        content=json_content,
        content_type="application/json",
        content_length=len(json_content),
        status_code=200,
        duration_ms=42.0,
        format_hint="json",
    )

    res: DynamicDiscoveryResult = await agent.discover_and_register_from_url(
        "https://api.weather-service.com/openapi.json", fetcher_override=mock_fetcher
    )

    assert res.success is True
    assert res.provider == "Weather Service API"
    assert res.endpoints_indexed == 1
    assert res.connector_spec.provider == "Weather Service API"

    # Verify endpoint is registered into live in-memory catalog
    ops = [op["operation"] for op in operation_ranker.OPERATION_CATALOG]
    assert "weather_service.forecast.get" in ops

    providers = [c["provider"] for c in connector_selector.CONNECTOR_CATALOG]
    assert "Weather Service API" in providers


@pytest.mark.asyncio
async def test_valid_remote_openapi_yaml_discovery_bridge(agent):
    yaml_spec = """
openapi: 3.0.0
info:
  title: Petstore YAML API
  version: 1.0.0
paths:
  /pets:
    get:
      summary: List all pets
      operationId: petstore_yaml.pets.list
"""
    mock_fetcher = AsyncMock(spec=SpecFetcher)
    mock_fetcher.fetch.return_value = SpecFetchResult(
        requested_url="https://api.petstore.com/openapi.yaml",
        final_url="https://api.petstore.com/openapi.yaml",
        content=yaml_spec,
        content_type="application/yaml",
        content_length=len(yaml_spec),
        status_code=200,
        duration_ms=35.0,
        format_hint="yaml",
    )

    res = await agent.discover_and_register_from_url(
        "https://api.petstore.com/openapi.yaml", fetcher_override=mock_fetcher
    )

    assert res.success is True
    assert res.provider == "Petstore YAML API"

    ops = [op["operation"] for op in operation_ranker.OPERATION_CATALOG]
    assert "petstore_yaml.pets.list" in ops


@pytest.mark.asyncio
async def test_multiple_endpoints_registered_in_bridge(agent):
    openapi_multi = {
        "openapi": "3.0.0",
        "info": {"title": "MultiEndpoint Service", "version": "v2"},
        "paths": {
            "/v2/items": {
                "get": {
                    "summary": "List items",
                    "operationId": "multi.items.list",
                },
                "post": {
                    "summary": "Create item",
                    "operationId": "multi.items.create",
                },
            }
        },
    }
    json_str = json.dumps(openapi_multi)

    mock_fetcher = AsyncMock(spec=SpecFetcher)
    mock_fetcher.fetch.return_value = SpecFetchResult(
        requested_url="https://api.multi.com/openapi.json",
        final_url="https://api.multi.com/openapi.json",
        content=json_str,
        content_type="application/json",
        content_length=len(json_str),
        status_code=200,
        duration_ms=50.0,
        format_hint="json",
    )

    res = await agent.discover_and_register_from_url(
        "https://api.multi.com/openapi.json", fetcher_override=mock_fetcher
    )

    assert res.success is True
    assert res.endpoints_indexed == 2
    ops = [op["operation"] for op in operation_ranker.OPERATION_CATALOG]
    assert "multi.items.list" in ops
    assert "multi.items.create" in ops


@pytest.mark.asyncio
async def test_duplicate_operation_registration_safety(agent):
    openapi_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Idempotent Service", "version": "v1"},
        "paths": {
            "/v1/data": {
                "get": {
                    "summary": "Get data",
                    "operationId": "idempotent.data.get",
                }
            }
        },
    }
    json_str = json.dumps(openapi_spec)

    mock_fetcher = AsyncMock(spec=SpecFetcher)
    mock_fetcher.fetch.return_value = SpecFetchResult(
        requested_url="https://api.idempotent.com/spec.json",
        final_url="https://api.idempotent.com/spec.json",
        content=json_str,
        content_type="application/json",
        content_length=len(json_str),
        status_code=200,
        duration_ms=10.0,
        format_hint="json",
    )

    # Register first time
    res1 = await agent.discover_and_register_from_url(
        "https://api.idempotent.com/spec.json", fetcher_override=mock_fetcher
    )
    count_first = operation_ranker.OPERATION_CATALOG.count(
        next(
            op
            for op in operation_ranker.OPERATION_CATALOG
            if op["operation"] == "idempotent.data.get"
        )
    )

    # Register second time
    res2 = await agent.discover_and_register_from_url(
        "https://api.idempotent.com/spec.json", fetcher_override=mock_fetcher
    )
    count_second = operation_ranker.OPERATION_CATALOG.count(
        next(
            op
            for op in operation_ranker.OPERATION_CATALOG
            if op["operation"] == "idempotent.data.get"
        )
    )

    assert count_first == 1
    assert count_second == 1  # No duplicate entries appended


@pytest.mark.asyncio
async def test_spec_fetcher_failure_propagation(agent):
    mock_fetcher = AsyncMock(spec=SpecFetcher)
    mock_fetcher.fetch.side_effect = SSRFBlockedError("SSRF attempt to 127.0.0.1 blocked")

    res = await agent.discover_and_register_from_url(
        "https://127.0.0.1/malicious.json", fetcher_override=mock_fetcher
    )

    assert res.success is False
    assert res.provider == "Unknown"
    assert "SSRF attempt" in res.message


@pytest.mark.asyncio
async def test_invalid_spec_content_controlled_failure(agent):
    mock_fetcher = AsyncMock(spec=SpecFetcher)
    mock_fetcher.fetch.return_value = SpecFetchResult(
        requested_url="https://api.example.com/invalid.json",
        final_url="https://api.example.com/invalid.json",
        content="{'invalid_json_format': unquoted_string}",
        content_type="application/json",
        content_length=40,
        status_code=200,
        duration_ms=12.0,
        format_hint="json",
    )

    res = await agent.discover_and_register_from_url(
        "https://api.example.com/invalid.json", fetcher_override=mock_fetcher
    )

    assert res.success is False
    assert "Spec parse error" in res.message


@pytest.mark.asyncio
async def test_planner_and_execution_untouched(agent):
    # Verify planner imports and DAG execution engine modules are unmodified and not invoked by bridge
    from app.agents.planner.planner_v4 import IntelligentPlannerEngineV4
    from app.runtime.dag_execution_engine import DAGExecutionEngine

    # Check that calling discover_and_register_from_url does NOT invoke planner.plan or execution
    with patch.object(
        IntelligentPlannerEngineV4, "plan"
    ) as mock_plan, patch.object(
        DAGExecutionEngine, "execute_dag"
    ) as mock_exec:
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {"title": "Isolated Service", "version": "v1"},
            "paths": {
                "/v1/ping": {
                    "get": {
                        "summary": "Ping",
                        "operationId": "isolated.ping.get",
                    }
                }
            },
        }
        mock_fetcher = AsyncMock(spec=SpecFetcher)
        mock_fetcher.fetch.return_value = SpecFetchResult(
            requested_url="https://api.isolated.com/spec.json",
            final_url="https://api.isolated.com/spec.json",
            content=json.dumps(openapi_spec),
            content_type="application/json",
            content_length=100,
            status_code=200,
            duration_ms=5.0,
            format_hint="json",
        )

        res = await agent.discover_and_register_from_url(
            "https://api.isolated.com/spec.json", fetcher_override=mock_fetcher
        )

        assert res.success is True
        mock_plan.assert_not_called()
        mock_exec.assert_not_called()
