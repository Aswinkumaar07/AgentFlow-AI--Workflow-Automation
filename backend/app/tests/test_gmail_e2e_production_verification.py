import pytest
import time
from app.agents.planner.planner_v4 import intelligent_planner_v4
from app.agents.validator.workflow_validator import workflow_validator
from app.runtime.workflow_executor import workflow_runtime_executor_v3
from app.oauth.manager import oauth_manager


@pytest.mark.asyncio
async def test_gmail_e2e_production_verification_pipeline():
    prompt = "Send good night email to test@example.com"

    # 1. Planner V5 Intent & DAG Generation
    plan = intelligent_planner_v4.plan(prompt)
    graph = plan.workflow_graph

    assert plan.intent in ["EMAIL_SEND", "SAAS_WORKFLOW_AUTOMATION"]
    assert "Gmail" in plan.selected_connectors
    assert len(graph["nodes"]) == 1

    gmail_node = graph["nodes"][0]
    assert gmail_node["provider"] == "gmail"
    assert gmail_node["operation"] == "gmail.messages.send"
    assert gmail_node["parameters"]["to"] == "test@example.com"
    assert gmail_node["parameters"]["subject"] == "Good Night 🌙"
    assert "Good Night" in gmail_node["parameters"]["body"]
    assert "Sleep well." in gmail_node["parameters"]["body"]

    # 2. Pre-execution DAG Validation
    val_res = workflow_validator.validate_workflow(graph)
    assert val_res.is_valid is True
    assert len(val_res.errors) == 0

    # 3. Full Runtime Execution Stack
    state = await workflow_runtime_executor_v3.execute_workflow(graph)
    assert state.execution_id is not None

    rec = state.node_records["step_1"]
    status = rec.get("status")
    output = rec.get("output", {})

    # 4. Strict Non-Mocked Enforcement
    if status == "COMPLETED":
        assert output.get("status_code") in [200, 201, 202]
        assert "provider_message_id" in output or "messageId" in output
    else:
        # On OAuth/API failure, must explicitly report FAILED (never fake success)
        assert status == "FAILED"
        assert output.get("status_code") in [400, 401, 403, 429, 500]
        assert "error" in output

    # 5. Collect Audit Telemetry
    assert "request" in output
    assert "response" in output
    assert "latency_ms" in output
    assert "retries" in output or "retry_count" in output
