import pytest
import os
import asyncio
import time
from app.services.workflow_scheduler import workflow_scheduler_service, WorkflowSchedulerService
from app.runtime.execution_analytics import workflow_analytics_service
from app.versions.manager import workflow_version_manager


@pytest.mark.asyncio
async def test_ai28_natural_language_parsing():
    service = WorkflowSchedulerService()

    # 1. Interval expressions
    t1 = service.parse_schedule_expression("run every 30 minutes")
    assert t1["schedule_type"] == "interval"
    assert t1["interval_seconds"] == 1800

    t2 = service.parse_schedule_expression("run every 5 mins")
    assert t2["schedule_type"] == "interval"
    assert t2["interval_seconds"] == 300

    t3 = service.parse_schedule_expression("run every 2 hours")
    assert t3["schedule_type"] == "interval"
    assert t3["interval_seconds"] == 7200

    # 2. Daily & weekly cron expressions
    t4 = service.parse_schedule_expression("every day at 9 AM send sales summary")
    assert t4["schedule_type"] == "recurring"
    assert t4["cron"] == "0 9 * * *"

    t5 = service.parse_schedule_expression("every Monday at 10 AM generate report")
    assert t5["schedule_type"] == "recurring"
    assert t5["cron"] == "0 10 * * 1"

    # 3. One-shot delay expressions
    t6 = service.parse_schedule_expression("after 15 minutes trigger backup")
    assert t6["schedule_type"] == "one_shot"
    assert t6["delay_seconds"] == 900


@pytest.mark.asyncio
async def test_ai28_version_pinning_and_disk_persistence(tmp_path):
    storage_dir = str(tmp_path / "schedules")
    service = WorkflowSchedulerService(storage_dir=storage_dir)

    wf_id = "wf_ai28_test_pinning"
    dummy_spec = {
        "workflow_id": wf_id,
        "nodes": [
            {"id": "n1", "data": {"provider": "Gmail", "operation_id": "gmail.messages.list", "parameters": {}}},
        ],
        "edges": [],
    }

    v1 = await workflow_version_manager.create_version_snapshot(
        workflow_id=wf_id,
        workflow_spec=dummy_spec,
        name="Version 1",
        description="Initial version",
    )

    job = service.schedule_job(
        prompt="every 30 minutes",
        workflow_json=dummy_spec,
        name="30 Min Sync v1",
        workflow_id=wf_id,
        version_id=v1.version_id,
        version_number=v1.version_number,
    )

    assert job.version_id == v1.version_id
    assert job.version_number == v1.version_number
    assert job.interval_seconds == 1800

    # Create v2 for same workflow
    v2_spec = dict(dummy_spec)
    v2_spec["nodes"].append({"id": "n2", "data": {"provider": "Slack", "operation_id": "slack.chat.postMessage"}})
    v2 = await workflow_version_manager.create_version_snapshot(
        workflow_id=wf_id,
        workflow_spec=v2_spec,
        name="Version 2",
        description="Added Slack node",
    )

    # Verify that the schedule remains pinned to v1
    fetched_job = service.get_job(job.job_id)
    assert fetched_job is not None
    assert fetched_job.version_id == v1.version_id
    assert fetched_job.version_number == v1.version_number

    # Verify disk persistence file exists
    job_file = os.path.join(storage_dir, f"{job.job_id}.json")
    assert os.path.exists(job_file)


@pytest.mark.asyncio
async def test_ai28_idempotent_tick_execution(tmp_path):
    storage_dir = str(tmp_path / "schedules_tick")
    service = WorkflowSchedulerService(storage_dir=storage_dir)

    wf_id = "wf_ai28_tick_test"
    dummy_spec = {
        "workflow_id": wf_id,
        "nodes": [
            {"id": "n1", "data": {"provider": "Gmail", "operation_id": "gmail.messages.list", "parameters": {}}},
        ],
        "edges": [],
    }

    job = service.schedule_job(
        prompt="every 1 minute",
        workflow_json=dummy_spec,
        name="Frequent Tick",
        workflow_id=wf_id,
        interval_seconds=60,
    )

    # Force last_run_at to past so it's due
    job.last_run_at = None

    # First tick executes job
    res1 = await service.tick()
    assert len(res1) == 1
    assert res1[0]["job_id"] == job.job_id

    # Immediate second tick within same minute slot skips execution due to idempotency slot tracking
    res2 = await service.tick()
    assert len(res2) == 0


@pytest.mark.asyncio
async def test_ai28_run_now_on_demand(tmp_path):
    storage_dir = str(tmp_path / "schedules_run_now")
    service = WorkflowSchedulerService(storage_dir=storage_dir)

    wf_id = "wf_ai28_run_now"
    dummy_spec = {
        "workflow_id": wf_id,
        "nodes": [
            {"id": "n1", "data": {"provider": "Gmail", "operation_id": "gmail.messages.list", "parameters": {}}},
        ],
        "edges": [],
    }

    job = service.schedule_job(
        prompt="every Monday at 9 AM",
        workflow_json=dummy_spec,
        name="Monday Job",
        workflow_id=wf_id,
    )

    run_res = await service.run_now(job.job_id)
    assert run_res["schedule_id"] == job.job_id
    assert run_res["status"] in ["COMPLETED", "SUCCESS"]
    assert job.run_count == 1
    assert job.last_run_at is not None


@pytest.mark.asyncio
async def test_ai28_analytics_trigger_distribution():
    analytics = await workflow_analytics_service.get_workflow_analytics("all")
    assert "trigger_distribution" in analytics
    assert "summary" in analytics
    assert "trigger_distribution" in analytics["summary"]
    dist = analytics["trigger_distribution"]
    assert "manual" in dist
    assert "scheduled" in dist
    assert "webhook" in dist
