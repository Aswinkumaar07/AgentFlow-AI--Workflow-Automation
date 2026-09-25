import pytest
from app.runtime.live_node_executor import live_node_executor
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_live_node_executor_generic_http():
    node = {
        "id": "step_http_1",
        "provider": "Generic REST",
        "operation_id": "generic.http.request",
        "parameters": {
            "url": "https://httpbin.org/post",
            "method": "POST",
            "body": "{\"test\": \"payload\"}",
        },
    }

    result = await live_node_executor.execute_node(node)
    assert result.node_id == "step_http_1"
    assert result.provider == "Generic REST"
    assert isinstance(result.status_code, int)
    assert result.status_code > 0
    assert result.latency_ms > 0
    assert result.request["url"] == "https://httpbin.org/post"
    assert "response" in result.model_dump()
    assert len(result.logs) >= 2


@pytest.mark.asyncio
async def test_live_node_executor_gmail_test():
    node = {
        "id": "step_gmail_1",
        "provider": "Gmail",
        "operation_id": "gmail.messages.send",
        "parameters": {
            "to": "test@company.com",
            "subject": "Live Test Subject",
            "body": "Live Test Body",
        },
    }

    result = await live_node_executor.execute_node(node)
    assert result.node_id == "step_gmail_1"
    assert result.provider == "Gmail"
    assert result.latency_ms >= 0.1
    assert "payload" in result.request


@pytest.mark.asyncio
async def test_runtime_test_node_api_endpoint(async_client):
    token = create_access_token("usr_1")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "node": {
            "id": "step_api_1",
            "provider": "Slack",
            "operation_id": "slack.chat.postMessage",
            "parameters": {
                "channel": "#general",
                "text": "Hello world from test node",
            },
        }
    }

    res = await async_client.post("/api/v1/runtime/test-node", json=payload, headers=headers)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["success"] is True
    data = res_data["data"]
    assert data["node_id"] == "step_api_1"
    assert data["provider"] == "Slack"
    assert "latency_ms" in data
    assert "status_code" in data
