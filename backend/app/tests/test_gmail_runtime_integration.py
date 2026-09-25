import pytest
from app.runtime.workflow_executor import workflow_runtime_executor_v3
from app.connectors.registry import connector_registry
from app.connectors.providers.gmail.adapter import GmailAdapter


@pytest.mark.asyncio
async def test_gmail_adapter_registered_in_registry():
    adapter = connector_registry.get("Gmail")
    assert adapter is not None
    assert isinstance(adapter, GmailAdapter)
    assert adapter.provider_name == "Gmail"


@pytest.mark.asyncio
async def test_workflow_runtime_executor_v3_gmail_integration():
    workflow_spec = {
        "workflow_id": "wf_gmail_integration_test",
        "tenant_id": "usr_integration_test",
        "steps": [
            {
                "id": "step_gmail_1",
                "step_id": "step_gmail_1",
                "provider": "Gmail",
                "operation_id": "gmail.messages.send",
                "parameters": {
                    "to": "test@domain.com",
                    "subject": "Integration Test Mail",
                    "body": "Integration Test Body",
                },
                "dependencies": [],
            }
        ],
    }

    state = await workflow_runtime_executor_v3.execute_workflow(workflow_spec)
    assert state.execution_id is not None
    assert "step_gmail_1" in state.node_records

    rec = state.node_records["step_gmail_1"]
    assert "status" in rec
    output = rec.get("output", {})

    # Verify telemetry persistence
    assert "status_code" in output
    assert "latency_ms" in output
    assert "request" in output
    assert "response" in output
    assert "retries" in output or "retry_count" in output
    assert "provider_message_id" in output
    assert "provider_thread_id" in output


@pytest.mark.asyncio
async def test_gmail_runtime_failure_error_propagation():
    workflow_spec = {
        "workflow_id": "wf_gmail_fail_test",
        "tenant_id": "usr_integration_test",
        "steps": [
            {
                "id": "step_gmail_fail",
                "step_id": "step_gmail_fail",
                "provider": "Gmail",
                "operation_id": "gmail.messages.send",
                "parameters": {
                    "to": "invalid_email_no_auth",
                },
                "dependencies": [],
            }
        ],
    }

    state = await workflow_runtime_executor_v3.execute_workflow(workflow_spec)
    rec = state.node_records["step_gmail_fail"]
    output = rec.get("output", {})

    # Must preserve exact Gmail API failure details
    assert rec["status"] == "FAILED"
    assert output.get("status_code") in [400, 401, 403, 500]
    assert "error" in output
