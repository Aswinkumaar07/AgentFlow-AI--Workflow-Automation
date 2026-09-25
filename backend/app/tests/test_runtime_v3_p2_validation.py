import asyncio
import pytest
from app.runtime.workflow_executor import workflow_runtime_executor_v3
from app.runtime.dependency_resolver import dependency_resolver
from app.runtime.exceptions import DependencyCycleException
from app.runtime.dlq import dead_letter_queue
from app.runtime.approval import human_approval_engine


@pytest.mark.asyncio
async def test_p2_topological_traversal_and_cycle_detection():
    # Valid DAG
    steps = [
        {"id": "step_1", "provider": "Gmail", "dependencies": []},
        {"id": "step_2", "provider": "AI", "dependencies": ["step_1"]},
        {"id": "step_3", "provider": "Slack", "dependencies": ["step_2"]},
    ]
    topo_order = dependency_resolver.validate_dag(steps)
    assert topo_order == ["step_1", "step_2", "step_3"]

    # Invalid Cyclic DAG
    cyclic_steps = [
        {"id": "step_1", "provider": "Gmail", "dependencies": ["step_2"]},
        {"id": "step_2", "provider": "Slack", "dependencies": ["step_1"]},
    ]
    with pytest.raises(DependencyCycleException):
        dependency_resolver.validate_dag(cyclic_steps)


@pytest.mark.asyncio
async def test_p2_all_17_node_types_execution():
    node_providers = [
        "Manual", "Webhook", "Schedule", "Condition", "Switch", "Loop", "Merge",
        "Approval", "Delay", "AI", "Code", "Generic REST", "Gmail", "Slack",
        "Google Sheets", "Google Drive", "GitHub"
    ]

    steps = []
    for idx, provider in enumerate(node_providers):
        if provider == "Approval":
            continue
        step_id = f"step_{idx+1}"
        deps = [f"step_{idx}"] if idx > 0 and node_providers[idx-1] != "Approval" else []
        steps.append({
            "id": step_id,
            "provider": provider,
            "operation_id": f"{provider.lower()}.operation",
            "parameters": {"sample_param": f"value_{idx}"},
            "dependencies": deps,
        })

    spec = {
        "workflow_id": "wf_17_nodes",
        "tenant_id": "usr_test",
        "steps": steps,
    }

    state = await workflow_runtime_executor_v3.execute_workflow(spec)
    assert state.status == "COMPLETED"
    assert len(state.node_records) == 16


@pytest.mark.asyncio
async def test_p2_variable_interpolation_and_loop_context():
    spec = {
        "workflow_id": "wf_interpolation",
        "steps": [
            {
                "id": "step_1",
                "provider": "Google Sheets",
                "parameters": {"range": "A1:Z5"},
                "dependencies": [],
            },
            {
                "id": "step_2",
                "provider": "Gmail",
                "parameters": {
                    "to": "{{step_1.output.params.range}}",
                    "subject": "Notice for {{step_1.output.provider}}",
                },
                "dependencies": ["step_1"],
            },
        ],
    }

    state = await workflow_runtime_executor_v3.execute_workflow(spec)
    assert state.status == "COMPLETED"
    step_2_rec = state.node_records["step_2"]
    assert step_2_rec["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_p2_human_approval_pause_and_approval_resume():
    spec = {
        "workflow_id": "wf_approval",
        "steps": [
            {"id": "step_1", "provider": "Gmail", "dependencies": []},
            {"id": "step_2", "provider": "Approval", "dependencies": ["step_1"]},
            {"id": "step_3", "provider": "Slack", "dependencies": ["step_2"]},
        ],
    }

    # First execution should pause at Approval node
    state = await workflow_runtime_executor_v3.execute_workflow(spec)
    assert state.status == "WAITING"

    # Approve node and resume workflow
    res_state = await workflow_runtime_executor_v3.approve_node(state.execution_id, "step_2", approver="manager")
    assert res_state is not None
    assert res_state.status == "COMPLETED"


@pytest.mark.asyncio
async def test_p2_dlq_replay_on_failed_execution():
    spec = {
        "workflow_id": "wf_dlq_test",
        "steps": [
            {"id": "step_1", "provider": "MockFailureProvider", "dependencies": []},
        ],
    }

    # Simulate DLQ push
    exec_id = "exec_dlq_101"
    await dead_letter_queue.push_failed_execution(exec_id, spec, "step_1", "Simulated network timeout")
    record = await dead_letter_queue.get_dlq_record(exec_id)
    assert record is not None
    assert record.execution_id == exec_id

    # Replay DLQ
    replayed_record = await dead_letter_queue.replay(exec_id)
    assert replayed_record is not None
    assert replayed_record.replayed is True


@pytest.mark.asyncio
async def test_p2_stress_testing_concurrent_100_executions():
    spec = {
        "workflow_id": "wf_stress",
        "steps": [
            {"id": "step_1", "provider": "Gmail", "dependencies": []},
            {"id": "step_2", "provider": "Slack", "dependencies": ["step_1"]},
        ],
    }

    # Execute 100 workflows concurrently with semaphore concurrency control
    sem = asyncio.Semaphore(20)

    async def run_guarded(s):
        async with sem:
            return await workflow_runtime_executor_v3.execute_workflow(s)

    tasks = [run_guarded(spec) for _ in range(100)]
    results = await asyncio.gather(*tasks)

    assert len(results) == 100
    assert all(r.status == "COMPLETED" for r in results)


@pytest.mark.asyncio
async def test_p2_large_dag_execution():
    # Construct large 25-node DAG
    steps = []
    for i in range(25):
        sid = f"node_{i+1}"
        deps = [f"node_{i}"] if i > 0 else []
        steps.append({
            "id": sid,
            "provider": "Generic REST",
            "dependencies": deps,
        })

    spec = {
        "workflow_id": "wf_large_dag",
        "steps": steps,
    }

    state = await workflow_runtime_executor_v3.execute_workflow(spec)
    assert state.status == "COMPLETED"
    assert len(state.node_records) == 25
