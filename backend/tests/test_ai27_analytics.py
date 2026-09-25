import pytest
import time
from app.runtime.execution_history import ExecutionHistoryStore
from app.runtime.state import WorkflowExecutionStateV2
from app.runtime.execution_analytics import (
    WorkflowAnalyticsService,
    sanitize_telemetry_secrets,
)


@pytest.fixture
def temp_history_store(tmp_path):
    store_dir = str(tmp_path / "history")
    return ExecutionHistoryStore(storage_dir=store_dir)


@pytest.mark.asyncio
async def test_no_execution_history(temp_history_store):
    service = WorkflowAnalyticsService(history_store=temp_history_store)
    res = await service.get_workflow_analytics("wf_empty")

    assert res["workflow_id"] == "wf_empty"
    assert res["summary"]["total_executions"] == 0
    assert res["summary"]["successful_executions"] == 0
    assert res["summary"]["failed_executions"] == 0
    assert res["summary"]["success_rate"] is None
    assert res["summary"]["average_duration_ms"] is None
    assert res["status_distribution"]["COMPLETED"] == 0
    assert res["node_statistics"] == []
    assert res["recent_executions"] == []


@pytest.mark.asyncio
async def test_single_successful_execution(temp_history_store):
    service = WorkflowAnalyticsService(history_store=temp_history_store)
    t_now = time.time()

    state = WorkflowExecutionStateV2(
        execution_id="exec_1",
        workflow_id="wf_1",
        version_id="ver_1",
        version_number=1,
        status="COMPLETED",
        start_time=t_now - 2.0,
        end_time=t_now,
        node_records={
            "step_1": {
                "status": "COMPLETED",
                "latency_ms": 500,
                "provider": "Gmail",
                "operation": "gmail.messages.list",
            }
        },
    )
    await temp_history_store.save_state(state)

    res = await service.get_workflow_analytics("wf_1")

    assert res["summary"]["total_executions"] == 1
    assert res["summary"]["successful_executions"] == 1
    assert res["summary"]["failed_executions"] == 0
    assert res["summary"]["success_rate"] == 100.0
    assert res["summary"]["average_duration_ms"] == 2000.0
    assert res["status_distribution"]["COMPLETED"] == 1

    node = res["node_statistics"][0]
    assert node["node_id"] == "step_1"
    assert node["execution_count"] == 1
    assert node["success_count"] == 1
    assert node["failure_rate"] == 0.0


@pytest.mark.asyncio
async def test_multiple_executions_and_rates(temp_history_store):
    service = WorkflowAnalyticsService(history_store=temp_history_store)
    t_now = time.time()

    ex1 = WorkflowExecutionStateV2(
        execution_id="exec_1",
        workflow_id="wf_multi",
        status="COMPLETED",
        start_time=t_now - 3.0,
        end_time=t_now - 1.0,
    )
    ex2 = WorkflowExecutionStateV2(
        execution_id="exec_2",
        workflow_id="wf_multi",
        status="FAILED",
        start_time=t_now - 2.0,
        end_time=t_now - 1.0,
    )
    ex3 = WorkflowExecutionStateV2(
        execution_id="exec_3",
        workflow_id="wf_multi",
        status="WAITING",
        start_time=t_now - 1.0,
    )

    await temp_history_store.save_state(ex1)
    await temp_history_store.save_state(ex2)
    await temp_history_store.save_state(ex3)

    res = await service.get_workflow_analytics("wf_multi")

    assert res["summary"]["total_executions"] == 3
    assert res["summary"]["successful_executions"] == 1
    assert res["summary"]["failed_executions"] == 1
    assert res["summary"]["waiting_executions"] == 1
    assert res["summary"]["success_rate"] == 50.0
    assert res["summary"]["average_duration_ms"] == 1500.0


@pytest.mark.asyncio
async def test_skipped_nodes_not_counted_as_failures(temp_history_store):
    service = WorkflowAnalyticsService(history_store=temp_history_store)

    ex = WorkflowExecutionStateV2(
        execution_id="exec_cond",
        workflow_id="wf_cond",
        status="COMPLETED",
        node_records={
            "step_cond": {"status": "COMPLETED", "latency_ms": 10},
            "step_true": {"status": "COMPLETED", "latency_ms": 100},
            "step_false": {"status": "SKIPPED", "latency_ms": 0},
        },
    )
    await temp_history_store.save_state(ex)

    res = await service.get_workflow_analytics("wf_cond")
    nodes_map = {n["node_id"]: n for n in res["node_statistics"]}

    assert nodes_map["step_false"]["skipped_count"] == 1
    assert nodes_map["step_false"]["failure_count"] == 0
    assert nodes_map["step_false"]["failure_rate"] == 0.0


@pytest.mark.asyncio
async def test_loop_iteration_statistics(temp_history_store):
    service = WorkflowAnalyticsService(history_store=temp_history_store)

    ex = WorkflowExecutionStateV2(
        execution_id="exec_loop",
        workflow_id="wf_loop",
        status="COMPLETED",
        node_records={
            "step_loop": {
                "status": "COMPLETED",
                "latency_ms": 400,
                "output": {
                    "iterations": [
                        {"index": 0, "status": "COMPLETED"},
                        {"index": 1, "status": "COMPLETED"},
                        {"index": 2, "status": "FAILED"},
                    ]
                },
            }
        },
    )
    await temp_history_store.save_state(ex)

    res = await service.get_workflow_analytics("wf_loop")
    node = res["node_statistics"][0]

    assert node["iterations"] == 3
    assert node["successful_iterations"] == 2
    assert node["failed_iterations"] == 1


@pytest.mark.asyncio
async def test_resumed_execution_remains_single_record(temp_history_store):
    service = WorkflowAnalyticsService(history_store=temp_history_store)
    t_now = time.time()

    ex = WorkflowExecutionStateV2(
        execution_id="exec_resume",
        workflow_id="wf_res",
        status="WAITING",
        start_time=t_now - 5.0,
    )
    await temp_history_store.save_state(ex)

    res1 = await service.get_workflow_analytics("wf_res")
    assert res1["summary"]["total_executions"] == 1
    assert res1["summary"]["waiting_executions"] == 1

    # Simulate resume by mutating state in place
    ex.status = "COMPLETED"
    ex.end_time = 105.0
    await temp_history_store.save_state(ex)

    res2 = await service.get_workflow_analytics("wf_res")
    assert res2["summary"]["total_executions"] == 1
    assert res2["summary"]["successful_executions"] == 1
    assert res2["summary"]["waiting_executions"] == 0


def test_secret_sanitization():
    payload = {
        "execution_id": "exec_sec",
        "api_key": "secret_12345",
        "access_token": "ya29.abcdef1234567890",
        "nested": {
            "refresh_token": "xoxb-12345",
            "safe_field": "hello_world",
        },
        "auth_header": "Bearer token_xyz",
    }
    cleaned = sanitize_telemetry_secrets(payload)

    assert cleaned["api_key"] == "[REDACTED_SECRET]"
    assert cleaned["access_token"] == "[REDACTED_SECRET]"
    assert cleaned["nested"]["refresh_token"] == "[REDACTED_SECRET]"
    assert cleaned["nested"]["safe_field"] == "hello_world"
    assert cleaned["auth_header"] == "[REDACTED_SECRET]"


@pytest.mark.asyncio
async def test_workflow_isolation(temp_history_store):
    service = WorkflowAnalyticsService(history_store=temp_history_store)

    ex_a = WorkflowExecutionStateV2(execution_id="ex_a", workflow_id="wf_A", status="COMPLETED")
    ex_b = WorkflowExecutionStateV2(execution_id="ex_b", workflow_id="wf_B", status="FAILED")

    await temp_history_store.save_state(ex_a)
    await temp_history_store.save_state(ex_b)

    res_a = await service.get_workflow_analytics("wf_A")
    assert res_a["summary"]["total_executions"] == 1
    assert res_a["summary"]["successful_executions"] == 1
    assert res_a["summary"]["failed_executions"] == 0

    res_b = await service.get_workflow_analytics("wf_B")
    assert res_b["summary"]["total_executions"] == 1
    assert res_b["summary"]["successful_executions"] == 0
    assert res_b["summary"]["failed_executions"] == 1
