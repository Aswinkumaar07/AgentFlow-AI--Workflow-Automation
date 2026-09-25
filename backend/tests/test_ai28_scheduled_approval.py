import pytest
import os
import time
import asyncio
from app.services.workflow_scheduler import workflow_scheduler_service, WorkflowSchedulerService
from app.runtime.workflow_executor import workflow_runtime_executor_v3
from app.runtime.execution_history import execution_history_store
from app.runtime.execution_analytics import workflow_analytics_service
from app.versions.manager import workflow_version_manager
from app.runtime.approval import human_approval_engine


@pytest.mark.asyncio
async def test_ai28_scheduled_approval_and_overlap_suite(tmp_path):
    from app.agents.oauth_ai.account_picker import account_picker, ConnectedAccount
    from app.connectors.security.secret_manager import secret_manager
    from app.connectors.models import ConnectorCredentialModel

    account_picker.add_or_update_account(
        ConnectedAccount(
            account_id="conn_slack_test",
            provider="Slack",
            email_or_name="test@slack.com",
            status="active",
            is_default=True,
        )
    )
    await secret_manager.set_secret(
        "usr_1",
        "Slack",
        ConnectorCredentialModel(
            provider="Slack",
            access_token="mock_slack_test_token",
            account_label="test@slack.com",
            scopes=["chat:write"],
        ),
    )

    storage_dir = str(tmp_path / "schedules_approval")
    scheduler = WorkflowSchedulerService(storage_dir=storage_dir)

    wf_id = "wf_ai28_sched_approval_test"
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
        name="Scheduled 5-node Approval Workflow",
        workflow_id=wf_id,
        version_id=v7.version_id,
        version_number=v7.version_number,
        interval_seconds=60,
        allow_overlap=False,
    )

    # A: Scheduled workflow runs via Run Now or tick
    res = await scheduler.run_now(job.job_id)
    assert res["success"] is True
    exec_id = res["execution_id"]
    assert exec_id.startswith("exec_v3_")

    # B: Reaches step_4 (Human Approval) and status is WAITING / WAITING_FOR_APPROVAL
    assert res["status"] in ["WAITING", "WAITING_FOR_APPROVAL"]

    # C & D: Persisted state has correct details
    state_before = await execution_history_store.get_state(exec_id)
    assert state_before is not None
    assert state_before.execution_id == exec_id
    assert state_before.status in ["WAITING", "WAITING_FOR_APPROVAL"]
    assert state_before.trigger_type == "scheduled"
    assert state_before.version_id == v7.version_id
    assert state_before.version_number == v7.version_number
    # Nodes 1, 2, 3 executed
    executed_nodes = [k for k, v in state_before.node_records.items() if (isinstance(v, dict) and v.get("status") in ["COMPLETED", "SUCCESS", "SUCCESSFUL"]) or not isinstance(v, dict)]
    assert "step_1" in state_before.node_records
    assert "step_2" in state_before.node_records
    assert "step_3" in state_before.node_records
    assert "step_4" not in state_before.node_records

    # K: Overlap Protection test - while exec_id is WAITING, tick should skip creating a duplicate execution
    job.last_run_at = None  # force due
    tick_results = await scheduler.tick()
    assert len(tick_results) == 0, "Tick should skip execution due to allow_overlap=False and WAITING prior run"

    # Analytics before approval
    analytics_before = await workflow_analytics_service.get_workflow_analytics(wf_id)
    initial_total = analytics_before["summary"]["total_executions"]

    # E & F: Approve step and resume under exact SAME execution_id
    approval_ok = await human_approval_engine.approve(exec_id, "step_4")
    assert approval_ok is True

    resumed_state = await workflow_runtime_executor_v3.execute_workflow(
        workflow_spec=dummy_spec,
        resume_execution_id=exec_id,
        initial_context={"_mock_dispatch_fn": lambda *args, **kwargs: {"status": "SUCCESS", "output": {"ok": True}}},
    )

    # S: resumed_state execution_id matches original
    assert resumed_state.execution_id == exec_id

    # H & G: Status becomes COMPLETED and all 5 nodes completed (including Slack step_5)
    assert resumed_state.status in ["COMPLETED", "SUCCESS"]
    assert len(resumed_state.node_records) == 5
    assert "step_4" in resumed_state.node_records
    assert "step_5" in resumed_state.node_records

    # I & J: Analytics verification - Total runs not duplicated, status updated
    analytics_after = await workflow_analytics_service.get_workflow_analytics(wf_id)
    # Total executions count remains the same (no duplicate run created)
    assert analytics_after["summary"]["total_executions"] == initial_total

    # L & M: Run count and version pinning intact
    assert job.run_count == 1
    assert job.version_id == v7.version_id

    # N: History has 1 execution entry for exec_id with COMPLETED status
    history = await execution_history_store.list_workflow_executions(wf_id)
    matching = [h for h in history if h.execution_id == exec_id]
    assert len(matching) == 1
    assert matching[0].status in ["COMPLETED", "SUCCESS"]

    # O: Version history intact
    v_history = await workflow_version_manager.get_version_history(wf_id)
    assert len(v_history) >= 1
    assert v_history[0].version_id == v7.version_id

    # P: Trigger distribution updated
    assert analytics_after["summary"]["trigger_distribution"]["scheduled"] >= 1
