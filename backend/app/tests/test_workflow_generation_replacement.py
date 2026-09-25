import pytest
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_workflow_generation_sequential_replacement(async_client):
    token = create_access_token("usr_1")
    headers = {"Authorization": f"Bearer {token}"}

    # First prompt: Gmail send email
    prompt_1 = "Send an email using Gmail"
    res_1 = await async_client.post("/api/v1/ai/generate", json={"prompt": prompt_1}, headers=headers)
    assert res_1.status_code == 200
    payload_1 = res_1.json()
    assert payload_1["success"] is True
    wf_1 = payload_1["data"]["workflow_json"]
    nodes_1 = wf_1.get("nodes", [])
    operations_1 = [n.get("data", {}).get("operation_id") or n.get("operation_id") for n in nodes_1]
    assert "gmail.messages.send" in operations_1

    # Second prompt: Send message to Slack channel #all-agentflow-ai
    prompt_2 = 'Send "AgentFlow AI integration test" to #all-agentflow-ai'
    res_2 = await async_client.post("/api/v1/ai/generate", json={"prompt": prompt_2}, headers=headers)
    assert res_2.status_code == 200
    payload_2 = res_2.json()
    assert payload_2["success"] is True
    wf_2 = payload_2["data"]["workflow_json"]
    nodes_2 = wf_2.get("nodes", [])
    operations_2 = [n.get("data", {}).get("operation_id") or n.get("operation_id") for n in nodes_2]

    # Verify second generation replaced the workflow completely
    assert "slack.chat.postMessage" in operations_2
    assert "gmail.messages.send" not in operations_2
    assert "manual.trigger" not in operations_2

    # Check Slack parameters
    slack_node = next(n for n in nodes_2 if (n.get("data", {}).get("operation_id") or n.get("operation_id")) == "slack.chat.postMessage")
    params = slack_node.get("parameters") or slack_node.get("data", {}).get("parameters") or {}
    assert params.get("channel") in ["#all-agentflow-ai", "all-agentflow-ai"]
