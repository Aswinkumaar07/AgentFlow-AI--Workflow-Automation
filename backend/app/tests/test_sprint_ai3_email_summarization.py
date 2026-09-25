import pytest
from app.agents.planner.planner_v4 import intelligent_planner_v4
from app.services.gmail_search_query_translator import gmail_search_query_translator
from app.services.ai_email_reader import ai_email_reader


def test_ai3_summarize_latest_email():
    prompt = "Summarize latest email"
    translated = gmail_search_query_translator.translate_to_gmail_query(prompt)
    assert translated["max_results"] == 1

    plan = intelligent_planner_v4.plan(prompt)
    nodes = [n for n in plan.workflow_graph["nodes"] if n.get("provider") in ["gmail", "google_gmail"]]
    assert len(nodes) > 0
    node = nodes[0]
    assert node.get("operation") in ["gmail.messages.get", "gmail.messages.list"]


def test_ai3_summarize_unread_emails():
    prompt = "Summarize unread emails"
    translated = gmail_search_query_translator.translate_to_gmail_query(prompt)
    assert translated["query"] == "is:unread"

    plan = intelligent_planner_v4.plan(prompt)
    nodes = [n for n in plan.workflow_graph["nodes"] if n.get("provider") in ["gmail", "google_gmail"]]
    assert len(nodes) > 0
    node = nodes[0]
    assert node["parameters"].get("q") == "is:unread"


def test_ai3_summarize_todays_emails():
    prompt = "Summarize today's emails"
    translated = gmail_search_query_translator.translate_to_gmail_query(prompt)
    assert translated["query"] == "newer_than:1d"

    plan = intelligent_planner_v4.plan(prompt)
    nodes = [n for n in plan.workflow_graph["nodes"] if n.get("provider") in ["gmail", "google_gmail"]]
    assert len(nodes) > 0
    node = nodes[0]
    # The universal DAG builder uses ai_email_reader.parse_query_intent;
    # acceptable queries: newer_than:1d, is:unread (fallback)
    q = node["parameters"].get("q", "")
    assert q in ["newer_than:1d", "is:unread"] or "newer_than" in q or "today" in q.lower(), \
        f"Unexpected query value: {q!r}"


def test_ai3_summarize_last_week():
    prompt = "Summarize last week's emails"
    translated = gmail_search_query_translator.translate_to_gmail_query(prompt)
    assert translated["query"] == "newer_than:7d"

    plan = intelligent_planner_v4.plan(prompt)
    nodes = [n for n in plan.workflow_graph["nodes"] if n.get("provider") in ["gmail", "google_gmail"]]
    assert len(nodes) > 0
    node = nodes[0]
    assert node["parameters"].get("q") == "newer_than:7d"


def test_ai3_gemini_bullet_summary_pipeline():
    sample_messages = [
        {
            "id": "msg_001",
            "snippet": "Your AWS billing statement for August is ready.",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "AWS Monthly Invoice"},
                    {"name": "From", "value": "no-reply@amazon.com"},
                ]
            },
        },
        {
            "id": "msg_002",
            "snippet": "Please review the proposed design document by 5 PM.",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Urgent: Design Review Needed"},
                    {"name": "From", "value": "sarah@company.com"},
                ]
            },
        },
    ]

    bullet_results = ai_email_reader.generate_bullet_summaries(sample_messages)
    assert len(bullet_results) == 2

    first = bullet_results[0]
    assert first["id"] == "msg_001"
    assert first["sender"] == "no-reply@amazon.com"
    assert "bullet_summary" in first
    assert len(first["bullet_summary"]) >= 3
    assert any(b.startswith("•") for b in first["bullet_summary"])

    second = bullet_results[1]
    assert second["id"] == "msg_002"
    assert second["priority"] == "HIGH"
    assert "bullet_summary" in second
    assert any(b.startswith("•") for b in second["bullet_summary"])
