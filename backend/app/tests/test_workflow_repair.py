import pytest
from app.agents.repair import workflow_repair_agent, repair_ai_service, RepairResult


def test_repair_oauth_failure():
    node = {"id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.send"}
    res = repair_ai_service.repair_failure("401 Unauthorized OAuth token expired", node)
    assert isinstance(res, RepairResult)
    assert res.problem == "OAuth2 Authorization Failure"
    assert res.auto_fix.get("refresh_oauth") is True
    assert res.confidence > 0.9


def test_repair_rate_limit_exceeded():
    node = {"id": "step_2", "provider": "Slack", "operation_id": "slack.chat.postMessage"}
    res = repair_ai_service.repair_failure("HTTP 429 Rate limit exceeded", node)
    assert res.problem == "Rate Limit Exceeded (HTTP 429)"
    assert res.auto_fix.get("retry_policy", {}).get("max_retries") == 5


def test_repair_expression_syntax():
    node = {
        "id": "step_3",
        "provider": "Gmail",
        "operation_id": "gmail.messages.send",
        "parameters": {"subject": "Hello {{$node.Gmail.subject"},
    }
    res = repair_ai_service.repair_failure("Expression syntax error mismatched braces", node)
    assert res.problem == "Expression Syntax Error"
    repaired_params = res.auto_fix.get("repaired_parameters", {})
    assert repaired_params.get("subject") == "Hello {{$node.Gmail.subject}}"


def test_repair_missing_parameter():
    node = {
        "id": "step_4",
        "provider": "Gmail",
        "operation_id": "gmail.messages.send",
        "parameters": {"to": None, "subject": "Notice"},
    }
    res = repair_ai_service.repair_failure("Missing mandatory parameter 'to'", node)
    assert res.problem == "Missing Mandatory Parameter"
    repaired_params = res.auto_fix.get("repaired_parameters", {})
    assert repaired_params.get("to") == "{{$loop.item.email}}"


def test_repair_unresolved_variable():
    node = {"id": "step_5", "provider": "AI", "operation_id": "ai.summarize"}
    res = repair_ai_service.repair_failure("Unresolved variable reference KeyError", node)
    assert res.problem == "Unresolved Variable Reference"
    assert res.auto_fix.get("fallback_expression") == "{{$now}}"
