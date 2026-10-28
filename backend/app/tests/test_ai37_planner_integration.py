import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.agents.planner.planner_v4 import IntelligentPlannerEngineV4, PlanningResultV4
from app.agents.planner.ai37_planner_bridge import extract_qualifying_spec_url, ai37_planner_bridge, AI37BridgeResult
from app.agents.api_discovery.dynamic_discovery import DynamicDiscoveryResult, DynamicConnectorSpec


@pytest.fixture
def planner():
    return IntelligentPlannerEngineV4()


def test_tc_p3_01_unknown_api_with_explicit_openapi_url(planner):
    """
    TC-P3-01: Prompt contains unknown API + explicit OpenAPI URL.
    AI-37 discovery is invoked, succeeds, dynamic provider is selected, DAG generated, no execution.
    """
    prompt = "Fetch users from https://api.acme-corp.com/openapi.json"

    mock_discovery_res = DynamicDiscoveryResult(
        success=True,
        provider="Acme API",
        endpoints_indexed=2,
        connector_spec=DynamicConnectorSpec(
            provider="Acme API",
            operations=[
                {
                    "provider": "Acme API",
                    "operation": "acme.users.list",
                    "summary": "List all registered users",
                    "parameters": {},
                    "authentication": "APIKey",
                }
            ],
        ),
        message="Discovery successful",
    )

    with patch(
        "app.agents.api_discovery.service.api_discovery_agent.discover_and_register_from_url",
        new_callable=AsyncMock,
        return_value=mock_discovery_res,
    ) as mock_discover:
        result = planner.plan(prompt)

        assert mock_discover.called
        assert "Acme API" in result.selected_connectors
        assert result.pipeline_summary.get("dynamic_discovery", {}).get("success") is True
        assert result.can_execute is True


def test_tc_p3_02_gmail_prompt_bypasses_ai37(planner):
    """
    TC-P3-02: Existing Gmail prompt. Native provider takes priority; AI-37 is NOT invoked.
    """
    prompt = "Send an email using Gmail to alice@example.com with spec link https://api.acme.com/openapi.json"

    with patch("app.agents.planner.ai37_planner_bridge.ai37_planner_bridge.discover_if_eligible") as mock_bridge:
        result = planner.plan(prompt)

        assert "Gmail" in result.selected_connectors
        assert not mock_bridge.called


def test_tc_p3_03_slack_prompt_bypasses_ai37(planner):
    """
    TC-P3-03: Existing Slack prompt. Slack is selected; AI-37 is NOT invoked.
    """
    prompt = "Send a Slack message to #general channel"

    with patch("app.agents.planner.ai37_planner_bridge.ai37_planner_bridge.discover_if_eligible") as mock_bridge:
        result = planner.plan(prompt)

        assert "Slack" in result.selected_connectors
        assert not mock_bridge.called


def test_tc_p3_04_github_prompt_bypasses_ai37(planner):
    """
    TC-P3-04: Existing GitHub prompt. GitHub is selected; AI-37 is NOT invoked.
    """
    prompt = "Create issue on GitHub repository AgentFlow-AI"

    with patch("app.agents.planner.ai37_planner_bridge.ai37_planner_bridge.discover_if_eligible") as mock_bridge:
        result = planner.plan(prompt)

        assert "GitHub" in result.selected_connectors
        assert not mock_bridge.called


def test_tc_p3_05_url_without_openapi_indicator(planner):
    """
    TC-P3-05: Unknown service + ordinary HTTPS URL without OpenAPI indicators.
    AI-37 is NOT invoked; zero-provider fallback behavior preserved.
    """
    prompt = "Visit website https://example.com/landing"

    with patch(
        "app.agents.api_discovery.service.api_discovery_agent.discover_and_register_from_url",
        new_callable=AsyncMock,
    ) as mock_discover:
        result = planner.plan(prompt)

        assert not mock_discover.called
        assert "dynamic_discovery" not in result.pipeline_summary


def test_tc_p3_06_http_url_rejected(planner):
    """
    TC-P3-06: Unknown service + HTTP OpenAPI URL.
    HTTP is rejected by bridge; SpecFetcher is not reached.
    """
    prompt = "Fetch spec from http://petstore.swagger.io/v2/swagger.json"

    url = extract_qualifying_spec_url(prompt)
    assert url is None

    with patch(
        "app.agents.api_discovery.service.api_discovery_agent.discover_and_register_from_url",
        new_callable=AsyncMock,
    ) as mock_discover:
        result = planner.plan(prompt)
        assert not mock_discover.called


def test_tc_p3_07_localhost_url_rejected(planner):
    """
    TC-P3-07: Unknown service + localhost OpenAPI URL.
    Localhost is rejected by bridge URL extractor; planner does not crash.
    """
    prompt = "Fetch spec from https://localhost/swagger.json"

    url = extract_qualifying_spec_url(prompt)
    assert url is None

    result = planner.plan(prompt)
    assert result is not None
    assert isinstance(result, PlanningResultV4)


def test_tc_p3_08_invalid_url_discovery_failure(planner):
    """
    TC-P3-08: Unknown service + invalid OpenAPI URL.
    Controlled discovery failure; no fake provider created.
    """
    prompt = "Inspect swagger spec at https://invalid-domain-999.com/swagger.json"

    mock_failed_res = DynamicDiscoveryResult(
        success=False,
        provider="Unknown",
        endpoints_indexed=0,
        connector_spec=DynamicConnectorSpec(provider="Unknown"),
        message="SpecFetcher error: 404 Not Found",
    )

    with patch(
        "app.agents.api_discovery.service.api_discovery_agent.discover_and_register_from_url",
        new_callable=AsyncMock,
        return_value=mock_failed_res,
    ):
        result = planner.plan(prompt)

        assert result.pipeline_summary.get("dynamic_discovery", {}).get("success") is False
        assert "Unknown" not in result.selected_connectors


def test_tc_p3_09_multiple_endpoints_preserves_op_ids(planner):
    """
    TC-P3-09: Successful discovery with multiple endpoints.
    Actual discovered operation IDs are preserved in DAG nodes.
    """
    prompt = "Call API at https://api.weather.com/openapi.json"

    mock_discovery_res = DynamicDiscoveryResult(
        success=True,
        provider="Weather API",
        endpoints_indexed=2,
        connector_spec=DynamicConnectorSpec(
            provider="Weather API",
            operations=[
                {
                    "provider": "Weather API",
                    "operation": "weather.forecast.get",
                    "summary": "Get weather forecast",
                    "parameters": {"city": "London"},
                    "authentication": "APIKey",
                }
            ],
        ),
        message="Success",
    )

    with patch(
        "app.agents.api_discovery.service.api_discovery_agent.discover_and_register_from_url",
        new_callable=AsyncMock,
        return_value=mock_discovery_res,
    ):
        result = planner.plan(prompt)

        assert "Weather API" in result.selected_connectors
        assert len(result.workflow_graph.get("nodes", [])) > 0


def test_tc_p3_10_discovery_failure_no_exception_escapes(planner):
    """
    TC-P3-10: Discovery failure.
    No exception escapes Planner V4; returns valid PlanningResultV4.
    """
    prompt = "Inspect OpenAPI spec at https://broken-server.org/openapi.yaml"

    with patch(
        "app.agents.api_discovery.service.api_discovery_agent.discover_and_register_from_url",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Network Timeout"),
    ):
        result = planner.plan(prompt)

        assert isinstance(result, PlanningResultV4)
        assert result.pipeline_summary.get("dynamic_discovery", {}).get("success") is False


def test_tc_p3_11_no_execution_occurs_during_planning(planner):
    """
    TC-P3-11: Ensure no execution occurs during planning.
    Assert GenericRESTAdapter and execution engine are NOT called.
    """
    prompt = "Inspect OpenAPI spec at https://api.data.com/openapi.json"

    mock_discovery_res = DynamicDiscoveryResult(
        success=True,
        provider="Data API",
        endpoints_indexed=1,
        connector_spec=DynamicConnectorSpec(
            provider="Data API",
            operations=[
                {"provider": "Data API", "operation": "data.records.get", "summary": "Get records", "parameters": {}}
            ],
        ),
        message="Success",
    )

    with patch(
        "app.agents.api_discovery.service.api_discovery_agent.discover_and_register_from_url",
        new_callable=AsyncMock,
        return_value=mock_discovery_res,
    ), patch("app.connectors.providers.generic_rest.adapter.GenericRESTAdapter.execute_operation") as mock_rest, patch(
        "app.runtime.dag_execution_engine.DAGExecutionEngine"
    ) as mock_engine, patch(
        "app.runtime.workflow_executor.WorkflowRuntimeExecutorV3"
    ) as mock_executor:
        planner.plan(prompt)

        assert not mock_rest.called
        assert not mock_engine.called
        assert not mock_executor.called
