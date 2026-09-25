import pytest
from app.agents.planner.planner_v2 import intelligent_planner_v2


def test_example1_send_good_morning_email():
    plan = intelligent_planner_v2.reason_and_plan("Send good morning email")
    assert plan.intent == "SEND_EMAIL"
    assert len(plan.nodes) == 1
    assert plan.nodes[0]["provider"] == "Gmail"
    assert plan.nodes[0]["operation_id"] == "gmail.messages.send"
    assert "Good Morning" in plan.nodes[0]["parameters"]["subject"]
    assert "recipient_email" in plan.missing_inputs


def test_example2_every_morning_send_good_morning_email():
    plan = intelligent_planner_v2.reason_and_plan("Every morning send good morning email")
    assert plan.trigger["type"] == "Schedule"
    assert plan.trigger["cron"] == "0 8 * * *"
    assert plan.nodes[0]["provider"] == "Gmail"


def test_example3_gmail_invoice_loop_drive():
    plan = intelligent_planner_v2.reason_and_plan("Whenever invoice arrives in Gmail upload PDF to Drive")
    assert plan.intent == "READ_EMAIL"
    assert len(plan.nodes) == 4
    providers = [n["provider"] for n in plan.nodes]
    assert providers == ["Gmail", "Loop", "Condition", "Google Drive"]
    assert len(plan.edges) == 3
    assert plan.edges[2]["sourceHandle"] == "true_branch"


def test_example4_github_pr_notify_slack():
    plan = intelligent_planner_v2.reason_and_plan("Notify Slack when GitHub PR opens")
    assert plan.intent == "GITHUB_EVENT"
    assert len(plan.nodes) == 2
    assert plan.nodes[0]["provider"] == "GitHub"
    assert plan.nodes[1]["provider"] == "Slack"


def test_example5_webhook_ai_summarize_email():
    plan = intelligent_planner_v2.reason_and_plan("Webhook AI summarize Email customer")
    assert plan.trigger["type"] == "Webhook"
    assert plan.nodes[0]["provider"] == "OpenAI/Gemini"
    assert plan.nodes[1]["provider"] == "Gmail"


def test_example6_sheets_loop_gmail_merge():
    plan = intelligent_planner_v2.reason_and_plan("Read rows from Google Sheets Loop Send email to each employee")
    assert plan.intent == "SHEETS_OPERATIONS"
    assert len(plan.nodes) == 4
    providers = [n["provider"] for n in plan.nodes]
    assert providers == ["Google Sheets", "Loop", "Gmail", "Merge"]
