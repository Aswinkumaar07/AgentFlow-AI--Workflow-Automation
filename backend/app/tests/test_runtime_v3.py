import pytest
from app.runtime.approval import human_approval_engine
from app.runtime.checkpoint import checkpoint_manager
from app.runtime.dlq import dead_letter_queue
from app.runtime.events.event_bus import event_bus
from app.runtime.events.event_types import RuntimeEvent, RuntimeEventType
from app.runtime.exceptions import RuntimeException
from app.runtime.lifecycle import WorkflowLifecycle, WorkflowLifecycleState
from app.runtime.wait_handler import wait_handler
from app.runtime.workflow_executor import workflow_runtime_executor_v3


@pytest.mark.asyncio
async def test_event_bus_pub_sub():
    events_received = []

    def callback(evt: RuntimeEvent):
        events_received.append(evt)

    event_bus.subscribe(RuntimeEventType.WORKFLOW_STARTED, callback)

    event = RuntimeEvent(
        event_type=RuntimeEventType.WORKFLOW_STARTED,
        execution_id="exec_evt_1",
        workflow_id="wf_evt_1",
    )
    await event_bus.publish(event)

    assert len(events_received) == 1
    assert events_received[0].execution_id == "exec_evt_1"


@pytest.mark.asyncio
async def test_workflow_lifecycle_transitions():
    assert WorkflowLifecycle.validate_transition(WorkflowLifecycleState.CREATED, WorkflowLifecycleState.VALIDATING) is True
    assert WorkflowLifecycle.validate_transition(WorkflowLifecycleState.RUNNING, WorkflowLifecycleState.COMPLETED) is True

    # Test invalid transition
    with pytest.raises(RuntimeException):
        WorkflowLifecycle.validate_transition(WorkflowLifecycleState.CREATED, WorkflowLifecycleState.COMPLETED)


@pytest.mark.asyncio
async def test_checkpoint_restore():
    exec_id = "exec_cp_test"
    await checkpoint_manager.save_checkpoint(
        execution_id=exec_id,
        workflow_id="wf_cp",
        state=WorkflowLifecycleState.RUNNING,
        variables={"foo": "bar"},
        completed_nodes={"step_1"},
        pending_nodes=["step_2"],
        outputs={"step_1": {"res": "ok"}},
        retries={"step_1": 0},
    )

    restored = await checkpoint_manager.restore(exec_id)
    assert restored is not None
    assert restored.completed_nodes == ["step_1"]
    assert restored.variables["foo"] == "bar"


@pytest.mark.asyncio
async def test_wait_handler_node():
    res = await wait_handler.process_wait_node({"duration_seconds": 0.05})
    assert res["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_human_approval_node():
    exec_id = "exec_appr_01"
    req = await human_approval_engine.create_approval_request(exec_id, "step_approval")
    assert req.status == "PENDING"

    approved = await human_approval_engine.approve(exec_id, "step_approval", "admin_user")
    assert approved is True

    app_state = await human_approval_engine.get_approval(exec_id, "step_approval")
    assert app_state.status == "APPROVED"
    assert app_state.approver == "admin_user"


@pytest.mark.asyncio
async def test_dead_letter_queue_and_replay():
    exec_id = "exec_dlq_01"
    wf_spec = {"workflow_id": "wf_dlq", "steps": [{"step_id": "step_1"}]}

    record = await dead_letter_queue.push_failed_execution(exec_id, wf_spec, "step_1", "Connection timeout")
    assert record.node_id == "step_1"
    assert record.replayed is False

    replayed = await dead_letter_queue.replay(exec_id)
    assert replayed is not None
    assert replayed.replayed is True


@pytest.mark.asyncio
async def test_end_to_end_runtime_v3_execution():
    wf_spec = {
        "workflow_id": "wf_runtime_v3_e2e",
        "steps": [
            {
                "step_id": "step_1",
                "provider": "Generic",
                "operation_id": "generic.http.request",
                "parameters": {"method": "GET"},
            },
            {
                "step_id": "step_2",
                "provider": "Wait",
                "parameters": {"duration_seconds": 0.01},
                "dependencies": ["step_1"],
            },
        ],
    }

    state = await workflow_runtime_executor_v3.execute_workflow(wf_spec)
    assert state.status == "COMPLETED"
    assert len(state.node_records) == 2
    assert "step_1" in state.node_records
    assert "step_2" in state.node_records
