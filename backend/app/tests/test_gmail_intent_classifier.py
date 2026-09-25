import pytest
from app.agents.gmail_intent_classifier import gmail_intent_classifier, GmailIntent, INTENT_OPERATION_MAP
from app.agents.planner.planner_v4 import intelligent_planner_v4


def test_all_16_intents_classification():
    prompts_and_intents = [
        ("Send an email to john@example.com", GmailIntent.EMAIL_SEND, "gmail.messages.send"),
        ("Write an apology email to client", GmailIntent.EMAIL_GENERATE, "gmail.messages.send"),
        ("Read my email details", GmailIntent.EMAIL_READ, "gmail.messages.get"),
        ("Read my latest email", GmailIntent.EMAIL_READ_LATEST, "gmail.messages.list"),
        ("Read my unread emails", GmailIntent.EMAIL_READ_UNREAD, "gmail.messages.list"),
        ("Find invoices in my inbox", GmailIntent.EMAIL_SEARCH, "gmail.messages.search"),
        ("Find emails from:john@example.com", GmailIntent.EMAIL_SEARCH_BY_SENDER, "gmail.messages.search"),
        ("Search subject:Meeting", GmailIntent.EMAIL_SEARCH_BY_SUBJECT, "gmail.messages.search"),
        ("Reply to message msg_123", GmailIntent.EMAIL_REPLY, "gmail.messages.reply"),
        ("Forward email to team@company.com", GmailIntent.EMAIL_FORWARD, "gmail.messages.forward"),
        ("Delete email msg_123", GmailIntent.EMAIL_DELETE, "gmail.messages.delete"),
        ("Mark as read msg_123", GmailIntent.EMAIL_MARK_READ, "gmail.messages.mark_read"),
        ("Mark as unread msg_123", GmailIntent.EMAIL_MARK_UNREAD, "gmail.messages.mark_unread"),
        ("Summarize my inbox messages", GmailIntent.EMAIL_SUMMARIZE, "gmail.messages.list"),
        ("Create draft for project update", GmailIntent.EMAIL_DRAFT, "gmail.drafts.create"),
        ("Tomorrow 9 AM send email reminder", GmailIntent.EMAIL_SCHEDULE, "scheduler.create_job"),
    ]

    for prompt, expected_intent, expected_op in prompts_and_intents:
        res = gmail_intent_classifier.classify(prompt)
        assert res.intent == expected_intent, f"For '{prompt}', expected intent {expected_intent}, got {res.intent}"
        assert res.confidence >= 0.90, f"For '{prompt}', expected confidence >= 0.90, got {res.confidence}"
        assert res.target_operation == expected_op, f"For '{prompt}', expected operation {expected_op}, got {res.target_operation}"


def test_planner_intent_classification_integration():
    # Example 1: "Read my latest email" -> gmail.messages.get (NOT gmail.messages.send)
    plan_read = intelligent_planner_v4.plan("Read my latest email")
    nodes_read = [n for n in plan_read.workflow_graph["nodes"] if n.get("provider") in ["gmail", "google_gmail"]]
    assert len(nodes_read) > 0
    assert nodes_read[0]["operation"] in ["gmail.messages.get", "gmail.messages.list"]
    assert nodes_read[0]["operation"] != "gmail.messages.send"
    assert any("Stage 3.5 [Intelligent Intent Classification]" in trace for trace in plan_read.reasoning_trace)

    # Example 2: "Summarize my unread emails" -> gmail.messages.list (followed by summary)
    plan_sum = intelligent_planner_v4.plan("Summarize my unread emails")
    nodes_sum = [n for n in plan_sum.workflow_graph["nodes"] if n.get("provider") in ["gmail", "google_gmail"]]
    assert len(nodes_sum) > 0
    assert nodes_sum[0]["operation"] == "gmail.messages.list"

    # Example 3: "Send an email" -> gmail.messages.send
    plan_send = intelligent_planner_v4.plan("Send an email to john@example.com")
    nodes_send = [n for n in plan_send.workflow_graph["nodes"] if n.get("provider") in ["gmail", "google_gmail"]]
    assert len(nodes_send) > 0
    assert nodes_send[0]["operation"] == "gmail.messages.send"
