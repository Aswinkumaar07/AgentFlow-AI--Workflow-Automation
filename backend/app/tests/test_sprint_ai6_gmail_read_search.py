import pytest
from app.services.gmail_search_query_translator import gmail_search_query_translator
from app.agents.planner.planner_v4 import intelligent_planner_v4
from app.connectors.providers.gmail.adapter import GmailAdapter


def test_gmail_query_translation():
    # 1. Read latest email
    q1 = gmail_search_query_translator.translate_to_gmail_query("Read latest email")
    assert q1["max_results"] == 1

    # 2. Read unread emails
    q2 = gmail_search_query_translator.translate_to_gmail_query("Read unread emails")
    assert q2["query"] == "is:unread"

    # 3. Search invoices
    q3 = gmail_search_query_translator.translate_to_gmail_query("Search invoices")
    assert "invoice" in q3["query"]

    # 4. Find Amazon emails
    q4 = gmail_search_query_translator.translate_to_gmail_query("Find Amazon emails")
    assert q4["query"].lower() == "from:amazon"

    # 5. Summarize emails
    q5 = gmail_search_query_translator.translate_to_gmail_query("Summarize emails")
    assert q5["query"] == "is:unread"


def test_planner_detects_gmail_read_operations():
    # Read latest email
    plan1 = intelligent_planner_v4.plan("Read latest email")
    nodes1 = plan1.workflow_graph["nodes"]
    assert any(n["operation"] in ["gmail.messages.get", "gmail.messages.list"] for n in nodes1)

    # Search invoices
    plan2 = intelligent_planner_v4.plan("Search invoices")
    nodes2 = plan2.workflow_graph["nodes"]
    assert any(n["operation"] in ["gmail.messages.search", "gmail.messages.list"] for n in nodes2)

    # Find Amazon emails
    plan3 = intelligent_planner_v4.plan("Find Amazon emails")
    nodes3 = plan3.workflow_graph["nodes"]
    assert any(n["operation"] in ["gmail.messages.search", "gmail.messages.list"] for n in nodes3)

    # Summarize emails
    plan4 = intelligent_planner_v4.plan("Summarize emails")
    nodes4 = plan4.workflow_graph["nodes"]
    assert any(n["operation"] in ["gmail.messages.list", "gmail.messages.get"] for n in nodes4)


def test_gmail_adapter_metadata_read_operations():
    adapter = GmailAdapter()
    meta = adapter.get_metadata()
    op_ids = meta.supported_operations

    assert "gmail.messages.list" in op_ids
    assert "gmail.messages.get" in op_ids
    assert "gmail.messages.search" in op_ids
