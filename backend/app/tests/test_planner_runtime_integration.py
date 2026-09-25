import pytest
from app.agents.planner.planner_v4 import intelligent_planner_v4
from app.agents.validator.workflow_validator import workflow_validator
from app.runtime.workflow_executor import workflow_runtime_executor_v3


@pytest.mark.asyncio
async def test_planner_to_runtime_direct_execution_good_night():
    prompt = "Send good night email to john@example.com"
    plan = intelligent_planner_v4.plan(prompt)
    graph = plan.workflow_graph

    # 1. Verify Planner Payload Specification
    gmail_node = next(n for n in graph["nodes"] if n["provider"] == "gmail")
    assert gmail_node["provider"] == "gmail"
    assert gmail_node["operation"] == "gmail.messages.send"
    assert gmail_node["parameters"]["to"] == "john@example.com"
    assert gmail_node["parameters"]["subject"] == "Good Night 🌙"
    assert "Good Night" in gmail_node["parameters"]["body"]
    assert gmail_node["authentication"] == "google_oauth"
    assert "runtime_metadata" in gmail_node
    assert "execution_metadata" in gmail_node

    # 2. Verify Pre-execution Validation passes
    val_res = workflow_validator.validate_workflow(graph)
    assert val_res.is_valid is True
    assert len(val_res.errors) == 0

    # 3. Direct Runtime Execution without Transformation
    state = await workflow_runtime_executor_v3.execute_workflow(graph)
    assert state.status in ["COMPLETED", "FAILED"]
    assert "step_1" in state.node_records

    rec = state.node_records["step_1"]
    output = rec.get("output", {})
    assert "status_code" in output
    assert "latency_ms" in output
    assert "request" in output
    assert "response" in output


@pytest.mark.asyncio
async def test_workflow_validator_pre_execution_rejection():
    invalid_graph = {
        "title": "Invalid Workflow Test",
        "trigger": {"type": "Manual"},
        "nodes": [
            {
                "id": "step_bad_1",
                "provider": "gmail",
                "operation": "gmail.messages.send",
                "parameters": {
                    # Missing required "to" and "subject" and "body"
                },
                "authentication": "google_oauth",
            }
        ],
    }

    val_res = workflow_validator.validate_workflow(invalid_graph)
    assert val_res.is_valid is False
    assert len(val_res.errors) >= 1
    assert any("Required parameter" in err for err in val_res.errors)
