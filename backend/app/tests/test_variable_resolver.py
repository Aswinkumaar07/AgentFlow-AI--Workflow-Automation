import pytest
from app.agents.variables import variable_resolver, variable_ai_service, VariableDiscoveryResult


def test_variable_resolver_system_vars():
    graph = {"nodes": [], "edges": []}
    res = variable_resolver.discover_variables(graph)
    assert isinstance(res, VariableDiscoveryResult)
    expressions = [v.expression for v in res.system_variables]
    assert "{{$today}}" in expressions
    assert "{{$now}}" in expressions
    assert "{{$uuid}}" in expressions


def test_variable_resolver_loop_vars():
    graph = {"nodes": [], "edges": []}
    res = variable_resolver.discover_variables(graph)
    expressions = [v.expression for v in res.loop_variables]
    assert "{{$loop.item}}" in expressions
    assert "{{$loop.item.email}}" in expressions
    assert "{{$loop.index}}" in expressions


def test_variable_resolver_node_outputs():
    graph = {
        "nodes": [
            {"id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.list"},
            {"id": "step_2", "provider": "Google Sheets", "operation_id": "sheets.spreadsheets.values.get"},
        ],
        "edges": [],
    }
    res = variable_resolver.discover_variables(graph)
    expressions = [v.expression for v in res.node_outputs]
    assert "{{$node.Gmail.subject}}" in expressions
    assert "{{$node.Google Sheets.values}}" in expressions


def test_variable_ai_service_dict_output():
    graph = {
        "trigger": {"type": "Webhook"},
        "nodes": [{"id": "step_1", "provider": "AI", "operation_id": "ai.summarize"}],
    }
    data = variable_ai_service.discover(graph)
    assert "node_outputs" in data
    assert "system_variables" in data
    assert "loop_variables" in data
    assert "trigger_variables" in data
