import pytest
import asyncio
import os
from app.agents.planner.planner_v4 import intelligent_planner_v4
from app.agents.task_decomposer.decomposer import EnterpriseTaskDecomposer
from app.agents.planner.gmail_search_query_builder import extract_gmail_result_count, build_gmail_search_query
from app.services.workflow_scheduler import workflow_scheduler_service
from app.agents.planner.deterministic_normalizer import deterministic_normalizer


# ==============================================================================
# CATEGORY A: SIMPLE TASKS (1-7)
# ==============================================================================

@pytest.mark.asyncio
async def test_simple_task_find_latest_email():
    plan = intelligent_planner_v4.plan("Find my latest email")
    nodes = plan.workflow_graph.get("nodes", [])
    assert len(nodes) >= 1
    assert any(n.get("provider") in ["gmail", "Google"] or n.get("operation") == "gmail.messages.list" for n in nodes)


@pytest.mark.asyncio
async def test_simple_task_summarize_latest_email():
    plan = intelligent_planner_v4.plan("Find my latest email and summarize it using AI")
    nodes = plan.workflow_graph.get("nodes", [])
    providers = [n.get("provider", "").lower() for n in nodes]
    assert any("gmail" in p or "google" in p for p in providers)
    assert any("ai" in p for p in providers)


@pytest.mark.asyncio
async def test_simple_task_send_email():
    plan = intelligent_planner_v4.plan("Send email to test@example.com with subject Hello and body World")
    nodes = plan.workflow_graph.get("nodes", [])
    send_nodes = [n for n in nodes if n.get("operation") in ["gmail.messages.send", "execute.action"]]
    assert len(send_nodes) >= 1
    params = send_nodes[0].get("parameters", {})
    assert params.get("to") == "test@example.com"


@pytest.mark.asyncio
async def test_simple_task_post_slack_message():
    plan = intelligent_planner_v4.plan("Post message Hello World to #all-agentflow-ai on Slack")
    nodes = plan.workflow_graph.get("nodes", [])
    slack_nodes = [n for n in nodes if n.get("provider", "").lower() in ["slack", "slack_oauth"]]
    assert len(slack_nodes) >= 1
    assert slack_nodes[0]["parameters"]["channel"] == "#all-agentflow-ai"


@pytest.mark.asyncio
async def test_simple_task_search_unread_emails():
    plan = intelligent_planner_v4.plan("Show me my unread emails")
    nodes = plan.workflow_graph.get("nodes", [])
    assert len(nodes) >= 1
    gmail_list = next(n for n in nodes if n.get("operation") == "gmail.messages.list")
    assert "is:unread" in gmail_list["parameters"].get("q", "")


@pytest.mark.asyncio
async def test_simple_task_read_specific_subject():
    plan = intelligent_planner_v4.plan("Find email with subject Monthly Report")
    nodes = plan.workflow_graph.get("nodes", [])
    assert len(nodes) >= 1
    gmail_list = next((n for n in nodes if n.get("operation") in ["gmail.messages.list", "gmail.messages.search"]), None)
    assert gmail_list is not None


@pytest.mark.asyncio
async def test_simple_task_post_slack_explicit_channel():
    plan = intelligent_planner_v4.plan("Send update to #engineering-alerts channel")
    nodes = plan.workflow_graph.get("nodes", [])
    slack_node = next((n for n in nodes if "slack" in n.get("provider", "").lower()), None)
    assert slack_node is not None
    assert slack_node["parameters"]["channel"] == "#engineering-alerts"


# ==============================================================================
# CATEGORY B: MULTI-STEP & MULTI-SERVICE (8-13)
# ==============================================================================

@pytest.mark.asyncio
async def test_multi_step_email_summarize_send():
    plan = intelligent_planner_v4.plan("Find invoice emails, summarize using AI, and send a summary email to finance@example.com")
    nodes = plan.workflow_graph.get("nodes", [])
    ops = [n.get("operation") or n.get("operation_id") for n in nodes]
    assert "gmail.messages.list" in ops or "gmail.messages.search" in ops
    assert "ai.summarize" in ops
    assert "gmail.messages.send" in ops

    send_node = next(n for n in nodes if n.get("operation") == "gmail.messages.send")
    assert send_node["parameters"]["to"] == "finance@example.com"


@pytest.mark.asyncio
async def test_multi_service_gmail_ai_slack():
    plan = intelligent_planner_v4.plan("Find my latest email, summarize it using AI, and send the summary to #all-agentflow-ai on Slack")
    nodes = plan.workflow_graph.get("nodes", [])
    providers = [n.get("provider", "").lower() for n in nodes]
    assert any("gmail" in p or "google" in p for p in providers)
    assert any("ai" in p for p in providers)
    assert any("slack" in p for p in providers)

    slack_node = next(n for n in nodes if "slack" in n.get("provider", "").lower())
    assert slack_node["parameters"]["channel"] == "#all-agentflow-ai"


@pytest.mark.asyncio
async def test_multi_service_gmail_attachment_drive():
    plan = intelligent_planner_v4.plan("Find latest email with attachment download pdf file and upload to google drive")
    nodes = plan.workflow_graph.get("nodes", [])
    providers = [n.get("provider", "").lower() for n in nodes]
    assert any("gmail" in p or "google" in p for p in providers)
    assert any("drive" in p for p in providers)


@pytest.mark.asyncio
async def test_multi_service_gmail_approval_slack():
    plan = intelligent_planner_v4.plan("Find invoice emails, summarize using AI, wait for my approval, then post summary to #all-agentflow-ai")
    nodes = plan.workflow_graph.get("nodes", [])
    ops = [n.get("operation") for n in nodes]
    assert "approval.wait" in ops or any(n.get("provider") == "human_approval" for n in nodes)


@pytest.mark.asyncio
async def test_multi_step_search_summarize_slack():
    plan = intelligent_planner_v4.plan("Search unread emails from manager, summarize using AI, post to #all-agentflow-ai")
    nodes = plan.workflow_graph.get("nodes", [])
    ops = [n.get("operation") for n in nodes]
    assert "gmail.messages.list" in ops or "gmail.messages.search" in ops
    assert "ai.summarize" in ops
    assert "slack.chat.postMessage" in ops


@pytest.mark.asyncio
async def test_multi_step_fetch_5_emails_summarize_send():
    plan = intelligent_planner_v4.plan("Fetch 5 emails, summarize using AI, send to team@example.com")
    nodes = plan.workflow_graph.get("nodes", [])
    list_node = next(n for n in nodes if n.get("operation") == "gmail.messages.list")
    assert list_node["parameters"]["max_results"] == 5


# ==============================================================================
# CATEGORY C: CONDITIONS & LOOPS (14-18)
# ==============================================================================

@pytest.mark.asyncio
async def test_condition_if_urgent_otherwise_do_nothing():
    plan = intelligent_planner_v4.plan("Check whether my latest email contains urgent. If it does, summarize it using AI and send to #all-agentflow-ai on Slack. Otherwise, do nothing.")
    nodes = plan.workflow_graph.get("nodes", [])
    cond_node = next((n for n in nodes if n.get("provider") == "condition"), None)
    assert cond_node is not None
    assert cond_node["parameters"]["right"] == "urgent"


@pytest.mark.asyncio
async def test_condition_if_invoice_send_fallback():
    plan = intelligent_planner_v4.plan("Check if email contains invoice. If so summarize and send to #all-agentflow-ai, otherwise send notice email to finance@example.com")
    nodes = plan.workflow_graph.get("nodes", [])
    cond_node = next((n for n in nodes if n.get("provider") == "condition"), None)
    assert cond_node is not None


@pytest.mark.asyncio
async def test_loop_summarize_each_email():
    plan = intelligent_planner_v4.plan("Find invoice emails from the last 30 days, summarize each using AI, and send a combined summary to #all-agentflow-ai")
    nodes = plan.workflow_graph.get("nodes", [])
    ops = [n.get("operation") or n.get("operation_id") for n in nodes]
    assert "loop.forEach" in ops or any(n.get("provider") == "loop" for n in nodes)


@pytest.mark.asyncio
async def test_loop_for_every_unread_email():
    plan = intelligent_planner_v4.plan("For every unread email summarize content using AI")
    nodes = plan.workflow_graph.get("nodes", [])
    ops = [n.get("operation") for n in nodes]
    assert "loop.forEach" in ops or any(n.get("provider") == "loop" for n in nodes)


@pytest.mark.asyncio
async def test_single_item_no_loop_generated():
    plan = intelligent_planner_v4.plan("Find my latest email and summarize it using AI")
    nodes = plan.workflow_graph.get("nodes", [])
    ops = [n.get("operation") for n in nodes]
    assert "loop.forEach" not in ops


# ==============================================================================
# CATEGORY D: SCHEDULING & TIME EXPRESSIONS (19-24)
# ==============================================================================

@pytest.mark.asyncio
async def test_schedule_one_shot_tomorrow_8am():
    prompt = "Send a good morning email to test@example.com tomorrow at 8 AM"
    assert workflow_scheduler_service.has_scheduling_intent(prompt) is True
    parsed = workflow_scheduler_service.parse_schedule_expression(prompt)
    assert parsed["schedule_type"] == "one_shot"
    assert "Tomorrow at 08:00 AM" in parsed["description"]


@pytest.mark.asyncio
async def test_schedule_recurring_every_1_minute():
    prompt = "Send my email summary every 1 minute"
    assert workflow_scheduler_service.has_scheduling_intent(prompt) is True
    parsed = workflow_scheduler_service.parse_schedule_expression(prompt)
    assert parsed["schedule_type"] == "interval"
    assert parsed["interval_seconds"] == 60


@pytest.mark.asyncio
async def test_schedule_recurring_every_monday_9am():
    prompt = "Summarize emails every Monday at 9 AM"
    assert workflow_scheduler_service.has_scheduling_intent(prompt) is True
    parsed = workflow_scheduler_service.parse_schedule_expression(prompt)
    assert parsed["schedule_type"] in ["cron", "recurring", "one_shot"]


@pytest.mark.asyncio
async def test_schedule_interval_5_minutes():
    prompt = "Check inbox every 5 minutes"
    assert workflow_scheduler_service.has_scheduling_intent(prompt) is True
    parsed = workflow_scheduler_service.parse_schedule_expression(prompt)
    assert parsed["interval_seconds"] == 300


@pytest.mark.asyncio
async def test_no_schedule_intent():
    prompt = "Find my latest email and summarize it once right now"
    assert workflow_scheduler_service.has_scheduling_intent(prompt) is False


@pytest.mark.asyncio
async def test_schedule_metadata_in_planning_result():
    plan = intelligent_planner_v4.plan("Send email to test@example.com tomorrow at 8 AM")
    assert plan.schedule_metadata is not None
    assert plan.schedule_metadata.get("schedule_type") == "one_shot"


# ==============================================================================
# CATEGORY E: NEGATIVE CONSTRAINTS & PROVIDER PROHIBITIONS (25-28)
# ==============================================================================

@pytest.mark.asyncio
async def test_negative_constraint_do_not_send_slack():
    plan = intelligent_planner_v4.plan("Summarize my latest email, but do not send anything to Slack")
    nodes = plan.workflow_graph.get("nodes", [])
    slack_nodes = [n for n in nodes if "slack" in n.get("provider", "").lower()]
    assert len(slack_nodes) == 0


@pytest.mark.asyncio
async def test_negative_constraint_dont_send_email():
    plan = intelligent_planner_v4.plan("Summarize my latest email and post on Slack, but don't send email")
    nodes = plan.workflow_graph.get("nodes", [])
    email_send_nodes = [n for n in nodes if n.get("operation") == "gmail.messages.send"]
    assert len(email_send_nodes) == 0


@pytest.mark.asyncio
async def test_negative_constraint_do_not_upload_drive():
    plan = intelligent_planner_v4.plan("Find attachment in latest email, summarize, do not upload to google drive")
    nodes = plan.workflow_graph.get("nodes", [])
    drive_nodes = [n for n in nodes if "drive" in n.get("provider", "").lower()]
    assert len(drive_nodes) == 0


@pytest.mark.asyncio
async def test_negative_constraint_no_slack():
    plan = intelligent_planner_v4.plan("Check unread emails and draft summary, no slack notification")
    nodes = plan.workflow_graph.get("nodes", [])
    slack_nodes = [n for n in nodes if "slack" in n.get("provider", "").lower()]
    assert len(slack_nodes) == 0


# ==============================================================================
# CATEGORY F: PRECEDENCE & ENTITY EXTRACTION (29-35)
# ==============================================================================

@pytest.mark.asyncio
async def test_entity_extraction_result_count():
    assert extract_gmail_result_count("Summarize the first 5 emails") == 5
    assert extract_gmail_result_count("Find 15 emails") == 15
    assert extract_gmail_result_count("Find 100 emails") == 100


@pytest.mark.asyncio
async def test_entity_extraction_result_count_clamping():
    plan = intelligent_planner_v4.plan("List 100 emails and summarize")
    nodes = plan.workflow_graph.get("nodes", [])
    list_node = next(n for n in nodes if n.get("operation") == "gmail.messages.list")
    assert list_node["parameters"]["max_results"] == 50


@pytest.mark.asyncio
async def test_entity_extraction_slack_channel_precedence():
    plan = intelligent_planner_v4.plan("Summarize latest email and send to #custom-alerts channel on Slack")
    nodes = plan.workflow_graph.get("nodes", [])
    slack_node = next((n for n in nodes if "slack" in n.get("provider", "").lower()), None)
    assert slack_node is not None
    assert slack_node["parameters"]["channel"] == "#custom-alerts"


@pytest.mark.asyncio
async def test_entity_extraction_email_recipient():
    plan = intelligent_planner_v4.plan("Send email to finance@example.com with summary of latest report")
    nodes = plan.workflow_graph.get("nodes", [])
    send_node = next(n for n in nodes if n.get("operation") == "gmail.messages.send")
    assert send_node["parameters"]["to"] == "finance@example.com"


@pytest.mark.asyncio
async def test_entity_extraction_search_query_no_count_leakage():
    q = build_gmail_search_query("Find top 5 invoice emails")
    assert "5" not in q
    assert "invoice" in q


@pytest.mark.asyncio
async def test_precedence_explicit_channel_over_default():
    channel = deterministic_normalizer.extract_slack_channel("Post summary to #all-agentflow-ai")
    assert channel == "#all-agentflow-ai"


@pytest.mark.asyncio
async def test_precedence_explicit_recipient_over_default():
    plan = intelligent_planner_v4.plan("Send apology email to sarah@example.com")
    nodes = plan.workflow_graph.get("nodes", [])
    send_node = next(n for n in nodes if n.get("operation") == "gmail.messages.send")
    assert send_node["parameters"]["to"] == "sarah@example.com"
