import pytest
from app.services.ai_email_reader import ai_email_reader, AIEmailReader
from app.agents.planner.planner_v4 import intelligent_planner_v4


def test_ai_email_reader_parse_query_intents():
    reader = AIEmailReader()

    unread = reader.parse_query_intent("Read my unread emails")
    assert unread["query"] == "is:unread"
    assert unread["max_results"] == 10

    latest = reader.parse_query_intent("Read latest email")
    assert latest["query"] == "is:unread"
    assert latest["max_results"] == 1

    last5 = reader.parse_query_intent("Read last 5 emails")
    assert last5["max_results"] == 5

    important = reader.parse_query_intent("Show important emails")
    assert important["query"] == "is:important"

    starred = reader.parse_query_intent("Show starred emails")
    assert starred["query"] == "is:starred"

    search = reader.parse_query_intent("Search emails from github")
    assert "github" in search["query"].lower()


def test_ai_email_reader_summarize_messages():
    reader = AIEmailReader()
    mock_messages = [
        {
            "id": "msg_001",
            "snippet": "Your monthly cloud invoice is ready for review.",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Monthly Billing Invoice"},
                    {"name": "From", "value": "billing@cloudcorp.com"},
                ]
            },
        },
        {
            "id": "msg_002",
            "snippet": "CRITICAL: Security patch required immediately.",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "URGENT Security Advisory"},
                    {"name": "From", "value": "security@corp.com"},
                ]
            },
        },
    ]

    summaries = reader.summarize_messages(mock_messages)
    assert len(summaries) == 2
    assert summaries[0]["id"] == "msg_001"
    assert summaries[0]["subject"] == "Monthly Billing Invoice"
    assert summaries[1]["priority"] == "HIGH"


def test_planner_email_reading_workflow_dag():
    prompts_and_expected = [
        ("Read my unread emails", "is:unread", 10),
        ("Read latest email", "is:unread", 1),
        ("Read last 5 emails", "is:unread", 5),
        ("Show important emails", "is:important", 10),
        ("Show starred emails", "is:starred", 10),
    ]

    for prompt, expected_q, expected_max in prompts_and_expected:
        plan = intelligent_planner_v4.plan(prompt)
        nodes = [n for n in plan.workflow_graph["nodes"] if n.get("provider") in ["gmail", "google_gmail"]]
        assert len(nodes) > 0
        params = nodes[0]["parameters"]
        assert params.get("q") == expected_q, f"For '{prompt}', expected q='{expected_q}', got '{params.get('q')}'"
        assert params.get("max_results") == expected_max, f"For '{prompt}', expected max={expected_max}, got '{params.get('max_results')}'"
