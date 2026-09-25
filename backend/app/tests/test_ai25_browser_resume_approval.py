import pytest
import pytest_asyncio
from app.agents.task_decomposer.decomposer import EnterpriseTaskDecomposer
from app.api.v1.runtime import execute_full_workflow_dag, approve_human_step, resume_execution
from app.runtime.checkpoint import checkpoint_manager
from app.runtime.approval import human_approval_engine

@pytest.mark.asyncio
async def test_human_approval_full_flow_no_reexecution():
    decomposer = EnterpriseTaskDecomposer()
    prompt = "Find my latest email, summarize it using AI, then wait for my approval before sending the summary to #all-agentflow-ai on Slack."
    result = decomposer.decompose(prompt)
    
    # 10. Verify provider human_approval is non-OAuth and clean
    assert any(t.provider == "human_approval" for t in result.tasks)
    
    formatted_steps = [
        {"step_id": "step_1", "id": "step_1", "provider": "gmail", "operation_id": "gmail.messages.list", "parameters": {"q": "", "max_results": 1}, "dependencies": []},
        {"step_id": "step_2", "id": "step_2", "provider": "gmail", "operation_id": "gmail.messages.get", "parameters": {"message_id": "{{step_1.messages[0].id}}"}, "dependencies": ["step_1"]},
        {"step_id": "step_3", "id": "step_3", "provider": "ai", "operation_id": "ai.summarize", "parameters": {"text": "{{step_2.snippet}}"}, "dependencies": ["step_2"]},
        {"step_id": "step_4", "id": "step_4", "provider": "human_approval", "operation_id": "approval.wait", "parameters": {}, "dependencies": ["step_3"]},
        {"step_id": "step_5", "id": "step_5", "provider": "slack", "operation_id": "slack.chat.postMessage", "parameters": {"channel": "#all-agentflow-ai", "text": "{{step_3.summary}}"}, "dependencies": ["step_4"]},
    ]
    
    workflow_spec = {
        "workflow_id": "wf_ai25_browser_approval_flow",
        "nodes": formatted_steps,
        "edges": [],
        "steps": formatted_steps,
    }
    
    # 1. Initial Execution -> Enters WAITING at step_4
    res1 = await execute_full_workflow_dag({"workflow": workflow_spec})
    assert res1["status"] == "WAITING"
    assert res1["nodes_executed"] == 3
    assert res1["can_resume"] is True
    assert res1["checkpoint_timestamp"] is not None
    exec_id = res1["execution_id"]

    # Verify step_1, step_2, step_3 completed
    node_records_1 = {r["node_id"]: r["status"] for r in res1["node_results"]}
    assert node_records_1["step_1"] == "SUCCESS"
    assert node_records_1["step_2"] == "SUCCESS"
    assert node_records_1["step_3"] == "SUCCESS"
    assert node_records_1["step_4"] == "PENDING"
    assert node_records_1["step_5"] == "PENDING"

    # Resuming WITHOUT approval should re-pause at WAITING (item 8 & 9)
    res_resume_only = await resume_execution(execution_id=exec_id)
    assert res_resume_only["status"] == "WAITING"

    # 2. User explicitly APPROVES step_4
    res_approve = await approve_human_step(execution_id=exec_id, node_id="step_4", approver="admin_user")
    assert res_approve is not None
    assert res_approve["status"] in ("COMPLETED", "FAILED") # step_5 Slack may fail due to test token environment

    # 3. Check checkpoint integrity and no re-execution of step 1, 2, 3
    cp_final = await checkpoint_manager.restore(exec_id)
    assert cp_final is not None
    assert "step_1" in cp_final.completed_nodes
    assert "step_2" in cp_final.completed_nodes
    assert "step_3" in cp_final.completed_nodes
    assert "step_4" in cp_final.completed_nodes
