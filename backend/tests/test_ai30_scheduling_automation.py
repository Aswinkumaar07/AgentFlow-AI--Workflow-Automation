import asyncio
import pytest
from app.services.workflow_scheduler import workflow_scheduler_service, ScheduledJobModel
from app.versions.manager import workflow_version_manager
from app.schemas.ai import AIGenerateRequest
from app.api.v1.ai import generate_workflow
from app.models.users import User


@pytest.fixture
def mock_user():
    u = User()
    u.id = "usr_ai30_test"
    u.email = "test@agentflow.ai"
    return u


def test_ai30_schedule_intent_detection():
    """Verify natural language schedule detection vs non-scheduling overrides (Items A & B)."""
    # Positive schedule intent prompts
    assert workflow_scheduler_service.has_scheduling_intent("Find my latest email, summarize it, and send to Slack every 1 minute") is True
    assert workflow_scheduler_service.has_scheduling_intent("Run this workflow every 30 minutes") is True
    assert workflow_scheduler_service.has_scheduling_intent("Check stock prices every day at 9 AM") is True
    assert workflow_scheduler_service.has_scheduling_intent("Send report tomorrow at 9 AM") is True
    assert workflow_scheduler_service.has_scheduling_intent("Sync github PRs every monday") is True
    assert workflow_scheduler_service.has_scheduling_intent("Run this every 5 minutes") is True
    assert workflow_scheduler_service.has_scheduling_intent("Schedule this workflow every Monday") is True
    assert workflow_scheduler_service.has_scheduling_intent("Run once in 2 minutes") is True
    assert workflow_scheduler_service.has_scheduling_intent("Run once 2 minutes from now") is True
    assert workflow_scheduler_service.has_scheduling_intent("Run this daily at 9 AM") is True

    # Negative / Non-scheduling prompts
    assert workflow_scheduler_service.has_scheduling_intent("Find my latest email and send to Slack") is False
    assert workflow_scheduler_service.has_scheduling_intent("Summarize this doc do this once") is False
    assert workflow_scheduler_service.has_scheduling_intent("Fetch user data do not schedule") is False
    assert workflow_scheduler_service.has_scheduling_intent("Run once: send email to manager") is False
    assert workflow_scheduler_service.has_scheduling_intent("Summarize report don't repeat") is False
    assert workflow_scheduler_service.has_scheduling_intent("Send a Slack message saying scheduled execution test") is False
    assert workflow_scheduler_service.has_scheduling_intent("Send an email with subject Schedule Update") is False
    assert workflow_scheduler_service.has_scheduling_intent("Post 'my scheduled report is ready' to Slack") is False
    assert workflow_scheduler_service.has_scheduling_intent("Create a workflow for scheduled notifications") is False


@pytest.mark.asyncio
async def test_ai30_auto_schedule_and_version_pinning_on_generate(mock_user):
    """Verify generate_workflow creates version snapshot and active schedule for schedule prompts (Items C, D, F)."""
    prompt = "Summarize latest 5 emails and post to Slack every 5 minutes"
    req = AIGenerateRequest(prompt=prompt)

    response_wrapper = await generate_workflow(req, current_user=mock_user)
    data = response_wrapper.get("data", {})

    assert data.get("is_valid") is True
    sched = data.get("schedule")
    assert sched is not None, "Schedule metadata must be returned in AIGenerateResponse for schedule prompts"
    assert sched.get("status") == "paused"
    assert sched.get("version_id") is not None
    assert sched.get("version_number") is not None

    job_id = sched.get("job_id")
    persisted_job = workflow_scheduler_service.get_job(job_id)
    assert persisted_job is not None
    assert persisted_job.status == "paused"
    assert persisted_job.version_id == sched.get("version_id")


@pytest.mark.asyncio
async def test_ai30_duplicate_schedule_prevention(mock_user):
    """Verify re-generating with scheduling intent updates existing schedule rather than duplicating (Item E)."""
    prompt1 = "Check emails and alert Slack every 10 minutes"
    req1 = AIGenerateRequest(prompt=prompt1)
    resp1 = await generate_workflow(req1, current_user=mock_user)
    sched1 = resp1.get("data", {}).get("schedule")
    job_id1 = sched1.get("job_id")

    # Second generate for same workflow
    prompt2 = "Check emails and alert Slack every 15 minutes"
    req2 = AIGenerateRequest(prompt=prompt2)
    resp2 = await generate_workflow(req2, current_user=mock_user)
    sched2 = resp2.get("data", {}).get("schedule")
    job_id2 = sched2.get("job_id")

    assert job_id1 == job_id2, "Re-generating prompt for same workflow must update existing schedule, not duplicate"
    assert sched2.get("interval_seconds") == 900  # 15 minutes


@pytest.mark.asyncio
async def test_ai30_schedule_lifecycle_toggle_delete(mock_user):
    """Verify pause, resume, and delete operations on scheduled jobs (Item I)."""
    job = workflow_scheduler_service.schedule_job(
        prompt="Run every 1 hour",
        workflow_json={"workflow_id": "wf_lifecycle_test", "nodes": []},
        workflow_id="wf_lifecycle_test"
    )
    job_id = job.job_id

    # Pause
    assert workflow_scheduler_service.toggle_job(job_id, active=False) is True
    assert workflow_scheduler_service.get_job(job_id).status == "paused"

    # Resume
    assert workflow_scheduler_service.toggle_job(job_id, active=True) is True
    assert workflow_scheduler_service.get_job(job_id).status == "active"

    # Delete
    assert workflow_scheduler_service.delete_job(job_id) is True
    assert workflow_scheduler_service.get_job(job_id) is None


@pytest.mark.asyncio
async def test_ai30_manual_run_override(mock_user):
    """Verify prompts with non-scheduling overrides do NOT create schedules (Item J)."""
    prompt = "Find unread emails and log them do this once"
    req = AIGenerateRequest(prompt=prompt)
    resp = await generate_workflow(req, current_user=mock_user)
    data = resp.get("data", {})

    assert data.get("schedule") is None, "Manual one-off generation must not return schedule"


@pytest.mark.asyncio
async def test_ai30_exact_browser_prompt_and_schedule_separation(mock_user):
    """
    Verify exact browser prompt:
    'Find my latest email, summarize it using AI, and send the summary to the #all-agentflow-ai Slack channel every 1 minute.'
    Generates: Gmail List -> Gmail Get -> AI Summarize -> Slack (#all-agentflow-ai)
    With clean schedule metadata (schedule_expression = 'Every 1 minute').
    """
    prompt = "Find my latest email, summarize it using AI, and send the summary to the #all-agentflow-ai Slack channel every 1 minute."
    req = AIGenerateRequest(prompt=prompt)

    resp = await generate_workflow(req, current_user=mock_user)
    data = resp.get("data", {})

    # 1. Verify workflow DAG composition
    wf_json = data.get("workflow_json", {})
    nodes = wf_json.get("nodes", [])
    assert len(nodes) == 4, f"Expected 4 nodes (Gmail List, Gmail Get, AI Summarize, Slack), got {len(nodes)}"

    providers = [n.get("provider") or n.get("data", {}).get("provider") for n in nodes]
    operations = [n.get("operation") or n.get("operation_id") or n.get("data", {}).get("operation_id") for n in nodes]

    assert operations[0] in ["gmail.messages.list", "gmail.messages.search"]
    assert operations[1] == "gmail.messages.get"
    assert operations[2] == "ai.summarize"
    assert operations[3] == "slack.chat.postMessage"

    # Verify Slack Channel preservation
    slack_node = nodes[3]
    slack_params = slack_node.get("parameters") or slack_node.get("data", {}).get("parameters", {})
    assert slack_params.get("channel") == "#all-agentflow-ai", f"Expected #all-agentflow-ai, got {slack_params.get('channel')}"

    # 2. Verify Schedule metadata separation
    sched = data.get("schedule")
    assert sched is not None, "Schedule metadata must be present"
    assert sched.get("status") == "paused"
    assert sched.get("interval_seconds") == 60
    assert sched.get("schedule_type") == "interval"

    sched_expr = sched.get("schedule_expression")
    assert sched_expr == "Every 1 minute", f"Expected 'Every 1 minute', got '{sched_expr}'"
    assert prompt not in sched_expr, "Full prompt MUST NOT be stored in schedule_expression"
    assert "Find my latest email" not in sched_expr, "Workflow intent MUST NOT leak into schedule_expression"


def test_ai30_datetime_scheduling_intent_and_parsing():
    """Verify natural language date/time schedule parsing (Item M compliance)."""
    p1 = "send good morning email to aswinkumaarsr.cs24@bitsathy.ac.in at 12:17 am today"
    assert workflow_scheduler_service.has_scheduling_intent(p1) is True
    parsed1 = workflow_scheduler_service.parse_schedule_expression(p1)
    assert parsed1.get("schedule_type") == "one_shot"
    assert "Today at 12:17 AM" in parsed1.get("description", "")
    assert "+05:30" in parsed1.get("run_at_iso", "") or "T00:17:00" in parsed1.get("run_at_iso", "")

    p2 = "send email on September 20, 2026 at 6:30 pm"
    assert workflow_scheduler_service.has_scheduling_intent(p2) is True
    parsed2 = workflow_scheduler_service.parse_schedule_expression(p2)
    assert parsed2.get("schedule_type") == "one_shot"
    assert "September 20, 2026 at 06:30 PM" in parsed2.get("description", "")
    assert "2026-09-20T18:30:00" in parsed2.get("run_at_iso", "")


@pytest.mark.asyncio
async def test_ai30_execute_button_semantics_scheduled_vs_manual(mock_user):
    """Verify Execute button activates schedule without immediate execution for scheduled workflows, and executes immediately for manual workflows."""
    import shutil
    from app.api.v1.runtime import execute_full_workflow_dag

    shutil.rmtree(workflow_scheduler_service._storage_dir, ignore_errors=True)
    workflow_scheduler_service._jobs.clear()

    # Case A: Scheduled workflow
    prompt_sched = "Send report every 1 minute"
    req_gen = AIGenerateRequest(prompt=prompt_sched)
    gen_resp = await generate_workflow(req_gen, current_user=mock_user)
    wf_json = gen_resp.get("data", {}).get("workflow_json", {})
    wf_id = wf_json.get("workflow_id")

    # Schedule should be created in PAUSED state
    jobs = workflow_scheduler_service.list_jobs(wf_id)
    assert len(jobs) > 0
    job = jobs[0]
    assert job["status"] == "paused"

    # Now simulate Execute Workflow click
    exec_req = {"workflow": wf_json, "workflow_id": wf_id}
    exec_resp = await execute_full_workflow_dag(exec_req)

    assert exec_resp.get("success") is True
    assert exec_resp.get("status") == "SCHEDULE_ACTIVATED"
    assert exec_resp.get("nodes_executed") == 0

    # Verify schedule is now ACTIVE in scheduler
    job_updated = workflow_scheduler_service.get_job(job["job_id"])
    assert job_updated.status == "active"
    assert job_updated.enabled is True

    # Case B: Manual workflow (no scheduling intent)
    shutil.rmtree(workflow_scheduler_service._storage_dir, ignore_errors=True)
    workflow_scheduler_service._jobs.clear()
    prompt_manual = "Send email do this once"
    req_man = AIGenerateRequest(prompt=prompt_manual)
    gen_resp_man = await generate_workflow(req_man, current_user=mock_user)
    wf_json_man = gen_resp_man.get("data", {}).get("workflow_json", {})
    wf_id_man = wf_json_man.get("workflow_id") or "wf_manual_test_1"
    wf_json_man["workflow_id"] = wf_id_man

    # No schedule should exist
    assert len(workflow_scheduler_service.list_jobs(wf_id_man)) == 0

    # Now simulate Execute Workflow click
    exec_resp_man = await execute_full_workflow_dag({"workflow": wf_json_man, "workflow_id": wf_id_man})
    assert exec_resp_man.get("status") != "SCHEDULE_ACTIVATED"
    assert exec_resp_man.get("status") in ["COMPLETED", "FAILED", "WAITING", "WAITING_FOR_APPROVAL"]




