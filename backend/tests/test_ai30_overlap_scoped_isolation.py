import pytest
import asyncio
import time
from app.services.workflow_scheduler import workflow_scheduler_service, ScheduledJobModel
from app.runtime.execution_history import execution_history_store
from app.runtime.state import WorkflowExecutionStateV2


@pytest.fixture(autouse=True)
def reset_scheduler_jobs(monkeypatch):
    workflow_scheduler_service._jobs.clear()
    monkeypatch.setattr(workflow_scheduler_service, "_ensure_disk_loaded", lambda: None)
    monkeypatch.setattr(execution_history_store, "_ensure_disk_loaded", lambda: None)
    yield
    workflow_scheduler_service._jobs.clear()


@pytest.mark.asyncio
async def test_schedule_overlap_isolation_different_schedules():
    """1. Different schedules with same workflow_id do NOT block each other."""
    wf_id = "wf_shared_test_1"
    
    # Create WAITING execution belonging to job_A
    state_a = WorkflowExecutionStateV2(
        execution_id="exec_job_A_waiting",
        workflow_id=wf_id,
        status="WAITING",
        context_data={"schedule_id": "job_A", "trigger": {"schedule_id": "job_A"}}
    )
    await execution_history_store.save_state(state_a)

    # Schedule job_B for same workflow_id
    job_b = workflow_scheduler_service.schedule_job(
        prompt="every 1 minute",
        workflow_json={"workflow_id": wf_id, "nodes": []},
        workflow_id=wf_id,
        interval_seconds=60,
    )
    job_b.next_run_at = "2000-01-01T00:00:00+00:00" # Force due

    # Run tick
    res = await workflow_scheduler_service.tick()
    
    # job_B MUST execute and NOT be blocked by job_A's WAITING execution
    executed_jobs = [r["job_id"] for r in res]
    assert job_b.job_id in executed_jobs


@pytest.mark.asyncio
async def test_schedule_overlap_same_schedule_blocks():
    """2. Same schedule with WAITING execution DOES block."""
    wf_id = "wf_shared_test_2"
    job_a = workflow_scheduler_service.schedule_job(
        prompt="every 1 minute",
        workflow_json={"workflow_id": wf_id, "nodes": []},
        workflow_id=wf_id,
        interval_seconds=60,
    )
    job_a.next_run_at = "2000-01-01T00:00:00+00:00" # Force due

    state_a = WorkflowExecutionStateV2(
        execution_id="exec_job_A_block_waiting",
        workflow_id=wf_id,
        status="WAITING",
        context_data={"schedule_id": job_a.job_id}
    )
    await execution_history_store.save_state(state_a)

    res = await workflow_scheduler_service.tick()
    executed_jobs = [r["job_id"] for r in res]
    assert job_a.job_id not in executed_jobs


@pytest.mark.asyncio
async def test_schedule_overlap_running_blocks():
    """3. Same schedule with RUNNING execution DOES block."""
    wf_id = "wf_shared_test_3"
    job_a = workflow_scheduler_service.schedule_job(
        prompt="every 1 minute",
        workflow_json={"workflow_id": wf_id, "nodes": []},
        workflow_id=wf_id,
        interval_seconds=60,
    )
    job_a.next_run_at = "2000-01-01T00:00:00+00:00"

    state_a = WorkflowExecutionStateV2(
        execution_id="exec_job_A_running",
        workflow_id=wf_id,
        status="RUNNING",
        context_data={"schedule_id": job_a.job_id}
    )
    await execution_history_store.save_state(state_a)

    res = await workflow_scheduler_service.tick()
    executed_jobs = [r["job_id"] for r in res]
    assert job_a.job_id not in executed_jobs


@pytest.mark.asyncio
async def test_manual_execution_does_not_block_schedule():
    """4. Manual execution does NOT block scheduled execution."""
    wf_id = "wf_shared_test_4"
    
    # Manual execution state (no schedule_id)
    manual_state = WorkflowExecutionStateV2(
        execution_id="exec_manual_waiting",
        workflow_id=wf_id,
        status="WAITING",
        context_data={}
    )
    await execution_history_store.save_state(manual_state)

    job_a = workflow_scheduler_service.schedule_job(
        prompt="every 1 minute",
        workflow_json={"workflow_id": wf_id, "nodes": []},
        workflow_id=wf_id,
        interval_seconds=60,
    )
    job_a.next_run_at = "2000-01-01T00:00:00+00:00"

    res = await workflow_scheduler_service.tick()
    executed_jobs = [r["job_id"] for r in res]
    assert job_a.job_id in executed_jobs


@pytest.mark.asyncio
async def test_stale_schedule_name_refreshed():
    """8. Stale schedule name is refreshed when an existing schedule is updated."""
    import uuid
    wf_id = f"wf_stale_name_{uuid.uuid4().hex[:8]}"
    job = workflow_scheduler_service.schedule_job(
        prompt="Every Monday at 8 AM",
        workflow_json={"workflow_id": wf_id},
        workflow_id=wf_id,
        name="Scheduled Workflow (Weekly on Monday at 08:00)"
    )
    assert "Monday" in job.name

    # Update job with new prompt
    updated = workflow_scheduler_service.schedule_or_update_job(
        prompt="Find my latest email... every 1 minute.",
        workflow_json={"workflow_id": wf_id},
        workflow_id=wf_id,
        status="paused",
        enabled=False,
    )
    assert updated.job_id == job.job_id
    assert "Every 1 minute" in updated.name


@pytest.mark.asyncio
async def test_ai30_option1_lifecycle():
    """Option 1 Lifecycle: Generate creates paused schedule, Execute activates it."""
    import uuid
    wf_id = f"wf_opt1_lifecycle_{uuid.uuid4().hex[:8]}"
    
    # 1. Generate creates paused schedule
    job = workflow_scheduler_service.schedule_or_update_job(
        prompt="Find email every 1 minute",
        workflow_json={"workflow_id": wf_id, "nodes": []},
        workflow_id=wf_id,
        interval_seconds=60,
        status="paused",
        enabled=False,
    )
    assert job.status == "paused"
    assert job.enabled is False
    assert job.run_count == 0

    # 2. Tick loop skips paused schedule
    res = await workflow_scheduler_service.tick()
    executed_jobs = [r["job_id"] for r in res]
    assert job.job_id not in executed_jobs
    assert job.run_count == 0

    # 3. Simulate Execute activating schedule upon successful manual run
    workflow_scheduler_service.toggle_job(job.job_id, active=True)
    active_job = workflow_scheduler_service.get_job(job.job_id)
    assert active_job.status == "active"
    assert active_job.enabled is True
    assert active_job.run_count == 0

    # 4. Next tick dispatches scheduled run and increments run_count
    active_job.next_run_at = "2000-01-01T00:00:00+00:00"
    res2 = await workflow_scheduler_service.tick()
    executed_jobs2 = [r["job_id"] for r in res2]
    assert job.job_id in executed_jobs2
    assert workflow_scheduler_service.get_job(job.job_id).run_count == 1
