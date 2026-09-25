import pytest
import pytest_asyncio
from app.agents.task_decomposer.decomposer import EnterpriseTaskDecomposer
from app.api.v1.runtime import execute_full_workflow_dag, approve_human_step
from app.runtime.checkpoint import checkpoint_manager
from app.runtime.approval import human_approval_engine

@pytest.mark.asyncio
async def test_human_approval_dag_decomposition():
    decomposer = EnterpriseTaskDecomposer()
    prompt = "Find my latest email, summarize it using AI, then wait for my approval before sending the summary to #all-agentflow-ai on Slack."
    
    result = decomposer.decompose(prompt)
    assert len(result.tasks) == 5
    
    # Verify task topological sequence
    assert result.tasks[0].provider == "gmail"
    assert result.tasks[0].operation == "gmail.messages.list"
    
    assert result.tasks[1].provider == "gmail"
    assert result.tasks[1].operation == "gmail.messages.get"
    assert result.tasks[1].depends_on == [1]
    
    assert result.tasks[2].provider == "ai"
    assert result.tasks[2].operation == "ai.summarize"
    assert result.tasks[2].depends_on == [2]
    
    assert result.tasks[3].provider == "human_approval"
    assert result.tasks[3].operation == "approval.wait"
    assert result.tasks[3].depends_on == [3]
    
    assert result.tasks[4].provider == "slack"
    assert result.tasks[4].operation == "slack.chat.postMessage"
    assert result.tasks[4].depends_on == [4]
    assert result.tasks[4].parameters["channel"] == "#all-agentflow-ai"

@pytest.mark.asyncio
async def test_human_approval_execution_pauses_and_resumes():
    decomposer = EnterpriseTaskDecomposer()
    prompt = "Find my latest email, summarize it using AI, then wait for my approval before sending the summary to #all-agentflow-ai on Slack."
    result = decomposer.decompose(prompt)
    
    formatted_steps = []
    for idx, t in enumerate(result.tasks, 1):
        s_id = f"step_{idx}"
        deps = [f"step_{d}" for d in t.depends_on]
        formatted_steps.append({
            "step_id": s_id,
            "id": s_id,
            "provider": t.provider,
            "operation_id": t.operation,
            "parameters": t.parameters,
            "dependencies": deps,
        })
    
    workflow_spec = {
        "workflow_id": "wf_ai25_approval_test",
        "nodes": formatted_steps,
        "edges": [],
        "steps": formatted_steps,
    }
    
    # Initial execution -> should halt at step_4 (Human Approval)
    res = await execute_full_workflow_dag({"workflow": workflow_spec})
    
    assert res["status"] == "WAITING"
    assert res["can_resume"] is True
    assert res["checkpoint_timestamp"] is not None
    
    exec_id = res["execution_id"]
    
    # Verify checkpoint exists in store
    cp = await checkpoint_manager.restore(exec_id)
    assert cp is not None
    
    # Approve step 4 via engine
    app_res = await approve_human_step(execution_id=exec_id, node_id="step_4", approver="test_admin")
    assert app_res is not None
    status_val = getattr(app_res, "status", None) or (app_res.get("status") if isinstance(app_res, dict) else None)
    assert status_val in ("COMPLETED", "FAILED", "RUNNING")
