import pytest
from app.nodes.condition.node import ConditionNode
from app.nodes.expression_engine import ExpressionEngine, expression_engine
from app.nodes.loop.node import LoopNode
from app.nodes.merge.node import MergeNode
from app.nodes.switch.node import SwitchNode


@pytest.mark.asyncio
async def test_expression_engine_evaluation():
    scope = {
        "node": {
            "Gmail": {"subject": "Urgent Invoice PDF"},
            "Sheets": {"amount": 500},
        }
    }

    # String function
    sub_upper = expression_engine.evaluate("{{$node.Gmail.subject.toUpperCase()}}", scope)
    assert sub_upper == "URGENT INVOICE PDF"

    # Arithmetic
    amt = expression_engine.evaluate("{{$node.Sheets.amount + 100}}", scope)
    assert amt == 600.0

    # System variables
    now = expression_engine.evaluate("{{$now}}", scope)
    assert now != ""


@pytest.mark.asyncio
async def test_condition_node_execution():
    scope = {"node": {"Sheets": {"amount": 250}}}
    params = {"left_value": "{{$node.Sheets.amount}}", "operator": "Greater Than", "right_value": "100"}

    res = ConditionNode.evaluate_condition(params, scope)
    assert res["result"] is True
    assert res["selected_branch"] == "true_branch"


@pytest.mark.asyncio
async def test_switch_node_execution():
    scope = {"node": {"country": "USA"}}
    params = {
        "value": "{{$node.country}}",
        "cases": [
            {"case_val": "India", "branch": "branch_in"},
            {"case_val": "USA", "branch": "branch_us"},
        ],
        "default_branch": "branch_def",
    }

    res = SwitchNode.evaluate_switch(params, scope)
    assert res["selected_branch"] == "branch_us"


@pytest.mark.asyncio
async def test_loop_node_execution():
    scope = {"node": {"Sheets": {"values": ["Row 1", "Row 2", "Row 3"]}}}
    params = {"collection": "{{$node.Sheets.values}}"}

    res = LoopNode.process_loop(params, scope)
    assert res["total_items"] == 3
    assert len(res["iterations"]) == 3
    assert res["iterations"][0]["$loop"]["index"] == 0
    assert res["iterations"][0]["$loop"]["item"] == "Row 1"


@pytest.mark.asyncio
async def test_merge_node_execution():
    scope = {
        "previous_outputs": {
            "branch_a": {"status": "ok"},
            "branch_b": {"status": "ok"},
        }
    }
    params = {"mode": "Wait All"}

    res = MergeNode.process_merge(params, scope)
    assert res["merged_count"] == 2
    assert res["mode"] == "Wait All"
