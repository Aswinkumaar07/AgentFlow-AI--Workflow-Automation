import pytest
from app.services.workflow_scheduler import workflow_scheduler_service
from app.agents.planner.planner_v4 import intelligent_planner_v4


def test_sched1_parse_schedule_expressions():
    # 1. Tomorrow
    t1 = workflow_scheduler_service.parse_schedule_expression("Send email tomorrow at 9 AM")
    assert t1["schedule_type"] == "one_shot"
    assert "run_at_iso" in t1

    # 2. After 2 hours
    t2 = workflow_scheduler_service.parse_schedule_expression("Run workflow after 2 hours")
    assert t2["schedule_type"] == "one_shot"
    assert t2["delay_seconds"] == 7200

    # 3. Next Monday
    t3 = workflow_scheduler_service.parse_schedule_expression("Send report next monday")
    assert t3["schedule_type"] == "one_shot"
    assert "run_at_iso" in t3

    # 4. Every Monday
    t4 = workflow_scheduler_service.parse_schedule_expression("Send status update every monday")
    assert t4["schedule_type"] == "recurring"
    assert t4["cron"] == "0 9 * * 1"

    # 5. Every day
    t5 = workflow_scheduler_service.parse_schedule_expression("Summarize inbox every day")
    assert t5["schedule_type"] == "recurring"
    assert t5["cron"] == "0 9 * * *"

    # 6. Every month
    t6 = workflow_scheduler_service.parse_schedule_expression("Generate invoice digest every month")
    assert t6["schedule_type"] == "recurring"
    assert t6["cron"] == "0 9 1 * *"


def test_sched1_planner_to_scheduler_pipeline():
    prompt = "Schedule email every Monday"
    plan = intelligent_planner_v4.plan(prompt)

    assert plan.schedule_metadata is not None
    s_meta = plan.schedule_metadata
    assert s_meta["schedule_type"] == "recurring"
    assert s_meta["cron_expression"] == "0 9 * * 1"

    job = workflow_scheduler_service.schedule_job(prompt, plan.workflow_graph)
    job_dict = job.to_dict()
    assert job_dict["status"] == "active"
    assert "job_id" in job_dict
    assert job_dict["job_id"].startswith("job_")


def test_sched1_job_persistence_and_cancellation():
    prompt = "Send reminder after 2 hours"
    sample_workflow = {"nodes": [{"id": "step_1", "operation": "gmail.messages.send"}]}

    job = workflow_scheduler_service.schedule_job(prompt, sample_workflow)
    job_id = job.job_id

    assert job_id in [j["job_id"] for j in workflow_scheduler_service.list_jobs()]
    fetched = workflow_scheduler_service.get_job(job_id)
    assert fetched is not None
    assert fetched.status == "active"

    cancelled = workflow_scheduler_service.cancel_job(job_id)
    assert cancelled is True
    assert workflow_scheduler_service.get_job(job_id).status == "cancelled"


def test_sched1_job_update():
    prompt = "Send email tomorrow"
    sample_workflow = {"nodes": [{"id": "step_1"}]}
    job = workflow_scheduler_service.schedule_job(prompt, sample_workflow)

    updated = workflow_scheduler_service.update_job(job.job_id, {"prompt": "Send email every monday", "name": "Updated Monday Job"})
    assert updated is not None
    assert updated.name == "Updated Monday Job"
    assert updated.schedule_type == "recurring"
    assert updated.cron_expression == "0 9 * * 1"
