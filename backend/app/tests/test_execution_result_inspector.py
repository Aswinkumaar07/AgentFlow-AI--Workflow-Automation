import pytest
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_execution_result_inspector_data_mapping(async_client):
    token = create_access_token("usr_1")
    headers = {"Authorization": f"Bearer {token}"}

    # Simulate 4-node multi-step workflow result payload
    execution_payload = {
        "execution_id": "exec_test_4node",
        "status": "COMPLETED",
        "nodes_executed": 4,
        "total_nodes": 4,
        "node_results": [
            {
                "node_id": "step_1",
                "provider": "gmail",
                "operation": "gmail.messages.list",
                "status": "SUCCESS",
                "latency_ms": 120,
                "output": {"messages": [], "total_items": 0}
            },
            {
                "node_id": "step_2",
                "provider": "gmail",
                "operation": "gmail.messages.get",
                "status": "SUCCESS",
                "latency_ms": 95,
                "output": {
                    "id": "msg_123",
                    "threadId": "th_123",
                    "snippet": "Test email body",
                    "payload": {
                        "headers": [
                            {"name": "From", "value": "test@example.com"},
                            {"name": "Subject", "value": "Test Subject"}
                        ]
                    }
                }
            },
            {
                "node_id": "step_3",
                "provider": "ai",
                "operation": "ai.summarize",
                "status": "SUCCESS",
                "latency_ms": 300,
                "output": {"summary": "AI summary of email content."}
            },
            {
                "node_id": "step_4",
                "provider": "slack",
                "operation": "slack.chat.postMessage",
                "status": "SUCCESS",
                "latency_ms": 150,
                "output": {
                    "ok": True,
                    "channel": "#all-agentflow-ai",
                    "ts": "1726154500.000100",
                    "message": {"text": "AgentFlow AI summary notification"}
                }
            }
        ]
    }

    # 1. Verify Slack step result payload contains Slack parameters
    slack_node = execution_payload["node_results"][3]
    assert slack_node["operation"] == "slack.chat.postMessage"
    assert slack_node["output"]["ok"] is True
    assert slack_node["output"]["channel"] == "#all-agentflow-ai"
    assert slack_node["output"]["ts"] == "1726154500.000100"

    # 2. Verify AI step result payload contains AI summary
    ai_node = execution_payload["node_results"][2]
    assert ai_node["operation"] == "ai.summarize"
    assert ai_node["output"]["summary"] == "AI summary of email content."

    # 3. Verify Gmail List step result payload contains zero items
    gmail_list_node = execution_payload["node_results"][0]
    assert gmail_list_node["operation"] == "gmail.messages.list"
    assert len(gmail_list_node["output"]["messages"]) == 0

    # 4. Verify Gmail Get step result payload contains message details
    gmail_get_node = execution_payload["node_results"][1]
    assert gmail_get_node["operation"] == "gmail.messages.get"
    assert gmail_get_node["output"]["id"] == "msg_123"
