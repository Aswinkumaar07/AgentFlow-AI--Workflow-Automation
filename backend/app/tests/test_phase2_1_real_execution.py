import pytest
from app.oauth.manager import oauth_manager
from app.agents.oauth_ai.account_picker import account_picker
from app.agents.validator.workflow_validator import workflow_validator
from app.agents.planner.planner_v4 import intelligent_planner_v4


@pytest.mark.asyncio
async def test_no_mock_seed_credentials():
    user_conns = await oauth_manager.get_user_connections("usr_new_999")
    assert len(user_conns) == 0


@pytest.mark.asyncio
async def test_live_connection_unconnected_result():
    res = await oauth_manager.test_live_connection("usr_unbound", "Gmail")
    assert res["success"] is False
    assert res["is_connected"] is False
    assert "No connected account found" in res["message"]


def test_mandatory_trigger_validation_failure():
    graph_no_trigger = {
        "nodes": [
            {
                "id": "step_1",
                "provider": "Gmail",
                "operation_id": "gmail.messages.send",
                "parameters": {"to": "user@example.com"},
            }
        ],
        "edges": [],
    }

    res = workflow_validator.validate_workflow(graph_no_trigger)
    assert res.is_valid is False
    assert any("Workflow missing mandatory trigger" in err for err in res.errors)


def test_invalid_loop_variable_validation():
    graph_invalid_loop = {
        "trigger": {"type": "Manual"},
        "nodes": [
            {
                "id": "step_1",
                "provider": "Gmail",
                "operation_id": "gmail.messages.send",
                "parameters": {"to": "{{$loop.item.email}}"},
            }
        ],
        "edges": [],
    }

    res = workflow_validator.validate_workflow(graph_invalid_loop)
    assert res.is_valid is False
    assert any("No preceding Loop node in workflow" in err for err in res.errors)


def test_invalid_node_variable_reference():
    graph_invalid_node_ref = {
        "trigger": {"type": "Manual"},
        "nodes": [
            {
                "id": "step_1",
                "provider": "Gmail",
                "operation_id": "gmail.messages.send",
                "parameters": {"body": "{{$node.missing_step.output}}"},
            }
        ],
        "edges": [],
    }

    res = workflow_validator.validate_workflow(graph_invalid_node_ref)
    assert res.is_valid is False
    assert any("Referenced node 'missing_step' does not exist" in err for err in res.errors)


def test_planner_v4_always_includes_trigger():
    plan = intelligent_planner_v4.plan("Send welcome email to john@example.com")
    graph = plan.workflow_graph
    assert "trigger" in graph
    assert graph["trigger"]["type"] == "Manual"

    val_res = workflow_validator.validate_workflow(graph)
    assert val_res.is_valid is True
