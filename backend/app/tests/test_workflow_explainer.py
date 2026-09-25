import pytest
from app.agents.explainer import workflow_explainer, explainer_ai_service, ExplanationResult


def test_workflow_explainer_analysis():
    graph = {
        "title": "Email Processing Pipeline",
        "intent": "READ_EMAIL",
        "trigger": {"type": "Gmail"},
        "nodes": [
            {
                "id": "step_1",
                "label": "Gmail List Invoices",
                "provider": "Gmail",
                "operation_id": "gmail.messages.list",
                "parameters": {"query": "label:invoices"},
            },
            {
                "id": "step_2",
                "label": "Loop Attachments",
                "provider": "Loop",
                "operation_id": "loop.process",
                "parameters": {"collection": "{{step_1.attachments}}"},
            },
            {
                "id": "step_3",
                "label": "Slack Post Alert",
                "provider": "Slack",
                "operation_id": "slack.chat.postMessage",
                "parameters": {"channel": "#finance", "text": "Invoice processed for {{$loop.item.name}}"},
            },
        ],
        "edges": [
            {"id": "e1-2", "source": "step_1", "target": "step_2"},
            {"id": "e2-3", "source": "step_2", "target": "step_3"},
        ],
    }

    res = explainer_ai_service.explain(graph)
    assert isinstance(res, ExplanationResult)
    assert "Email Processing Pipeline" in res.summary
    assert len(res.step_explanations) == 3
    assert res.estimated_runtime_ms > 0
    assert res.estimated_cost_usd > 0.0
    assert len(res.dependencies) == 2
    assert "Gmail" in res.connector_descriptions
    assert "Slack" in res.connector_descriptions
    assert "# 📖 Workflow Explanation Report" in res.markdown_report
