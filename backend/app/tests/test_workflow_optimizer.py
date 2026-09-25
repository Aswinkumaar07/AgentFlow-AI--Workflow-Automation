import pytest
from app.agents.optimizer import workflow_optimizer_engine, optimizer_ai_service, OptimizationAnalysisResult


def test_workflow_optimizer_analysis_and_auto_fix():
    graph = {
        "title": "Email and Loop Workflow",
        "nodes": [
            {
                "id": "step_1",
                "provider": "Google Sheets",
                "operation_id": "sheets.spreadsheets.values.get",
            },
            {
                "id": "step_2",
                "provider": "Loop",
                "operation_id": "loop.process",
            },
            {
                "id": "step_3",
                "provider": "Gmail",
                "operation_id": "gmail.messages.send",
            },
        ],
        "edges": [
            {"id": "e1-2", "source": "step_1", "target": "step_2"},
            {"id": "e2-3", "source": "step_2", "target": "step_3"},
        ],
    }

    res = optimizer_ai_service.analyze(graph)
    assert isinstance(res, OptimizationAnalysisResult)
    assert res.performance_score > 0
    assert res.optimization_score > 0
    assert "faster" in res.estimated_speedup
    assert "cost reduction" in res.estimated_savings
    assert len(res.suggestions) >= 3

    # Apply one-click optimization
    opt_graph = optimizer_ai_service.apply_optimization(graph)
    assert opt_graph.get("is_optimized") is True

    nodes = opt_graph.get("nodes", [])
    # Verify retry policy added for Gmail
    gmail_params = nodes[2]["parameters"]
    assert "retry_policy" in gmail_params
    assert gmail_params["retry_policy"]["max_retries"] == 3

    # Verify loop batching added
    loop_params = nodes[1]["parameters"]
    assert loop_params.get("enable_batching") is True
    assert loop_params.get("batch_size") == 25
