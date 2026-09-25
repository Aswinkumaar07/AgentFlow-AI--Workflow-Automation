import pytest
import os
import shutil
import tempfile
import asyncio
from app.runtime.execution_history import ExecutionHistoryStore, DEFAULT_STORAGE_DIR
from app.runtime.state import WorkflowExecutionStateV2

@pytest.fixture
def temp_history_store(tmp_path):
    store_dir = str(tmp_path / "history")
    os.makedirs(store_dir, exist_ok=True)
    return ExecutionHistoryStore(storage_dir=store_dir)

@pytest.mark.asyncio
async def test_a_existing_history_files_load_into_index(temp_history_store):
    """A. Existing history files load correctly into the index on cold initialization."""
    # Write 3 history files directly to store_dir
    dir_path = temp_history_store._storage_dir
    state1 = WorkflowExecutionStateV2(execution_id="exec_init_1", workflow_id="wf_1", status="COMPLETED", tenant_id="usr_1", start_time=100.0)
    state2 = WorkflowExecutionStateV2(execution_id="exec_init_2", workflow_id="wf_1", status="FAILED", tenant_id="usr_1", start_time=200.0)
    state3 = WorkflowExecutionStateV2(execution_id="exec_init_3", workflow_id="wf_2", status="RUNNING", tenant_id="usr_1", start_time=150.0)

    for st in [state1, state2, state3]:
        with open(temp_history_store._get_file_path(st.execution_id), "w", encoding="utf-8") as f:
            f.write(st.model_dump_json(indent=2))

    # Fresh store with same storage dir
    fresh_store = ExecutionHistoryStore(storage_dir=dir_path)
    assert fresh_store._disk_loaded is False

    executions = await fresh_store.list_user_executions("usr_1")
    assert fresh_store._disk_loaded is True
    assert len(executions) == 3
    assert [e.execution_id for e in executions] == ["exec_init_2", "exec_init_3", "exec_init_1"]

@pytest.mark.asyncio
async def test_b_repeated_queries_do_not_reread_disk(temp_history_store, monkeypatch):
    """B. Repeated history queries use the in-memory index and do NOT reread disk files."""
    state = WorkflowExecutionStateV2(execution_id="exec_repeat_1", workflow_id="wf_repeat", status="COMPLETED", tenant_id="usr_1")
    await temp_history_store.save_state(state)

    # Force initial disk load
    await temp_history_store.list_user_executions("usr_1")

    # Spy on os.listdir to verify it is NOT called during repeated queries
    listdir_call_count = 0
    original_listdir = os.listdir

    def spy_listdir(path):
        nonlocal listdir_call_count
        listdir_call_count += 1
        return original_listdir(path)

    monkeypatch.setattr(os, "listdir", spy_listdir)

    for _ in range(10):
        res = await temp_history_store.list_user_executions("usr_1")
        assert len(res) == 1

    assert listdir_call_count == 0, f"Expected 0 os.listdir calls on repeated queries, got {listdir_call_count}"

@pytest.mark.asyncio
async def test_c_new_execution_appears_immediately(temp_history_store):
    """C. A newly created execution appears immediately in history without full index rebuild."""
    state1 = WorkflowExecutionStateV2(execution_id="exec_new_1", workflow_id="wf_new", status="COMPLETED", tenant_id="usr_1", start_time=10.0)
    await temp_history_store.save_state(state1)

    records = await temp_history_store.list_user_executions("usr_1")
    assert len(records) == 1
    assert records[0].execution_id == "exec_new_1"

    state2 = WorkflowExecutionStateV2(execution_id="exec_new_2", workflow_id="wf_new", status="RUNNING", tenant_id="usr_1", start_time=20.0)
    await temp_history_store.save_state(state2)

    records_updated = await temp_history_store.list_user_executions("usr_1")
    assert len(records_updated) == 2
    assert records_updated[0].execution_id == "exec_new_2"
    assert records_updated[1].execution_id == "exec_new_1"

@pytest.mark.asyncio
async def test_d_updated_execution_appears_with_updated_state(temp_history_store):
    """D. An updated execution appears with updated state."""
    state = WorkflowExecutionStateV2(execution_id="exec_upd_1", workflow_id="wf_upd", status="RUNNING", tenant_id="usr_1")
    await temp_history_store.save_state(state)

    fetched = await temp_history_store.get_state("exec_upd_1")
    assert fetched.status == "RUNNING"

    # Update status to COMPLETED
    state.status = "COMPLETED"
    state.end_time = 100.0
    await temp_history_store.save_state(state)

    updated_fetched = await temp_history_store.get_state("exec_upd_1")
    assert updated_fetched.status == "COMPLETED"
    assert updated_fetched.end_time == 100.0

    user_execs = await temp_history_store.list_user_executions("usr_1")
    assert user_execs[0].status == "COMPLETED"

@pytest.mark.asyncio
async def test_e_restart_rebuilds_index_from_disk(temp_history_store):
    """E. Restart/reinitialization rebuilds the index correctly from persisted JSON files."""
    dir_path = temp_history_store._storage_dir
    state1 = WorkflowExecutionStateV2(execution_id="exec_rst_1", workflow_id="wf_rst", status="COMPLETED", tenant_id="usr_1", start_time=100.0)
    state2 = WorkflowExecutionStateV2(execution_id="exec_rst_2", workflow_id="wf_rst", status="FAILED", tenant_id="usr_1", start_time=200.0)

    await temp_history_store.save_state(state1)
    await temp_history_store.save_state(state2)

    # Re-instantiate ExecutionHistoryStore simulating app restart
    restarted_store = ExecutionHistoryStore(storage_dir=dir_path)
    assert restarted_store._disk_loaded is False

    reloaded_list = await restarted_store.list_user_executions("usr_1")
    assert restarted_store._disk_loaded is True
    assert len(reloaded_list) == 2
    assert reloaded_list[0].execution_id == "exec_rst_2"
    assert reloaded_list[1].execution_id == "exec_rst_1"

@pytest.mark.asyncio
async def test_f_existing_disk_records_intact_and_parseable():
    """F. Existing history records on disk remain intact and loadable."""
    if not os.path.exists(DEFAULT_STORAGE_DIR):
        pytest.skip("Default storage directory does not exist.")

    store = ExecutionHistoryStore(storage_dir=DEFAULT_STORAGE_DIR)
    executions = await store.list_user_executions("usr_1")

    assert len(executions) >= 0
    # Every execution loaded must have a valid execution_id
    for ex in executions:
        assert ex.execution_id is not None
        assert ex.workflow_id is not None

@pytest.mark.asyncio
async def test_g_workflow_filtering_and_sorting(temp_history_store):
    """G & H. Workflow-specific history filtering and start_time sorting remain unchanged."""
    st1 = WorkflowExecutionStateV2(execution_id="ex_1", workflow_id="wf_alpha", status="COMPLETED", tenant_id="usr_1", start_time=10.0)
    st2 = WorkflowExecutionStateV2(execution_id="ex_2", workflow_id="wf_beta", status="COMPLETED", tenant_id="usr_1", start_time=50.0)
    st3 = WorkflowExecutionStateV2(execution_id="ex_3", workflow_id="wf_alpha", status="FAILED", tenant_id="usr_1", start_time=30.0)

    for st in [st1, st2, st3]:
        await temp_history_store.save_state(st)

    # Filter for wf_alpha
    alpha_execs = await temp_history_store.list_workflow_executions("wf_alpha")
    assert len(alpha_execs) == 2
    assert alpha_execs[0].execution_id == "ex_3"
    assert alpha_execs[1].execution_id == "ex_1"

    # Query all
    all_execs = await temp_history_store.list_workflow_executions("all")
    assert len(all_execs) == 3
    assert [e.execution_id for e in all_execs] == ["ex_2", "ex_3", "ex_1"]
