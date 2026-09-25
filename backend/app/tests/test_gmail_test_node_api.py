import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_gmail_test_node_api_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "node": {
                "id": "node_gmail_test",
                "provider": "Gmail",
                "operation_id": "gmail.messages.send",
                "parameters": {
                    "to": "test@domain.com",
                    "subject": "Test Node Gmail Subject",
                    "body": "Test Node Gmail Body",
                },
            },
            "context_variables": {"var1": "val1"},
        }

        res = await client.post("/api/v1/runtime/test-node", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert "success" in data
        assert "status" in data
        assert "status_code" in data
        assert "latency_ms" in data
        assert "headers" in data
        assert "response" in data
        assert "messageId" in data
        assert "threadId" in data


@pytest.mark.asyncio
async def test_gmail_test_node_api_failure_response():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "node": {
                "id": "node_gmail_fail",
                "provider": "Gmail",
                "operation_id": "gmail.messages.send",
                "parameters": {
                    "to": "invalid",
                },
            },
        }

        res = await client.post("/api/v1/runtime/test-node", json=payload)
        assert res.status_code == 200
        data = res.json()

        # Must return success=False when Google API rejects request
        assert data["success"] is False
        assert data["status"] == "FAILED"
        assert data["status_code"] in [400, 401, 403, 500]
        assert "google_error" in data
        assert "errors" in data
