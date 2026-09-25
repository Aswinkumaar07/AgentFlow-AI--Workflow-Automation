import pytest
from app.services.gmail_search_query_translator import gmail_search_query_translator, GmailSearchQueryTranslator
from app.agents.planner.planner_v4 import intelligent_planner_v4


def test_gmail_search_query_translation_examples():
    translator = GmailSearchQueryTranslator()

    res_amazon = translator.translate_to_gmail_query("Find emails from Amazon.")
    assert res_amazon["query"] == "from:Amazon"

    res_invoices = translator.translate_to_gmail_query("Find invoices.")
    assert res_invoices["query"] == "invoice"

    res_interviews = translator.translate_to_gmail_query("Find interview emails.")
    assert res_interviews["query"] == "interview"

    res_week = translator.translate_to_gmail_query("Find emails this week.")
    assert res_week["query"] == "newer_than:7d"

    res_unread = translator.translate_to_gmail_query("Find unread emails.")
    assert res_unread["query"] == "is:unread"

    res_att = translator.translate_to_gmail_query("Find attachments.")
    assert res_att["query"] == "has:attachment"


def test_planner_gmail_search_prompts():
    prompts_expected = [
        ("Find emails from Amazon.", "from:Amazon"),
        ("Find invoices.", "invoice"),
        ("Find interview emails.", "interview"),
        ("Find emails this week.", "newer_than:7d"),
        ("Find unread emails.", "is:unread"),
        ("Find attachments.", "has:attachment"),
    ]

    for prompt, expected_q in prompts_expected:
        plan = intelligent_planner_v4.plan(prompt)
        nodes = [n for n in plan.workflow_graph["nodes"] if n.get("provider") in ["gmail", "google_gmail"]]
        assert len(nodes) > 0, f"No Gmail node created for prompt: {prompt}"
        op_id = nodes[0].get("operation") or nodes[0].get("operation_id")
        assert op_id in ["gmail.messages.search", "gmail.messages.list"], f"For '{prompt}', expected search/list operation, got '{op_id}'"
        assert nodes[0]["parameters"]["q"] == expected_q, f"For '{prompt}', expected q='{expected_q}', got '{nodes[0]['parameters']['q']}'"
