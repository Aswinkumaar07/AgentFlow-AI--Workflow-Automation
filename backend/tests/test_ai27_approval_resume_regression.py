import pytest
import time
from app.runtime.workflow_executor import workflow_runtime_executor_v3
from app.runtime.execution_history import ExecutionHistoryStore
from app.runtime.checkpoint import CheckpointManager
from app.runtime.approval import HumanApprovalEngine


@pytest.fixture
def temp_stores(tmp_path):
    hist_dir = str(tmp_path / "history")
    cp_dir = str(tmp_path / "checkpoints")
    appr_dir = str(tmp_path / "approvals")

    hist_store = ExecutionHistoryStore(storage_dir=hist_dir)
    cp_mgr = CheckpointManager(storage_dir=cp_dir)
    appr_engine = HumanApprovalEngine(storage_dir=appr_dir)

    return hist_store, cp_mgr, appr_engine


@pytest.mark.asyncio
async def test_human_approval_resume_preserves_same_execution_id(temp_stores, monkeypatch):
    hist_store, cp_mgr, appr_engine = temp_stores

    monkeypatch.setattr(workflow_runtime_executor_v3, "history_store", hist_store)
    monkeypatch.setattr(workflow_runtime_executor_v3, "checkpoint_manager", cp_mgr)
    monkeypatch.setattr(workflow_runtime_executor_v3, "approval_engine", appr_engine)

    workflow_spec = {
        "workflow_id": "wf_approval_test",
        "version_id": "ver_wf_approval_v7",
        "version_number": 7,
        "nodes": [
            {"id": "step_1", "step_id": "step_1", "provider": "gmail", "operation_id": "gmail.messages.list", "parameters": {}, "dependencies": []},
            {"id": "step_2", "step_id": "step_2", "provider": "gmail", "operation_id": "gmail.messages.get", "parameters": {}, "dependencies": ["step_1"]},
            {"id": "step_3", "step_id": "step_3", "provider": "ai", "operation_id": "ai.summarize", "parameters": {}, "dependencies": ["step_2"]},
            {"id": "step_4", "step_id": "step_4", "provider": "human_approval", "operation_id": "approval.wait", "parameters": {}, "dependencies": ["step_3"]},
            {"id": "step_5", "step_id": "step_5", "provider": "slack", "operation_id": "slack.chat.postMessage", "parameters": {}, "dependencies": ["step_4"]},
        ],
        "edges": [
            {"source": "step_1", "target": "step_2"},
            {"source": "step_2", "target": "step_3"},
            {"source": "step_3", "target": "step_4"},
            {"source": "step_4", "target": "step_5"},
        ],
    }

    # 1. Start execution -> pauses at step_4 in WAITING
    mock_dispatch = lambda *args, **kwargs: {"status": "SUCCESS", "output": {"ok": True}}
    initial_state = await workflow_runtime_executor_v3.execute_workflow(
        workflow_spec,
        initial_context={"_mock_dispatch_fn": mock_dispatch}
    )
    exec_id = initial_state.execution_id

    assert exec_id.startswith("exec_v3_")
    assert initial_state.status == "WAITING"
    assert initial_state.node_records["step_1"]["status"] in ["COMPLETED", "SUCCESS"]
    assert initial_state.node_records["step_2"]["status"] in ["COMPLETED", "SUCCESS"]
    assert initial_state.node_records["step_3"]["status"] in ["COMPLETED", "SUCCESS"]
    assert "step_4" not in initial_state.node_records or initial_state.node_records["step_4"].get("status") not in ["COMPLETED", "SUCCESS"]
    assert "step_5" not in initial_state.node_records

    # Confirm exactly 1 execution stored in history
    executions_before = await hist_store.list_workflow_executions("wf_approval_test")
    assert len(executions_before) == 1
    assert executions_before[0].execution_id == exec_id
    assert executions_before[0].status == "WAITING"

    # 2. Approve human step -> resumes same execution
    resumed_state = await workflow_runtime_executor_v3.approve_node(exec_id, "step_4", approver="test_admin", initial_context={"_mock_dispatch_fn": mock_dispatch})

    assert resumed_state is not None
    assert resumed_state.execution_id == exec_id, "Execution ID MUST NOT CHANGE during approval resume!"
    assert resumed_state.status == "COMPLETED"
    assert resumed_state.version_number == 7
    assert resumed_state.version_id == "ver_wf_approval_v7"

    # Check node completion states
    assert resumed_state.node_records["step_1"]["status"] in ["COMPLETED", "SUCCESS"]
    assert resumed_state.node_records["step_2"]["status"] in ["COMPLETED", "SUCCESS"]
    assert resumed_state.node_records["step_3"]["status"] in ["COMPLETED", "SUCCESS"]
    assert resumed_state.node_records["step_4"]["status"] in ["COMPLETED", "SUCCESS"]
    assert resumed_state.node_records["step_5"]["status"] in ["COMPLETED", "SUCCESS"]

    # 3. Confirm STILL exactly 1 execution stored in history (WAITING updated in place to COMPLETED)
    executions_after = await hist_store.list_workflow_executions("wf_approval_test")
    assert len(executions_after) == 1
    assert executions_after[0].execution_id == exec_id
    assert executions_after[0].status == "COMPLETED"
