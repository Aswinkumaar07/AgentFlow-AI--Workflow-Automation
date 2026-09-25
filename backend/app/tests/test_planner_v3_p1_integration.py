import pytest
from app.agents.planner.planner_v3 import intelligent_planner_v3, PlanningResult


def test_p1_prompt_1_send_good_morning_email():
    prompt = "Send good morning email"
    res = intelligent_planner_v3.plan(prompt)

    assert isinstance(res, PlanningResult)
    assert "Gmail" in res.selected_connectors
    graph = res.workflow_graph
    assert graph["trigger"]["type"] == "Manual"
    assert len(graph["nodes"]) == 1
    assert graph["nodes"][0]["provider"] == "Gmail"


def test_p1_prompt_2_every_weekday_at_8am_send_good_morning_email():
    prompt = "Every weekday at 8AM send good morning email"
    res = intelligent_planner_v3.plan(prompt)

    graph = res.workflow_graph
    assert graph["trigger"]["type"] == "Schedule"
    assert graph["trigger"]["cron"] == "0 8 * * 1-5"
    assert "Gmail" in res.selected_connectors
    assert len(graph["nodes"]) == 1


def test_p1_prompt_3_notify_slack_when_github_pr_opens():
    prompt = "Notify Slack when GitHub PR opens"
    res = intelligent_planner_v3.plan(prompt)

    graph = res.workflow_graph
    assert graph["trigger"]["type"] == "GitHub"
    assert graph["trigger"]["event"] == "pull_request.opened"
    assert "GitHub" in res.selected_connectors
    assert "Slack" in res.selected_connectors
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1


def test_p1_prompt_4_upload_gmail_invoices_to_drive():
    prompt = "Upload Gmail invoices to Drive"
    res = intelligent_planner_v3.plan(prompt)

    graph = res.workflow_graph
    assert graph["trigger"]["type"] == "Gmail"
    assert graph["trigger"]["query"] == "label:invoices"
    assert len(graph["nodes"]) == 4
    assert len(graph["edges"]) == 3
    providers = [n["provider"] for n in graph["nodes"]]
    assert providers == ["Gmail", "Loop", "Condition", "Google Drive"]


def test_p1_prompt_5_backup_google_drive_every_night():
    prompt = "Backup Google Drive every night"
    res = intelligent_planner_v3.plan(prompt)

    graph = res.workflow_graph
    assert graph["trigger"]["type"] == "Schedule"
    assert graph["trigger"]["cron"] == "0 0 * * *"
    assert "Google Drive" in res.selected_connectors
    assert len(graph["nodes"]) == 2


def test_p1_prompt_6_webhook_ai_email():
    prompt = "Webhook -> AI -> Email"
    res = intelligent_planner_v3.plan(prompt)

    graph = res.workflow_graph
    assert graph["trigger"]["type"] == "Webhook"
    assert len(graph["nodes"]) == 2
    assert graph["nodes"][0]["provider"] == "AI"
    assert graph["nodes"][1]["provider"] == "Gmail"


def test_p1_prompt_7_google_sheets_employees_loop_gmail():
    prompt = "Google Sheets employees -> Loop -> Gmail"
    res = intelligent_planner_v3.plan(prompt)

    graph = res.workflow_graph
    assert len(graph["nodes"]) == 4
    providers = [n["provider"] for n in graph["nodes"]]
    assert providers == ["Google Sheets", "Loop", "Gmail", "Merge"]


def test_p1_prompt_8_stripe_payment_slack():
    prompt = "Stripe payment -> Slack"
    res = intelligent_planner_v3.plan(prompt)

    graph = res.workflow_graph
    assert graph["trigger"]["type"] == "Stripe"
    assert "Stripe" in res.selected_connectors
    assert "Slack" in res.selected_connectors
    assert len(graph["nodes"]) == 2


def test_p1_prompt_9_github_issue_notion():
    prompt = "GitHub Issue -> Notion"
    res = intelligent_planner_v3.plan(prompt)

    graph = res.workflow_graph
    assert graph["trigger"]["type"] == "GitHub"
    assert graph["trigger"]["event"] == "issues.opened"
    assert "GitHub" in res.selected_connectors
    assert "Notion" in res.selected_connectors
    assert len(graph["nodes"]) == 2


def test_p1_prompt_10_summarize_unread_gmail_using_ai():
    prompt = "Summarize unread Gmail using AI"
    res = intelligent_planner_v3.plan(prompt)

    graph = res.workflow_graph
    assert graph["trigger"]["type"] == "Gmail"
    assert graph["trigger"]["query"] == "is:unread"
    assert len(graph["nodes"]) == 2
    assert graph["nodes"][0]["provider"] == "Gmail"
    assert graph["nodes"][1]["provider"] == "AI"


def test_p1_all_dags_are_unique():
    prompts = [
        "Send good morning email",
        "Every weekday at 8AM send good morning email",
        "Notify Slack when GitHub PR opens",
        "Upload Gmail invoices to Drive",
        "Backup Google Drive every night",
        "Webhook -> AI -> Email",
        "Google Sheets employees -> Loop -> Gmail",
        "Stripe payment -> Slack",
        "GitHub Issue -> Notion",
        "Summarize unread Gmail using AI",
    ]

    generated_dags = []
    for p in prompts:
        res = intelligent_planner_v3.plan(p)
        graph = res.workflow_graph
        dag_signature = (
            graph["trigger"].get("type"),
            graph["trigger"].get("cron"),
            tuple([n["provider"] for n in graph["nodes"]]),
            tuple([(e["source"], e["target"]) for e in graph["edges"]]),
        )
        generated_dags.append(dag_signature)

    # Verify every prompt generated a unique DAG signature
    assert len(generated_dags) == len(set(generated_dags))
