import pytest
from app.runtime.events.event_types import RuntimeEvent, RuntimeEventType
from app.runtime.events.event_bus import event_bus
from app.runtime.live_node_executor import live_node_executor
from app.api.v1.runtime import get_runtime_execution_telemetry


@pytest.mark.asyncio
async def test_live_node_execution_status_states_and_telemetry():
    exec_id = "exec_live_status_test"

    # Publish events corresponding to node execution lifecycle
    await event_bus.publish(
        RuntimeEvent(
            event_type=RuntimeEventType.NODE_STARTED,
            execution_id=exec_id,
            workflow_id="wf_live_status",
            node_id="step_1",
            data={"status": "RUNNING", "provider": "Gmail"},
        )
    )

    await event_bus.publish(
        RuntimeEvent(
            event_type=RuntimeEventType.NODE_RETRYING,
            execution_id=exec_id,
            workflow_id="wf_live_status",
            node_id="step_1",
            data={"status": "RETRYING", "retries": 1, "status_code": 429},
        )
    )

    await event_bus.publish(
        RuntimeEvent(
            event_type=RuntimeEventType.NODE_COMPLETED,
            execution_id=exec_id,
            workflow_id="wf_live_status",
            node_id="step_1",
            data={"status": "COMPLETED", "status_code": 200, "latency_ms": 142.5, "retries": 1},
        )
    )

    events = event_bus.get_events_for_execution(exec_id)
    assert len(events) == 3

    event_types = [e.event_type for e in events]
    assert RuntimeEventType.NODE_STARTED in event_types
    assert RuntimeEventType.NODE_RETRYING in event_types
    assert RuntimeEventType.NODE_COMPLETED in event_types


@pytest.mark.asyncio
async def test_live_node_executor_metrics():
    node = {
        "id": "step_metrics_test",
        "provider": "Gmail",
        "operation_id": "gmail.messages.send",
        "parameters": {"to": "metrics@test.com", "subject": "Test", "body": "Body"},
    }

    res = await live_node_executor.execute_node(node)
    assert res.provider == "Gmail"
    assert res.operation_id == "gmail.messages.send"
    assert res.latency_ms >= 0
    assert res.status_code is not None
    assert res.status in ["SUCCESS", "FAILED"]
