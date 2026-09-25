import pytest
from app.agents.planner.planner_v3 import intelligent_planner_v3, PlanningResult


def test_planner_v3_send_email_intent():
    res = intelligent_planner_v3.plan("Send good morning email")
    assert isinstance(res, PlanningResult)
    assert res.intent == "SEND_EMAIL"
    assert "Gmail" in res.selected_connectors
    assert "gmail.messages.send" in res.selected_operations
    assert "recipient_email" in res.missing_inputs
    assert len(res.reasoning_trace) >= 9


test_planner_v3_send_email_intent()


def test_planner_v3_entity_extraction_and_schedule():
    res = intelligent_planner_v3.plan("Every Monday send weekly report to john@example.com in #engineering")
    assert res.intent == "SCHEDULE_TRIGGER"
    assert res.entities.get("emails") == ["john@example.com"]
    assert res.entities.get("channel") == "#engineering"
    assert res.entities.get("schedule_cron") == "0 9 * * 1"
    assert "Schedule" in res.selected_connectors
    assert "Slack" in res.selected_connectors
    assert "{{$now}}" in res.variables


def test_planner_v3_github_pr_event():
    res = intelligent_planner_v3.plan("Notify Slack when GitHub PR opens for repo: AgentFlow-AI/TERRAWATCH")
    assert res.intent == "GITHUB_EVENT"
    assert res.entities.get("github_repo") == "AgentFlow-AI/TERRAWATCH"
    assert "GitHub" in res.selected_connectors
    assert "Slack" in res.selected_connectors
    assert len(res.workflow_graph.get("nodes", [])) == 2


def test_planner_v3_sheets_loop_merge():
    res = intelligent_planner_v3.plan("Read employees from Google Sheets, loop over rows, and email each employee")
    assert res.intent == "SHEETS_OPERATIONS"
    assert "Google Sheets" in res.selected_connectors
    assert "Loop" in res.selected_connectors
    assert "Gmail" in res.selected_connectors
    assert "Merge" in res.selected_connectors
    assert len(res.workflow_graph.get("nodes", [])) == 4


def test_planner_v3_webhook_ai_gmail():
    res = intelligent_planner_v3.plan("Webhook -> AI summarize text -> Email customer")
    assert res.intent == "WEBHOOK_TRIGGER"
    assert "Webhook" in res.selected_connectors
    assert "AI" in res.selected_connectors
    assert "Gmail" in res.selected_connectors
    assert "{{trigger_payload.body}}" in res.variables


def test_planner_v3_gmail_invoice_condition_drive():
    res = intelligent_planner_v3.plan("Whenever invoice arrives in Gmail, loop attachments, check if PDF, upload to Drive")
    assert res.intent == "READ_EMAIL"
    assert "Gmail" in res.selected_connectors
    assert "Loop" in res.selected_connectors
    assert "Condition" in res.selected_connectors
    assert "Google Drive" in res.selected_connectors
    assert len(res.workflow_graph.get("edges", [])) == 3
