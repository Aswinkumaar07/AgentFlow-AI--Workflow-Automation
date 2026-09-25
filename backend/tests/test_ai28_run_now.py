import pytest
import os
import time
import asyncio
from app.services.workflow_scheduler import workflow_scheduler_service, WorkflowSchedulerService
from app.runtime.workflow_executor import workflow_runtime_executor_v3
from app.runtime.execution_history import execution_history_store
from app.runtime.execution_analytics import workflow_analytics_service
from app.versions.manager import workflow_version_manager


@pytest.mark.asyncio
async def test_ai28_run_now_complete_suite(tmp_path):
    storage_dir = str(tmp_path / "schedules_run_now")
    scheduler = WorkflowSchedulerService(storage_dir=storage_dir)

    wf_id = "wf_ai28_run_now_test"
    dummy_spec = {
        "workflow_id": wf_id,
        "nodes": [
            {"id": "step_1", "step_id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.list", "parameters": {}},
            {"id": "step_2", "step_id": "step_2", "provider": "Gmail", "operation_id": "gmail.messages.get", "parameters": {}, "dependencies": ["step_1"]},
            {"id": "step_3", "step_id": "step_3", "provider": "AI", "operation_id": "ai.summarize", "parameters": {}, "dependencies": ["step_2"]},
            {"id": "step_4", "step_id": "step_4", "provider": "Approval", "operation_id": "approval.wait", "parameters": {}, "dependencies": ["step_3"]},
            {"id": "step_5", "step_id": "step_5", "provider": "Slack", "operation_id": "slack.chat.postMessage", "parameters": {}, "dependencies": ["step_4"]},
        ],
        "edges": [
            {"id": "e1", "source": "step_1", "target": "step_2"},
            {"id": "e2", "source": "step_2", "target": "step_3"},
            {"id": "e3", "source": "step_3", "target": "step_4"},
            {"id": "e4", "source": "step_4", "target": "step_5"},
        ],
    }

    # Pin to v7
    v7 = await workflow_version_manager.create_version_snapshot(
        workflow_id=wf_id,
        workflow_spec=dummy_spec,
        name="Version 7 - Pinned Workflow",
        description="5 node workflow",
    )

    job = scheduler.schedule_job(
        prompt="every 1 minute",
        workflow_json=dummy_spec,
        name="Scheduled 5-node Workflow",
        workflow_id=wf_id,
        version_id=v7.version_id,
        version_number=v7.version_number,
        interval_seconds=60,
        allow_overlap=True,
    )

    initial_run_count = job.run_count
    assert initial_run_count == 0

    # A & B: Run Now creates execution and returns execution_id
    res = await scheduler.run_now(job.job_id)
    assert res["success"] is True
    assert "execution_id" in res
    exec_id = res["execution_id"]
    assert exec_id.startswith("exec_v3_")

    # C: execution_id is persisted
    persisted_state = await execution_history_store.get_state(exec_id)
    assert persisted_state is not None
    assert persisted_state.execution_id == exec_id

    # D & E: trigger_type = scheduled & pinned version used
    assert persisted_state.trigger_type == "scheduled"
    assert persisted_state.version_id == v7.version_id
    assert persisted_state.version_number == v7.version_number

    # F & G: run_count increments exactly once & last_run_at updates
    assert job.run_count == 1
    assert job.last_run_at is not None

    # H: execution appears in workflow execution history
    history = await execution_history_store.list_workflow_executions(wf_id)
    assert any(h.execution_id == exec_id for h in history)

    # I: analytics records execution
    analytics = await workflow_analytics_service.get_workflow_analytics(wf_id)
    assert analytics["summary"]["total_executions"] >= 1
    assert analytics["summary"]["trigger_distribution"]["scheduled"] >= 1

    # J & N: runtime actually executes nodes up to Human Approval (WAITING)
    assert res["status"] in ["WAITING", "WAITING_FOR_APPROVAL"]
    assert len(persisted_state.node_records) >= 3

    # K: failed dispatch does not falsely increment successful run count
    with pytest.raises(ValueError):
        await scheduler.run_now("nonexistent_job_id_12345")

    # L: repeated Run Now creates distinct executions
    res2 = await scheduler.run_now(job.job_id)
    assert res2["execution_id"] != exec_id
    assert job.run_count == 2

    # M: automatic scheduler tick works
    job.last_run_at = None
    tick_results = await scheduler.tick()
    assert len(tick_results) >= 1

    # O: AI-25 resume still works for WAITING execution
    from app.runtime.approval import human_approval_engine
    approved_res = await human_approval_engine.approve(exec_id, "step_4")
    assert approved_res is True

    resumed_state = await workflow_runtime_executor_v3.execute_workflow(
        workflow_spec=dummy_spec,
        resume_execution_id=exec_id,
        initial_context={"_mock_dispatch_fn": lambda *args, **kwargs: {"status": "SUCCESS", "output": {"ok": True}}},
    )
    assert resumed_state.execution_id == exec_id
    assert resumed_state.status in ["COMPLETED", "SUCCESS"]

    # P: AI-26 version history intact
    v_history = await workflow_version_manager.get_version_history(wf_id)
    assert len(v_history) >= 1
    assert v_history[0].version_id == v7.version_id

    # Q: AI-27 analytics intact
    final_analytics = await workflow_analytics_service.get_workflow_analytics(wf_id)
    assert final_analytics["summary"]["total_executions"] >= 2
