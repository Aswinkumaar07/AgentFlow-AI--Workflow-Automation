import pytest
from app.services.workflow_scheduler import workflow_scheduler_service, WorkflowSchedulerService


def test_parse_schedule_expressions():
    service = WorkflowSchedulerService()

    # Recurring tests
    res_daily = service.parse_schedule_expression("Every Day send report")
    assert res_daily["schedule_type"] == "recurring"
    assert res_daily["cron"] == "0 9 * * *"

    res_monday = service.parse_schedule_expression("Every Monday read unread emails")
    assert res_monday["schedule_type"] == "recurring"
    assert res_monday["cron"] == "0 9 * * 1"

    res_monthly = service.parse_schedule_expression("Every Month calculate payroll")
    assert res_monthly["schedule_type"] == "recurring"
    assert res_monthly["cron"] == "0 9 1 * *"

    # One-shot delay tests
    res_delay = service.parse_schedule_expression("After 2 hours trigger backup")
    assert res_delay["schedule_type"] == "one_shot"
    assert res_delay["delay_seconds"] == 7200

    res_from_now = service.parse_schedule_expression("run once 2 minutes from now")
    assert res_from_now["schedule_type"] == "one_shot"
    assert res_from_now["delay_seconds"] == 120

    res_later = service.parse_schedule_expression("run once 5 minutes later")
    assert res_later["schedule_type"] == "one_shot"
    assert res_later["delay_seconds"] == 300

    res_in_mins = service.parse_schedule_expression("in 10 minutes")
    assert res_in_mins["schedule_type"] == "one_shot"
    assert res_in_mins["delay_seconds"] == 600

    # One-shot date tests
    res_tomorrow = service.parse_schedule_expression("Tomorrow 9 AM send email")
    assert res_tomorrow["schedule_type"] == "one_shot"
    assert "09:00:00" in res_tomorrow["run_at_iso"]

    res_next_mon = service.parse_schedule_expression("Next Monday deploy update")
    assert res_next_mon["schedule_type"] == "one_shot"
    assert "09:00:00" in res_next_mon["run_at_iso"]


def test_schedule_and_persist_job():
    mock_workflow = {"nodes": [], "edges": []}
    job = workflow_scheduler_service.schedule_job(
        prompt="Every Monday send sales summary",
        workflow_json=mock_workflow,
        name="Monday Sales Summary",
        user_timezone="Asia/Kolkata",
    )

    assert job.job_id.startswith("job_")
    assert job.status == "active"
    assert job.cron_expression == "0 9 * * 1"
    assert job.timezone == "Asia/Kolkata"

    # Verify listing
    jobs_list = workflow_scheduler_service.list_jobs()
    assert any(j["job_id"] == job.job_id for j in jobs_list)


def test_edit_and_cancel_job():
    mock_workflow = {"nodes": [], "edges": []}
    job = workflow_scheduler_service.schedule_job(
        prompt="After 2 hours trigger alert",
        workflow_json=mock_workflow,
    )

    # Edit job
    updated = workflow_scheduler_service.update_job(job.job_id, {"name": "Edited Alert Job", "timezone": "UTC"})
    assert updated is not None
    assert updated.name == "Edited Alert Job"
    assert updated.timezone == "UTC"

    # Cancel job
    cancelled = workflow_scheduler_service.cancel_job(job.job_id)
    assert cancelled is True

    fetched = workflow_scheduler_service.get_job(job.job_id)
    assert fetched.status == "cancelled"
