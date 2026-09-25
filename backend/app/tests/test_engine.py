import pytest
import time
from app.engine import (
    StepType,
    WorkflowCompiler,
    WorkflowExecutor,
    WorkflowStatus,
    human_approval_handler,
    state_machine,
    workflow_compiler,
    workflow_executor,
)


@pytest.mark.asyncio
async def test_workflow_compiler_dag_validation():
    raw_wf = {
        "workflow_id": "wf_test_dag",
        "name": "Invoice Automation DAG",
        "steps": [
            {
                "step_id": "step_1",
                "step_type": "CONNECTOR_ACTION",
                "provider": "Gmail",
                "operation_id": "gmail.messages.list",
                "parameters": {"q": "invoice"},
            },
            {
                "step_id": "step_2",
                "step_type": "CONNECTOR_ACTION",
                "provider": "Google Drive",
                "operation_id": "drive.files.create",
                "dependencies": ["step_1"],
            },
            {
                "step_id": "step_3",
                "step_type": "CONNECTOR_ACTION",
                "provider": "Slack",
                "operation_id": "slack.chat.postMessage",
                "dependencies": ["step_2"],
            },
        ],
    }

    compiled = workflow_compiler.compile(raw_wf)
    assert compiled.workflow_id == "wf_test_dag"
    assert len(compiled.steps) == 3
    assert compiled.steps[1].dependencies == ["step_1"]


@pytest.mark.asyncio
async def test_workflow_execution_dag():
    raw_wf = {
        "workflow_id": "wf_exec_test",
        "name": "Parallel Workflow Execution",
        "steps": [
            {
                "step_id": "step_fetch",
                "step_type": "CONNECTOR_ACTION",
                "provider": "Gmail",
                "operation_id": "gmail.messages.list",
            },
            {
                "step_id": "step_drive",
                "step_type": "CONNECTOR_ACTION",
                "provider": "Google Drive",
                "operation_id": "drive.files.create",
                "dependencies": ["step_fetch"],
            },
            {
                "step_id": "step_slack",
                "step_type": "CONNECTOR_ACTION",
                "provider": "Slack",
                "operation_id": "slack.chat.postMessage",
                "dependencies": ["step_fetch"],
            },
        ],
    }

    compiled = workflow_compiler.compile(raw_wf)
    result_state = await workflow_executor.execute_workflow(compiled, {"initial_key": "initial_value"})

    assert result_state.status == WorkflowStatus.COMPLETED
    assert len(result_state.step_states) == 3
    assert result_state.step_states["step_fetch"].status == WorkflowStatus.COMPLETED
    assert result_state.step_states["step_drive"].status == WorkflowStatus.COMPLETED
    assert result_state.step_states["step_slack"].status == WorkflowStatus.COMPLETED


@pytest.mark.asyncio
async def test_human_approval_pause_and_resume():
    raw_wf = {
        "workflow_id": "wf_approval_test",
        "name": "Human Approval Workflow",
        "steps": [
            {
                "step_id": "step_prep",
                "step_type": "CONNECTOR_ACTION",
                "provider": "Gmail",
                "operation_id": "gmail.messages.list",
            },
            {
                "step_id": "step_approval",
                "step_type": "HUMAN_APPROVAL",
                "dependencies": ["step_prep"],
            },
        ],
    }

    compiled = workflow_compiler.compile(raw_wf)
    paused_state = await workflow_executor.execute_workflow(compiled)

    assert paused_state.status == WorkflowStatus.WAITING_FOR_APPROVAL
    assert paused_state.step_states["step_approval"].status == WorkflowStatus.WAITING_FOR_APPROVAL

    # Grant approval
    approved = await human_approval_handler.approve_step(paused_state.execution_id, "step_approval", "manager_bob")
    assert approved is True

    updated_state = await state_machine.get_state(paused_state.execution_id)
    assert updated_state.step_states["step_approval"].status == WorkflowStatus.COMPLETED


@pytest.mark.asyncio
async def test_sub_50ms_workflow_execution_benchmark():
    raw_wf = {
        "workflow_id": "wf_bench",
        "name": "Benchmark Workflow",
        "steps": [
            {"step_id": "step_a", "step_type": "TRANSFORMATION", "parameters": {"op": "filter"}},
            {"step_id": "step_b", "step_type": "TRANSFORMATION", "parameters": {"op": "map"}, "dependencies": ["step_a"]},
        ],
    }

    compiled = workflow_compiler.compile(raw_wf)

    start = time.perf_counter()
    res = await workflow_executor.execute_workflow(compiled)
    duration_ms = (time.perf_counter() - start) * 1000.0

    assert res.status == WorkflowStatus.COMPLETED
    assert duration_ms < 50.0, f"Workflow execution was {duration_ms:.2f}ms, expected sub-50ms!"
