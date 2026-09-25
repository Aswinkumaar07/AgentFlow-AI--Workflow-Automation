import pytest
from app.agents.gmail_ai_agent import gmail_ai_agent, GmailAIAgent
from app.agents.planner.planner_v4 import intelligent_planner_v4


def test_gmail_ai_agent_all_prompts():
    prompts_to_test = [
        "Reply politely to the latest email",
        "Summarize inbox for today",
        "Delete spam messages in my account",
        "Archive newsletters automatically",
        "Forward invoices to accounting",
        "Send follow-up email to client",
        "Schedule reminders for upcoming tasks",
        "Draft emails for project discussion",
        "Generate newsletters for monthly subscribers",
        "Weekly digest of my inbox",
        "Monthly digest for executive summary",
        "Meeting preparation notes from calendar emails",
    ]

    for prompt in prompts_to_test:
        res = gmail_ai_agent.process_agent_request(prompt)

        assert "version" in res
        assert "agent_intent" in res
        assert len(res["selected_tools"]) > 0
        assert len(res["nodes"]) > 0
        assert len(res["reasoning_trace"]) > 0
        assert "LLM Reasoning Engine" in res["reasoning_trace"][0]


def test_planner_integration_for_autonomous_prompts():
    prompts_expected = [
        ("Reply politely", "autonomous_polite_reply", 4),
        ("Summarize inbox", "autonomous_inbox_summary", 2),
        ("Delete spam", "autonomous_spam_cleanup", 2),
        ("Archive newsletters", "autonomous_newsletter_archive", 2),
        ("Forward invoices", "autonomous_invoice_forwarding", 2),
        ("Send follow-up", "autonomous_followup_sender", 2),
        ("Schedule reminders", "autonomous_reminder_scheduler", 2),
        ("Draft emails", "autonomous_draft_creator", 1),
        ("Generate newsletters", "autonomous_newsletter_generator", 1),
        ("Weekly digest", "autonomous_weekly_digest", 2),
        ("Monthly digest", "autonomous_monthly_digest", 2),
        ("Meeting preparation", "autonomous_meeting_prep", 2),
    ]

    for prompt, expected_intent, expected_node_count in prompts_expected:
        plan = intelligent_planner_v4.plan(prompt)
        graph = plan.workflow_graph

        assert len(graph["nodes"]) == expected_node_count, f"For '{prompt}', expected {expected_node_count} nodes, got {len(graph['nodes'])}"
        assert any("LLM Reasoning Engine" in t for t in plan.reasoning_trace), f"For '{prompt}', expected reasoning trace in plan"
