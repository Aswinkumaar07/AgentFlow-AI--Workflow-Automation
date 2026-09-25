import pytest
from app.agents.autonomous_agent import autonomous_agent_ai_service, AutonomousExecutionResult, ActionStep


def test_autonomous_agent_refund_goal_execution():
    goal = "Handle customer refunds automatically"
    res = autonomous_agent_ai_service.execute_goal(goal)

    assert isinstance(res, AutonomousExecutionResult)
    assert res.overall_confidence > 0.8
    assert len(res.action_trace) >= 4
    assert len(res.audit_logs) >= 5
    assert "jane@acme.com" in res.outcome_summary

    # Action trace providers should span Gmail, Hubspot, Stripe, Slack
    providers = [s.provider for s in res.action_trace]
    assert "Gmail" in providers
    assert "Stripe" in providers


def test_autonomous_agent_human_approval_guard():
    goal = "Handle customer refunds automatically"
    context = {"amount": 750.0}  # Exceeds $500 monetary threshold
    res = autonomous_agent_ai_service.execute_goal(goal, context)

    assert res.human_approval_required is True
    assert res.approval_prompt is not None

    pending_steps = [s for s in res.action_trace if s.approval_status == "pending"]
    assert len(pending_steps) >= 1


def test_autonomous_agent_rollback_execution():
    goal = "Handle customer refunds automatically"
    res = autonomous_agent_ai_service.execute_goal(goal)

    # Rollback execution
    rolled_back = autonomous_agent_ai_service.rollback(res)
    assert rolled_back.can_rollback is False
    assert "Rollback complete" in rolled_back.outcome_summary

    rolled_back_steps = [s for s in rolled_back.action_trace if s.status == "rolled_back"]
    assert len(rolled_back_steps) >= 1
