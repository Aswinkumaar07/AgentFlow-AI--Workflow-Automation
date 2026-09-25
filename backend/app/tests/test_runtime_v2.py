import pytest
from app.runtime.context import ExecutionContext
from app.runtime.dependency_resolver import DependencyResolver, dependency_resolver
from app.runtime.exceptions import DependencyCycleException, WorkflowCancelledException
from app.runtime.execution_history import execution_history_store
from app.runtime.node_executor import node_executor
from app.runtime.variable_store import VariableStore
from app.runtime.workflow_executor import workflow_runtime_executor


@pytest.mark.asyncio
async def test_variable_store_interpolation():
    vs = VariableStore({"user": "Alice"})
    scope = {
        "step_1": {"output": {"doc_id": "doc_999"}},
        "user": "Alice",
    }

    res = vs.interpolate("Processed {{step_1.output.doc_id}} for {{user}}", scope)
    assert res == "Processed doc_999 for Alice"

    exact = vs.interpolate("{{step_1.output.doc_id}}", scope)
    assert exact == "doc_999"


@pytest.mark.asyncio
async def test_dependency_resolver_topological_sort():
    steps = [
        {"step_id": "step_1", "dependencies": []},
        {"step_id": "step_2", "dependencies": ["step_1"]},
        {"step_id": "step_3", "dependencies": ["step_2"]},
    ]
    order = dependency_resolver.validate_dag(steps)
    assert order == ["step_1", "step_2", "step_3"]

    # Test cycle detection
    cycle_steps = [
        {"step_id": "step_1", "dependencies": ["step_2"]},
        {"step_id": "step_2", "dependencies": ["step_1"]},
    ]
    with pytest.raises(DependencyCycleException):
        dependency_resolver.validate_dag(cycle_steps)


@pytest.mark.asyncio
async def test_node_execution_payload_contract():
    context = ExecutionContext(execution_id="exec_test_01", workflow_id="wf_test")
    context.record_step_output("step_1", {"invoice_id": "inv_12345"})

    workflow_spec = {
        "workflow_id": "wf_test",
        "steps": [
            {
                "step_id": "step_2",
                "provider": "Generic",
                "operation_id": "generic.http.request",
                "parameters": {"query": "{{step_1.invoice_id}}"},
            }
        ],
    }

    node_input = context.build_node_input_payload(
        "step_2", {"query": "{{step_1.invoice_id}}"}, workflow_spec
    )
    assert node_input["metadata"]["interpolated_params"]["query"] == "inv_12345"

    res = await node_executor.execute_node(node_input)
    assert res["status"] == "COMPLETED"
    assert "output" in res
    assert "latency" in res
    assert "retries" in res
    assert "timestamp" in res


@pytest.mark.asyncio
async def test_full_runtime_dag_execution():
    workflow_spec = {
        "workflow_id": "wf_dag_v2",
        "steps": [
            {
                "step_id": "step_1",
                "provider": "Generic",
                "operation_id": "generic.http.request",
                "parameters": {"url": "https://api.myapp.com/fetch"},
            },
            {
                "step_id": "step_2",
                "provider": "Generic",
                "operation_id": "generic.webhook.send",
                "parameters": {"ref": "{{step_1.step_id}}"},
                "dependencies": ["step_1"],
            },
        ],
    }

    state = await workflow_runtime_executor.execute_workflow(workflow_spec)
    assert state.status == "COMPLETED"
    assert len(state.node_records) == 2
    assert "step_1" in state.node_records
    assert "step_2" in state.node_records

    # Check persistence in execution_history_store
    persisted = await execution_history_store.get_state(state.execution_id)
    assert persisted is not None
    assert persisted.status == "COMPLETED"
