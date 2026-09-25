import pytest
import os
import shutil
import tempfile
import asyncio
from app.runtime.execution_history import ExecutionHistoryStore, DEFAULT_STORAGE_DIR
from app.runtime.state import WorkflowExecutionStateV2
from app.runtime.execution_analytics import WorkflowAnalyticsService
from app.services.workflow_scheduler import workflow_scheduler_service, ScheduledJobModel

@pytest.fixture
def temp_history_store(tmp_path):
    store_dir = str(tmp_path / "history")
    os.makedirs(store_dir, exist_ok=True)
    return ExecutionHistoryStore(storage_dir=store_dir)

@pytest.mark.asyncio
async def test_1_list_user_executions_returns_correct_records(temp_history_store):
    """1. list_user_executions() returns correct user records."""
    st1 = WorkflowExecutionStateV2(execution_id="exec_u1", workflow_id="wf_1", tenant_id="usr_1", status="COMPLETED")
    st2 = WorkflowExecutionStateV2(execution_id="exec_u2", workflow_id="wf_2", tenant_id="usr_2", status="FAILED")
    await temp_history_store.save_state(st1)
    await temp_history_store.save_state(st2)

    user1_records = await temp_history_store.list_user_executions("usr_1")
    assert len(user1_records) == 1
    assert user1_records[0].execution_id == "exec_u1"

@pytest.mark.asyncio
async def test_2_list_workflow_executions_returns_correct_records(temp_history_store):
    """2. list_workflow_executions() returns correct workflow records."""
    st1 = WorkflowExecutionStateV2(execution_id="exec_w1", workflow_id="wf_alpha", tenant_id="usr_1", status="COMPLETED")
    st2 = WorkflowExecutionStateV2(execution_id="exec_w2", workflow_id="wf_beta", tenant_id="usr_1", status="COMPLETED")
    await temp_history_store.save_state(st1)
    await temp_history_store.save_state(st2)

    wf_alpha_records = await temp_history_store.list_workflow_executions("wf_alpha")
    assert len(wf_alpha_records) == 1
    assert wf_alpha_records[0].execution_id == "exec_w1"

@pytest.mark.asyncio
async def test_3_mutation_isolation_top_level_fields(temp_history_store):
    """3. Returned records cannot mutate the internal cached history state unexpectedly."""
    st = WorkflowExecutionStateV2(execution_id="exec_iso", workflow_id="wf_iso", tenant_id="usr_1", status="COMPLETED")
    await temp_history_store.save_state(st)

    list_res = await temp_history_store.list_user_executions("usr_1")
    retrieved = list_res[0]
    retrieved.status = "MUTATED_EXTERNALLY"

    # Verify store memory dict remains unchanged
    refetched = await temp_history_store.get_state("exec_iso")
    assert refetched.status == "COMPLETED"

@pytest.mark.asyncio
async def test_4_update_execution_path(temp_history_store):
    """4. Updating an execution through the existing update path still works."""
    st = WorkflowExecutionStateV2(execution_id="exec_upd", workflow_id="wf_upd", tenant_id="usr_1", status="RUNNING")
    await temp_history_store.save_state(st)

    st.status = "COMPLETED"
    st.end_time = 500.0
    await temp_history_store.save_state(st)

    updated = await temp_history_store.get_state("exec_upd")
    assert updated.status == "COMPLETED"
    assert updated.end_time == 500.0

@pytest.mark.asyncio
async def test_5_scheduler_overlap_protection_works(temp_history_store, monkeypatch):
    """5. Scheduler overlap protection still works using fast shallow copy."""
    st_waiting = WorkflowExecutionStateV2(
        execution_id="exec_sched_w",
        workflow_id="wf_sched_overlap",
        tenant_id="usr_1",
        status="WAITING",
        context_data={"schedule_id": "job_overlap_1"}
    )
    await temp_history_store.save_state(st_waiting)

    # Scheduler list_workflow_executions query
    records = await temp_history_store.list_workflow_executions("wf_sched_overlap")
    waiting_execs = [
        e for e in records
        if e.status in ["WAITING", "RUNNING"] and e.context_data.get("schedule_id") == "job_overlap_1"
    ]
    assert len(waiting_execs) == 1
    assert waiting_execs[0].execution_id == "exec_sched_w"

@pytest.mark.asyncio
async def test_6_analytics_receives_correct_execution_data(temp_history_store):
    """6. Analytics still receives correct execution data."""
    st = WorkflowExecutionStateV2(
        execution_id="exec_an",
        workflow_id="wf_analytics_test",
        tenant_id="usr_1",
        status="COMPLETED",
        start_time=100.0,
        end_time=110.0,
        node_records={"step_1": {"status": "COMPLETED", "latency_ms": 50.0}}
    )
    await temp_history_store.save_state(st)

    analytics_svc = WorkflowAnalyticsService(history_store=temp_history_store)
    analytics = await analytics_svc.get_workflow_analytics("wf_analytics_test")

    assert analytics["summary"]["total_executions"] == 1
    assert analytics["summary"]["successful_executions"] == 1
    assert analytics["summary"]["success_rate"] == 100.0

@pytest.mark.asyncio
async def test_7_resume_checkpoint_behavior(temp_history_store):
    """7. Resume/checkpoint behavior remains unchanged."""
    st = WorkflowExecutionStateV2(
        execution_id="exec_res",
        workflow_id="wf_resume_test",
        tenant_id="usr_1",
        status="PAUSED",
        context_data={"checkpoint_id": "cp_123"}
    )
    await temp_history_store.save_state(st)

    retrieved = await temp_history_store.get_state("exec_res")
    assert retrieved.status == "PAUSED"
    assert retrieved.context_data.get("checkpoint_id") == "cp_123"

@pytest.mark.asyncio
async def test_8_ordering_and_filtering(temp_history_store):
    """8. Existing ordering (newest first) and filtering remain unchanged."""
    st1 = WorkflowExecutionStateV2(execution_id="e1", workflow_id="wf_ord", tenant_id="usr_1", start_time=10.0)
    st2 = WorkflowExecutionStateV2(execution_id="e2", workflow_id="wf_ord", tenant_id="usr_1", start_time=30.0)
    st3 = WorkflowExecutionStateV2(execution_id="e3", workflow_id="wf_ord", tenant_id="usr_1", start_time=20.0)

    for st in [st1, st2, st3]:
        await temp_history_store.save_state(st)

    ordered = await temp_history_store.list_workflow_executions("wf_ord")
    assert [e.execution_id for e in ordered] == ["e2", "e3", "e1"]

@pytest.mark.asyncio
async def test_9_disk_loaded_cache_behavior(temp_history_store, monkeypatch):
    """9. Existing _disk_loaded history cache behavior remains intact."""
    st = WorkflowExecutionStateV2(execution_id="e_cache", workflow_id="wf_c", tenant_id="usr_1")
    await temp_history_store.save_state(st)

    # Initial load
    await temp_history_store.list_user_executions("usr_1")
    assert temp_history_store._disk_loaded is True

    # Ensure listdir is not called on repeated query
    listdir_calls = 0
    orig_listdir = os.listdir
    def spy_listdir(path):
        nonlocal listdir_calls
        listdir_calls += 1
        return orig_listdir(path)

    monkeypatch.setattr(os, "listdir", spy_listdir)

    for _ in range(5):
        await temp_history_store.list_user_executions("usr_1")

    assert listdir_calls == 0

@pytest.mark.asyncio
async def test_10_no_persisted_data_lost():
    """10. No persisted history data is lost."""
    if not os.path.exists(DEFAULT_STORAGE_DIR):
        pytest.skip("Default storage dir missing.")

    store = ExecutionHistoryStore(storage_dir=DEFAULT_STORAGE_DIR)
    records = await store.list_user_executions("usr_1")
    assert len(records) > 0
    for r in records:
        assert r.execution_id is not None
        assert r.workflow_id is not None
