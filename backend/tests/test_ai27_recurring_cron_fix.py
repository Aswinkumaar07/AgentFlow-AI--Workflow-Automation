import pytest
import datetime
import time
from app.services.workflow_scheduler import WorkflowSchedulerService, ScheduledJobModel


@pytest.fixture
def temp_scheduler(tmp_path):
    storage_dir = str(tmp_path / "schedules")
    return WorkflowSchedulerService(storage_dir=storage_dir)


def test_cron_next_occurrence_calculation(temp_scheduler):
    """Test E: Cron expression 0 9 * * 1 next occurrence calculated correctly."""
    base_dt = datetime.datetime(2026, 9, 16, 1, 45, tzinfo=datetime.timezone.utc)  # Wednesday
    next_run = temp_scheduler.calculate_next_cron_run("0 9 * * 1", from_dt=base_dt, user_timezone="Asia/Kolkata")
    
    assert next_run is not None
    assert "2026-09-21" in next_run  # Next Monday
    assert "09:00:00" in next_run


@pytest.mark.asyncio
async def test_recurring_cron_stale_past_run_advances_to_future(temp_scheduler):
    """Test A & B: Stale recurring cron job ticks once and advances next_run_at to future."""
    stale_iso = "2026-09-14T16:44:48.828955+00:00"
    job = ScheduledJobModel(
        job_id="job_cron_test",
        name="Monday Sales Summary",
        prompt="Every Monday send summary",
        workflow_json={"workflow_id": "wf_cron_test", "nodes": []},
        schedule_type="recurring",
        cron_expression="0 9 * * 1",
        status="active",
        enabled=True,
        next_run_at=stale_iso,
        timezone="Asia/Kolkata",
    )
    temp_scheduler._jobs[job.job_id] = job
    temp_scheduler._save_job_to_disk(job)

    # First tick: executes job ONCE
    res1 = await temp_scheduler.tick()
    assert len(res1) == 1
    assert res1[0]["job_id"] == "job_cron_test"

    updated_job = temp_scheduler.get_job("job_cron_test")
    assert updated_job.run_count == 1
    assert updated_job.next_run_at != stale_iso
    
    # Verify next_run_at is strictly in the future
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    assert updated_job.next_run_at > now_iso

    # Second tick immediately after: MUST NOT execute again
    res2 = await temp_scheduler.tick()
    assert len(res2) == 0
    assert updated_job.run_count == 1


@pytest.mark.asyncio
async def test_interval_schedule_behavior_unchanged(temp_scheduler):
    """Test C: Interval schedule advances next_run_at by interval_seconds."""
    stale_iso = "2026-09-14T16:44:48.828955+00:00"
    job = ScheduledJobModel(
        job_id="job_interval_test",
        name="Interval Job",
        prompt="Every 10 minutes",
        workflow_json={"workflow_id": "wf_interval_test", "nodes": []},
        schedule_type="interval",
        interval_seconds=600,
        status="active",
        enabled=True,
        next_run_at=stale_iso,
    )
    temp_scheduler._jobs[job.job_id] = job
    temp_scheduler._save_job_to_disk(job)

    res1 = await temp_scheduler.tick()
    assert len(res1) == 1
    updated_job = temp_scheduler.get_job("job_interval_test")
    assert updated_job.next_run_at > stale_iso
    assert updated_job.run_count == 1

    # Immediate second tick does not run
    res2 = await temp_scheduler.tick()
    assert len(res2) == 0


@pytest.mark.asyncio
async def test_one_shot_schedule_behavior_unchanged(temp_scheduler):
    """Test D: One-shot schedule completes and disables after execution."""
    stale_iso = "2026-09-14T16:44:48.828955+00:00"
    job = ScheduledJobModel(
        job_id="job_oneshot_test",
        name="One Shot Job",
        prompt="Run once",
        workflow_json={"workflow_id": "wf_oneshot_test", "nodes": []},
        schedule_type="one_shot",
        status="active",
        enabled=True,
        next_run_at=stale_iso,
    )
    temp_scheduler._jobs[job.job_id] = job
    temp_scheduler._save_job_to_disk(job)

    res1 = await temp_scheduler.tick()
    assert len(res1) == 1
    updated_job = temp_scheduler.get_job("job_oneshot_test")
    assert updated_job.status == "completed"
    assert updated_job.enabled is False
    assert updated_job.next_run_at is None

    # Subsequent tick does not run completed one-shot
    res2 = await temp_scheduler.tick()
    assert len(res2) == 0


@pytest.mark.asyncio
async def test_slot_idempotency_protection(temp_scheduler):
    """Test F: Same minute slot prevents duplicate executions on multiple ticks within same minute."""
    stale_iso = "2026-09-14T16:44:48.828955+00:00"
    job = ScheduledJobModel(
        job_id="job_slot_test",
        name="Slot Test",
        prompt="Cron test",
        workflow_json={"workflow_id": "wf_slot_test", "nodes": []},
        schedule_type="recurring",
        cron_expression="0 9 * * 1",
        status="active",
        enabled=True,
        next_run_at=stale_iso,
    )
    temp_scheduler._jobs[job.job_id] = job
    temp_scheduler._save_job_to_disk(job)

    res1 = await temp_scheduler.tick()
    assert len(res1) == 1

    # Ticking multiple times within the same minute
    for _ in range(5):
        res = await temp_scheduler.tick()
        assert len(res) == 0
