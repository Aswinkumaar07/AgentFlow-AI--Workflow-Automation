import pytest
from app.runtime.live_node_executor import live_node_executor
from app.runtime.node_executor import node_executor
from app.connectors.security.secret_manager import secret_manager
from app.connectors.models import ConnectorCredentialModel


@pytest.mark.asyncio
async def test_gmail_runtime_execution_routing_and_telemetry():
    node = {
        "id": "step_gmail_send_test",
        "provider": "Gmail",
        "operation_id": "gmail.messages.send",
        "parameters": {
            "to": "recipient@example.com",
            "subject": "Runtime Test Subject",
            "body": "Runtime Test Body",
        },
    }

    result = await live_node_executor.execute_node(node, tenant_id="usr_test_rt")

    assert result.node_id == "step_gmail_send_test"
    assert result.provider == "Gmail"
    assert result.operation_id == "gmail.messages.send"
    assert result.latency_ms >= 0

    # Verify request telemetry
    assert "request" in result.model_dump()
    assert "payload" in result.request
    assert result.request["payload"]["to"] == "recipient@example.com"

    # Verify response telemetry
    assert "response" in result.model_dump()
    assert "status_code" in result.response
    assert "body" in result.response

    # Verify execution logs
    assert len(result.logs) >= 2
    assert any("Routing to GmailAdapter" in log for log in result.logs)
    assert any("Gmail API response completed" in log for log in result.logs)


@pytest.mark.asyncio
async def test_gmail_node_executor_wrapper_integration():
    node_input = {
        "metadata": {
            "node_id": "step_gmail_exec_node",
            "interpolated_params": {
                "to": "test@domain.com",
                "subject": "Node Executor Subject",
                "body": "Node Executor Body",
            },
        },
        "workflow": {
            "steps": [
                {
                    "step_id": "step_gmail_exec_node",
                    "provider": "Gmail",
                    "operation_id": "gmail.messages.send",
                    "parameters": {"to": "test@domain.com"},
                }
            ]
        },
        "tenant_id": "usr_test_rt",
    }

    res = await node_executor.execute_node(node_input)
    assert res["node_id"] == "step_gmail_exec_node"
    assert "status" in res
    output = res["output"]

    assert "status_code" in output
    assert "latency_ms" in output
    assert "request" in output
    assert "response" in output
    assert "headers" in output
