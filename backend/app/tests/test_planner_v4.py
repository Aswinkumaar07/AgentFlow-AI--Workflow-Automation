import pytest
from app.agents.planner.planner_v4 import intelligent_planner_v4


def test_planner_v5_good_morning_email_reasoning():
    prompt = "Send good morning email to john@example.com"
    plan = intelligent_planner_v4.plan(prompt)

    assert plan.workflow_graph["trigger"]["type"] == "Manual"
    assert "Gmail" in plan.selected_connectors
    gmail_node = next(n for n in plan.workflow_graph["nodes"] if n["provider"].lower() == "gmail")

    assert gmail_node["parameters"]["to"] == "john@example.com"
    assert gmail_node["parameters"]["subject"] == "Good Morning ☀️"
    assert "Good Morning" in gmail_node["parameters"]["subject"]
    assert "Good Morning" in gmail_node["parameters"]["body"]
    assert any("Semantic Email Inference" in trace for trace in plan.reasoning_trace)


def test_planner_v5_good_night_email_reasoning():
    prompt = "Send good night email to alice@example.com"
    plan = intelligent_planner_v4.plan(prompt)

    assert "Gmail" in plan.selected_connectors
    gmail_node = next(n for n in plan.workflow_graph["nodes"] if n["provider"].lower() == "gmail")

    assert gmail_node["parameters"]["to"] == "alice@example.com"
    assert gmail_node["parameters"]["subject"] == "Good Night 🌙"
    assert "Good Night" in gmail_node["parameters"]["body"]
    assert "Sleep well." in gmail_node["parameters"]["body"]
    assert any("Good Night 🌙" in trace for trace in plan.reasoning_trace)


def test_planner_v5_happy_birthday_john_reasoning():
    prompt = "Wish John happy birthday"
    plan = intelligent_planner_v4.plan(prompt)

    assert "Gmail" in plan.selected_connectors
    gmail_node = next(n for n in plan.workflow_graph["nodes"] if n["provider"].lower() == "gmail")

    assert gmail_node["parameters"]["subject"] == "Happy Birthday John 🎉"
    assert "Happy Birthday John!" in gmail_node["parameters"]["body"]
    assert "Have an amazing day." in gmail_node["parameters"]["body"]
    assert any("Happy Birthday John 🎉" in trace for trace in plan.reasoning_trace)


def test_planner_v4_schedule_report_pure_reasoning():
    prompt = "Every Monday at 8AM send report from Employees sheet"
    plan = intelligent_planner_v4.plan(prompt)

    assert plan.workflow_graph["trigger"]["type"] == "Schedule"
    nodes = plan.workflow_graph["nodes"]
    # AI-8: Schedule trigger produces 3-node DAG: Schedule -> Generate -> Send
    assert len(nodes) >= 2, f"Expected >=2 nodes, got {len(nodes)}: {[n.get('provider') for n in nodes]}"
    providers = [n["provider"].lower() for n in nodes]
    assert "gmail" in providers or any("gmail" in p for p in providers), \
        f"Expected Gmail node in providers: {providers}"


def test_planner_v4_github_slack_notion_pure_reasoning():
    prompt = "When GitHub PR opens notify Slack #engineering and create Notion page"
    plan = intelligent_planner_v4.plan(prompt)

    assert plan.workflow_graph["trigger"]["type"] == "GitHub"
    assert plan.workflow_graph["trigger"]["event"] == "pull_request.opened"
    assert "Slack" in plan.selected_connectors
    assert "Notion" in plan.selected_connectors
    nodes = plan.workflow_graph["nodes"]
    assert len(nodes) == 2
    slack_node = next(n for n in nodes if n["provider"].lower() == "slack")
    assert slack_node["parameters"]["channel"] == "#engineering"
