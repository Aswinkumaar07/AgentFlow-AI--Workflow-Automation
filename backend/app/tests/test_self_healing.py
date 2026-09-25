import pytest
from app.agents.self_healing import self_healing_engine, self_healing_ai_service, SelfHealingDiagnostic


def test_self_healing_429_rate_limit_fix():
    graph = {
        "title": "Slack Notification Pipeline",
        "nodes": [
            {
                "id": "step_1",
                "label": "Post Slack Message",
                "provider": "Slack",
                "operation_id": "slack.chat.postMessage",
            }
        ],
    }
    node = graph["nodes"][0]

    diag = self_healing_ai_service.diagnose("HTTP 429 Rate limit exceeded", node, graph)
    assert isinstance(diag, SelfHealingDiagnostic)
    assert diag.problem == "Rate Limit Exceeded (HTTP 429)"
    assert "retry_policy" in diag.proposed_fix_patch

    repaired = self_healing_ai_service.apply_fix("HTTP 429 Rate limit exceeded", node, graph)
    assert repaired.get("is_repaired") is True
    assert "retry_policy" in repaired["nodes"][0]["parameters"]


def test_self_healing_oauth_expired_fix():
    graph = {
        "nodes": [{"id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.send"}]
    }
    node = graph["nodes"][0]

    repaired = self_healing_engine.apply_one_click_fix("401 Unauthorized token expired", node, graph)
    assert repaired["nodes"][0]["parameters"]["auth_status"] == "active"
    assert repaired["nodes"][0]["parameters"]["auth_refreshed"] is True


def test_self_healing_endpoint_changed_fix():
    graph = {
        "nodes": [{"id": "step_1", "provider": "GitHub", "operation_id": "github.pulls.old_endpoint"}]
    }
    node = graph["nodes"][0]

    repaired = self_healing_engine.apply_one_click_fix("HTTP 404 Endpoint deprecated", node, graph)
    assert "v2.endpoint" in repaired["nodes"][0]["operation_id"]
    assert repaired["nodes"][0]["parameters"]["endpoint_updated"] is True
