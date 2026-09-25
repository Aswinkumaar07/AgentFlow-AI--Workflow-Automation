"""
Sprint AI-14: Real-World Agent Acceptance Testing & Execution Fix Suite

Verifies the complete AgentFlowPipeline end-to-end against realistic natural-language prompts.
Enforces the Gmail Intent -> Operation Matrix and Side-Effect Guard rules.

Structured Log Output Format for each acceptance test:
PROMPT
INTENT
TASKS
NODES
EDGES
OPERATIONS
PARAMETERS
VALIDATION
CAN_EXECUTE
"""

import pytest
from app.agents.pipeline import agentflow_pipeline, PipelineResult


def print_acceptance_details(prompt: str, result: PipelineResult):
    nodes = result.workflow_graph.get("nodes", [])
    edges = result.workflow_graph.get("edges", [])
    ops = [n.get("operation") or n.get("operation_id") for n in nodes]
    params = [n.get("parameters") for n in nodes]

    print("\n==================================================")
    print(f"PROMPT:     '{prompt}'")
    print(f"INTENT:     {result.intent}")
    print(f"TASKS:      {result.task_count}")
    print(f"NODES:      {result.node_count}")
    print(f"EDGES:      {result.edge_count}")
    print(f"OPERATIONS: {ops}")
    print(f"PARAMETERS: {params}")
    print(f"VALIDATION: errors={result.validation_errors} warnings={result.validation_warnings}")
    print(f"CAN_EXECUTE:{result.can_execute}")
    print("==================================================\n")


def assert_universal_send_rule(prompt: str, result: PipelineResult, explicit_send_requested: bool = False):
    """
    Universal Side-Effect Assertion Helper:
    If intent is not sending an email and user did not ask to send an email,
    gmail.messages.send MUST NOT appear in the workflow operations.
    """
    nodes = result.workflow_graph.get("nodes", [])
    ops = [n.get("operation") or n.get("operation_id") for n in nodes]
    send_intents = ["EMAIL_SEND", "EMAIL_GENERATE", "EMAIL_SCHEDULE", "SCHEDULED_EMAIL", "SLACK_SEND"]
    
    if result.intent not in send_intents and not explicit_send_requested:
        assert "gmail.messages.send" not in ops, (
            f"[AI-14 VIOLATION] Prompt: '{prompt}' | Intent: '{result.intent}' | "
            f"Operations MUST NOT contain gmail.messages.send, got '{ops}'"
        )
        assert "gmail.messages.reply" not in ops, (
            f"[AI-14 VIOLATION] Prompt: '{prompt}' | Intent: '{result.intent}' | "
            f"Operations MUST NOT contain gmail.messages.reply, got '{ops}'"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 10 MANDATORY REAL-WORLD ACCEPTANCE TESTS (SPRINT AI-14)
# ═══════════════════════════════════════════════════════════════════════════════

def test_01_send_email():
    """TEST 1: Send an email to test@example.com saying hello."""
    prompt = "Send an email to test@example.com saying hello."
    res = agentflow_pipeline.run(prompt)
    print_acceptance_details(prompt, res)

    nodes = res.workflow_graph.get("nodes", [])
    assert len(nodes) == 1
    assert nodes[0].get("operation") == "gmail.messages.send"
    params = nodes[0].get("parameters", {})
    assert params.get("to") == "test@example.com"
    assert res.can_execute is True


def test_02_read_latest_email_complete():
    """TEST 2: Read my latest Gmail email and show me the sender, subject, and complete message content."""
    prompt = "Read my latest Gmail email and show me the sender, subject, and complete message content. Do not send, reply, forward, delete, or modify any email."
    res = agentflow_pipeline.run(prompt)
    print_acceptance_details(prompt, res)

    nodes = res.workflow_graph.get("nodes", [])
    ops = [n.get("operation") for n in nodes]
    assert ops == ["gmail.messages.list", "gmail.messages.get"]
    assert "gmail.messages.send" not in ops
    assert "gmail.messages.reply" not in ops
    assert "gmail.messages.forward" not in ops
    assert "gmail.messages.delete" not in ops
    assert nodes[1].get("parameters", {}).get("message_id") == "{{step_1.messages[0].id}}"
    assert res.can_execute is True


def test_03_find_unread_emails_and_read():
    """TEST 3: Find my unread Gmail emails and display their sender, subject, date, and message content."""
    prompt = "Find my unread Gmail emails and display their sender, subject, date, and message content. Do not send or modify anything."
    res = agentflow_pipeline.run(prompt)
    print_acceptance_details(prompt, res)

    nodes = res.workflow_graph.get("nodes", [])
    ops = [n.get("operation") for n in nodes]
    assert ops == ["gmail.messages.list", "gmail.messages.get"]
    assert nodes[0].get("parameters", {}).get("q") == "is:unread"
    assert nodes[1].get("parameters", {}).get("message_id") == "{{step_1.messages[0].id}}"
    assert res.can_execute is True


def test_04_find_emails_from_john():
    """TEST 4: Find emails from john@example.com."""
    prompt = "Find emails from john@example.com"
    res = agentflow_pipeline.run(prompt)
    print_acceptance_details(prompt, res)

    nodes = res.workflow_graph.get("nodes", [])
    ops = [n.get("operation") for n in nodes]
    assert ops == ["gmail.messages.search"] or ops == ["gmail.messages.list"]
    assert "john@example.com" in str(nodes[0].get("parameters", {}).get("q", ""))
    assert len(nodes) == 1
    assert res.can_execute is True


def test_05_summarize_unread_emails():
    """TEST 5: Summarize my unread emails."""
    prompt = "Summarize my unread emails."
    res = agentflow_pipeline.run(prompt)
    print_acceptance_details(prompt, res)

    nodes = res.workflow_graph.get("nodes", [])
    ops = [n.get("operation") for n in nodes]
    assert ops == ["gmail.messages.list", "gmail.messages.get", "ai.summarize"]
    assert "gmail.messages.send" not in ops
    assert res.can_execute is True


def test_06_summarize_and_email():
    """TEST 6: Summarize my unread emails and email the summary to me."""
    prompt = "Summarize my unread emails and email the summary to me."
    res = agentflow_pipeline.run(prompt)
    print_acceptance_details(prompt, res)

    nodes = res.workflow_graph.get("nodes", [])
    ops = [n.get("operation") for n in nodes]
    assert ops == ["gmail.messages.list", "gmail.messages.get", "ai.summarize", "gmail.messages.send"]
    assert res.can_execute is True


def test_07_reply_to_latest_email():
    """TEST 7: Reply to my latest email saying I will attend."""
    prompt = "Reply to my latest email saying I will attend."
    res = agentflow_pipeline.run(prompt)
    print_acceptance_details(prompt, res)

    nodes = res.workflow_graph.get("nodes", [])
    ops = [n.get("operation") for n in nodes]
    assert ops == ["gmail.messages.list", "gmail.messages.get", "gmail.messages.reply"]
    assert res.can_execute is True


def test_08_draft_email():
    """TEST 8: Draft an email to John about tomorrow's meeting. Do not send it."""
    prompt = "Draft an email to John about tomorrow's meeting. Do not send it."
    res = agentflow_pipeline.run(prompt)
    print_acceptance_details(prompt, res)

    nodes = res.workflow_graph.get("nodes", [])
    ops = [n.get("operation") for n in nodes]
    assert ops == ["gmail.drafts.create"]
    assert "gmail.messages.send" not in ops
    assert res.can_execute is True


def test_09_scheduled_read_and_summarize():
    """TEST 9: Every morning at 9 AM read my latest email and summarize it."""
    prompt = "Every morning at 9 AM read my latest email and summarize it."
    res = agentflow_pipeline.run(prompt)
    print_acceptance_details(prompt, res)

    nodes = res.workflow_graph.get("nodes", [])
    ops = [n.get("operation") for n in nodes]
    assert ops[0] == "schedule.trigger"
    assert "ai.summarize" in ops
    assert res.can_execute is True


def test_10_scheduled_send_email():
    """TEST 10: Tomorrow at 9 AM send an email to john@example.com saying good morning."""
    prompt = "Tomorrow at 9 AM send an email to john@example.com saying good morning."
    res = agentflow_pipeline.run(prompt)
    print_acceptance_details(prompt, res)

    nodes = res.workflow_graph.get("nodes", [])
    ops = [n.get("operation") for n in nodes]
    assert ops[0] == "schedule.trigger"
    assert "gmail.messages.send" in ops
    assert res.can_execute is True


def test_frontend_contract_response_structure():
    """Verify AgentFlowPipeline.to_frontend_response() schema."""
    prompt = "Find emails from john@example.com"
    res = agentflow_pipeline.run(prompt)
    f_res = res.to_frontend_response()

    assert f_res["success"] is True
    assert "workflow" in f_res
    assert "intent" in f_res
    assert "validation" in f_res
    assert f_res["can_execute"] is True
