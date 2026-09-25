import pytest
from app.runtime.node_executor import node_executor
from app.runtime.live_node_executor import live_node_executor
from app.connectors.security.secret_manager import secret_manager
from app.connectors.models import ConnectorCredentialModel


@pytest.mark.asyncio
async def test_real_node_executor_generic_http():
    node_input = {
        "metadata": {
            "node_id": "step_real_1",
            "interpolated_params": {"url": "https://httpbin.org/post", "method": "POST"},
        },
        "workflow": {
            "steps": [
                {
                    "step_id": "step_real_1",
                    "provider": "Generic REST",
                    "operation_id": "generic.http.request",
                    "parameters": {"url": "https://httpbin.org/post"},
                }
            ]
        },
        "tenant_id": "usr_1",
    }

    res = await node_executor.execute_node(node_input)
    assert res["node_id"] == "step_real_1"
    assert "output" in res
    output = res["output"]
    assert "status_code" in output
    assert "latency_ms" in output
    assert "request" in output
    assert "response" in output
    assert output["request"]["url"] == "https://httpbin.org/post"


@pytest.mark.asyncio
async def test_real_live_node_executor_credential_injection():
    # Store test credential
    cred = ConnectorCredentialModel(
        tenant_id="usr_real_test",
        provider="Slack",
        auth_type="Bearer",
        access_token="xoxb-real-slack-test-token",
    )
    await secret_manager.set_secret("usr_real_test", "Slack", cred)

    node = {
        "id": "step_slack_real",
        "provider": "Slack",
        "operation_id": "slack.chat.postMessage",
        "parameters": {"channel": "#general", "text": "Real Execution Test"},
    }

    result = await live_node_executor.execute_node(node, tenant_id="usr_real_test")
    assert result.node_id == "step_slack_real"
    assert result.provider == "Slack"
    assert result.latency_ms > 0
    assert "request" in result.model_dump()
    assert "headers" in result.request
    assert result.request["url"] == "https://slack.com/api/chat.postMessage"


@pytest.mark.asyncio
async def test_mock_failure_provider_dlq():
    node_input = {
        "metadata": {
            "node_id": "step_fail_1",
            "interpolated_params": {},
        },
        "workflow": {
            "steps": [
                {
                    "step_id": "step_fail_1",
                    "provider": "MockFailureProvider",
                    "operation_id": "fail",
                }
            ]
        },
    }

    res = await node_executor.execute_node(node_input)
    assert res["status"] == "FAILED"
    assert "Simulated failure for DLQ" in res["output"]["error"]
