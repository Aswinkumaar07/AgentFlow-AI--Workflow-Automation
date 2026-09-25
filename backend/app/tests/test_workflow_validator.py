import pytest
from app.agents.validator import workflow_validator, validator_ai_service


def test_validator_valid_dag():
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [
            {"id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.send"},
            {"id": "step_2", "provider": "Slack", "operation_id": "slack.chat.postMessage"},
        ],
        "edges": [{"id": "e1-2", "source": "step_1", "target": "step_2"}],
    }
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is True
    assert len(res.errors) == 0
    assert res.confidence >= 0.85


def test_validator_cycle_detection():
    # Graph with cycle: step_1 -> step_2 -> step_1
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [
            {"id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.send"},
            {"id": "step_2", "provider": "Slack", "operation_id": "slack.chat.postMessage"},
        ],
        "edges": [
            {"id": "e1-2", "source": "step_1", "target": "step_2"},
            {"id": "e2-1", "source": "step_2", "target": "step_1"},
        ],
    }
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is False
    assert any("Cycle detected" in err for err in res.errors)
    assert res.confidence == 0.0


def test_validator_unknown_connector():
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [{"id": "step_1", "provider": "UnknownInvalidProvider", "operation_id": "invalid.op"}],
        "edges": [],
    }
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is False
    assert any("Unknown connector provider" in err for err in res.errors)


def test_validator_duplicate_node_ids():
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [
            {"id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.send"},
            {"id": "step_1", "provider": "Slack", "operation_id": "slack.chat.postMessage"},
        ],
        "edges": [],
    }
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is False
    assert any("Duplicate node ID" in err for err in res.errors)


def test_validator_invalid_expression():
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [
            {
                "id": "step_1",
                "provider": "Gmail",
                "operation_id": "gmail.messages.send",
                "parameters": {"subject": "Hello {{unclosed_var"},
            }
        ],
        "edges": [],
    }
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is False
    assert any("Invalid expression syntax" in err for err in res.errors)


def test_validator_oauth_warnings():
    graph = {
        "trigger": {"type": "Manual"},
        "nodes": [{"id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.send"}],
        "edges": [],
    }
    res = workflow_validator.validate_workflow(graph)
    assert res.is_valid is True
    assert any("OAuth" in warn for warn in res.warnings)
