import pytest
from app.services.workflow_scheduler import workflow_scheduler_service, WorkflowSchedulerService, ScheduledJobModel


def test_scheduler_natural_language_parsing():
    # 1. Tomorrow
    res_tom = workflow_scheduler_service.parse_schedule_expression("Tomorrow send email")
    assert res_tom["schedule_type"] == "one_shot"
    assert "run_at_iso" in res_tom

    # 2. After 2 hours
    res_after = workflow_scheduler_service.parse_schedule_expression("After 2 hours send email")
    assert res_after["schedule_type"] == "one_shot"
    assert res_after["delay_seconds"] == 7200

    # 3. Next Monday
    res_next_mon = workflow_scheduler_service.parse_schedule_expression("Next Monday send report")
    assert res_next_mon["schedule_type"] == "one_shot"
    assert "run_at_iso" in res_next_mon

    # 4. Every Monday
    res_every_mon = workflow_scheduler_service.parse_schedule_expression("Every Monday send report")
    assert res_every_mon["schedule_type"] == "recurring"
    assert res_every_mon["cron"] == "0 9 * * 1"

    # 5. Every Day
    res_daily = workflow_scheduler_service.parse_schedule_expression("Every day check emails")
    assert res_daily["schedule_type"] == "recurring"
    assert res_daily["cron"] == "0 9 * * *"

    # 6. Monthly
    res_monthly = workflow_scheduler_service.parse_schedule_expression("Monthly invoice digest")
    assert res_monthly["schedule_type"] == "recurring"
    assert res_monthly["cron"] == "0 9 1 * *"

    # 7. Custom Cron
    res_cron = workflow_scheduler_service.parse_schedule_expression("cron: */15 * * * *")
    assert res_cron["schedule_type"] == "recurring"
    assert res_cron["cron"] == "*/15 * * * *"


def test_scheduler_job_crud_lifecycle():
    mock_workflow = {"nodes": [{"id": "step_1", "operation": "gmail.messages.send"}]}
    
    # Create Job
    job = workflow_scheduler_service.schedule_job(
        prompt="Tomorrow send John an email",
        workflow_json=mock_workflow,
        name="John Email Job",
        user_timezone="America/New_York",
    )

    assert isinstance(job, ScheduledJobModel)
    assert job.status == "active"
    assert job.timezone == "America/New_York"

    # Read Job
    retrieved = workflow_scheduler_service.get_job(job.job_id)
    assert retrieved is not None
    assert retrieved.name == "John Email Job"

    # List Jobs
    all_jobs = workflow_scheduler_service.list_jobs()
    assert any(j["job_id"] == job.job_id for j in all_jobs)

    # Edit / Update Job
    updated = workflow_scheduler_service.update_job(job.job_id, {"name": "Updated John Email Job", "prompt": "Every Monday send John email"})
    assert updated.name == "Updated John Email Job"
    assert updated.schedule_type == "recurring"
    assert updated.cron_expression == "0 9 * * 1"

    # Toggle Job
    toggled = workflow_scheduler_service.toggle_job(job.job_id, active=False)
    assert toggled is True
    assert workflow_scheduler_service.get_job(job.job_id).status == "paused"

    # Delete Job
    deleted = workflow_scheduler_service.delete_job(job.job_id)
    assert deleted is True
    assert workflow_scheduler_service.get_job(job.job_id) is None
