import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.runtime.checkpoint import checkpoint_manager
from app.runtime.execution_history import execution_history_store
from app.runtime.lifecycle import WorkflowLifecycleState
from app.services.runtime_service import perform_canonical_resume


class TestCanonicalHistoryReplay:
    """
    Test suite verifying real canonical History Replay execution semantics.
    """

    @pytest.mark.asyncio
    async def test_replay_invokes_real_runtime_executor(self, monkeypatch):
        """A. History replay invokes WorkflowRuntimeExecutorV3.execute_workflow."""
        exec_id = "exec_test_real_replay_invoked"
        spec = {
            "workflow_id": "wf_real_replay",
            "steps": [
                {"step_id": "step_1", "id": "step_1", "provider": "schedule", "operation_id": "schedule.trigger", "parameters": {}},
                {"step_id": "step_2", "id": "step_2", "provider": "ai", "operation_id": "ai.summarize", "parameters": {"text": "Hello"}, "dependencies": ["step_1"]}
            ]
        }

        await checkpoint_manager.save_checkpoint(
            execution_id=exec_id,
            workflow_id="wf_real_replay",
            state=WorkflowLifecycleState.FAILED,
            variables={},
            completed_nodes={"step_1"},
            pending_nodes=["step_2"],
            outputs={},
            retries={},
            metadata={"workflow_spec": spec}
        )

        executor_called = []

        from app.runtime.workflow_executor import workflow_runtime_executor_v3

        orig_execute = workflow_runtime_executor_v3.execute_workflow

        async def mock_execute(workflow_spec, initial_context=None, resume_execution_id=None):
            executor_called.append({
                "workflow_spec": workflow_spec,
                "resume_execution_id": resume_execution_id
            })
            return await orig_execute(workflow_spec, initial_context, resume_execution_id)

        monkeypatch.setattr(workflow_runtime_executor_v3, "execute_workflow", mock_execute)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.post(f"/api/v1/history/{exec_id}/replay")
            assert res.status_code == 200
            data = res.json()["data"]

            assert len(executor_called) == 1
            assert executor_called[0]["resume_execution_id"] == exec_id
            assert data["execution_id"] == exec_id
            assert data["status"] == "COMPLETED"

    @pytest.mark.asyncio
    async def test_blocked_execution_remains_blocked_when_connection_missing(self):
        """C & D. BLOCKED_MISSING_CONNECTION remains blocked when connection is missing and is NOT manually forced to COMPLETED."""
        exec_id = "exec_test_blocked_connection_replay"
        spec = {
            "workflow_id": "wf_blocked_replay",
            "tenant_id": "usr_test_missing_conn",
            "steps": [
                {"step_id": "step_1", "id": "step_1", "provider": "gmail", "operation_id": "gmail.send", "parameters": {}}
            ]
        }

        # Save initial blocked state & checkpoint
        await checkpoint_manager.save_checkpoint(
            execution_id=exec_id,
            workflow_id="wf_blocked_replay",
            state=WorkflowLifecycleState.FAILED,
            variables={},
            completed_nodes=set(),
            pending_nodes=["step_1"],
            outputs={},
            retries={},
            metadata={"workflow_spec": spec}
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.post(f"/api/v1/history/{exec_id}/replay")
            assert res.status_code == 200
            data = res.json()["data"]

            # Must NOT be forced to COMPLETED; must remain BLOCKED_MISSING_CONNECTION
            assert data["status"] == "BLOCKED_MISSING_CONNECTION"
            assert data["success"] is False

    @pytest.mark.asyncio
    async def test_missing_checkpoint_returns_controlled_response(self):
        """G. Replaying execution with no checkpoint/state returns controlled non-success response."""
        exec_id = "exec_non_existent_id_9999"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.post(f"/api/v1/history/{exec_id}/replay")
            assert res.status_code == 200
            data = res.json()["data"]

            assert data["replayed"] is False
            assert data["status"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_legacy_blocked_execution_no_checkpoint_remains_unchanged(self, monkeypatch):
        """C. Legacy BLOCKED_MISSING_CONNECTION with no checkpoint/steps must NOT be set to COMPLETED."""
        exec_id = "exec_test_legacy_blocked_no_cp"
        from app.runtime.state import WorkflowExecutionStateV2
        state = WorkflowExecutionStateV2(
            execution_id=exec_id,
            workflow_id="wf_legacy_blocked",
            tenant_id="usr_1",
            status="BLOCKED_MISSING_CONNECTION",
            node_records={},
            context_data={}
        )
        await execution_history_store.save_state(state)

        executor_called = []
        from app.runtime.workflow_executor import workflow_runtime_executor_v3
        orig_execute = workflow_runtime_executor_v3.execute_workflow

        async def mock_execute(workflow_spec, initial_context=None, resume_execution_id=None):
            executor_called.append(resume_execution_id)
            return await orig_execute(workflow_spec, initial_context, resume_execution_id)

        monkeypatch.setattr(workflow_runtime_executor_v3, "execute_workflow", mock_execute)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.post(f"/api/v1/history/{exec_id}/replay")
            assert res.status_code == 200
            data = res.json()["data"]

            # Executor MUST NOT be called
            assert len(executor_called) == 0

            # Response must be NOT_FOUND / non-success
            assert data["replayed"] is False
            assert data["status"] == "NOT_FOUND"

            # Stored history state must remain unchanged as BLOCKED_MISSING_CONNECTION
            persisted_state = await execution_history_store.get_state(exec_id)
            assert persisted_state.status == "BLOCKED_MISSING_CONNECTION"
