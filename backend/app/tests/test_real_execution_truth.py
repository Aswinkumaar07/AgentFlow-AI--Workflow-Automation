import pytest
from app.connectors.providers.gmail.adapter import GmailAdapter
from app.connectors.models import ConnectorRequestModel
from app.runtime.live_node_executor import live_node_executor
from app.services.connection_readiness import check_workflow_readiness

@pytest.mark.asyncio
async def test_a_b_c_d_e_unbound_gmail_returns_http_401_error():
    """Test A-E: Verify GmailAdapter returns HTTP 401 error and never creates dev_local_token_placeholder or fake 200."""
    adapter = GmailAdapter()
    req = ConnectorRequestModel(
        operation_id="gmail.messages.list",
        parameters={"q": "label:invoices"},
        tenant_id="test_unbound_user_999",
    )
    res = await adapter.execute_operation(req, credentials=None)
    
    assert res.success is False
    assert res.status_code == 401
    assert "No valid Google OAuth token available" in res.error_message or "verification failed" in res.error_message
    assert res.data is None or res.data.get("HTTP_status") != 200

@pytest.mark.asyncio
async def test_f_g_ai_does_not_fabricate_summary_for_empty_upstream():
    """Test F-G: Verify LiveNodeExecutor AI summarize reports empty dataset when input is missing or template."""
    node = {
        "id": "step_2",
        "provider": "AI",
        "operation_id": "ai.summarize",
        "parameters": {"text": "{{step_1.output}}"}
    }
    res = await live_node_executor.execute_node(node, tenant_id="usr_1")
    assert res.status == "SUCCESS"
    assert "No messages or input data available" in res.response["body"]["summary"]
    assert "Email summary: The email contains details" not in res.response["body"]["summary"]

@pytest.mark.asyncio
async def test_h_ai_works_with_real_supplied_input():
    """Test H: Verify LiveNodeExecutor AI summarize works with real supplied input."""
    node = {
        "id": "step_2",
        "provider": "AI",
        "operation_id": "ai.summarize",
        "parameters": {"text": "Invoice #1234 from Acme Corp total $500."}
    }
    res = await live_node_executor.execute_node(node, tenant_id="usr_1")
    assert res.status == "SUCCESS"
    assert "Invoice #1234" in res.response["body"]["summary"]

@pytest.mark.asyncio
async def test_workflow_readiness_blocks_unbound_gmail():
    """Test K: Verify check_workflow_readiness marks unbound Gmail as MISSING_CONNECTION."""
    readiness = await check_workflow_readiness(["Gmail"], user_id="unbound_user_xyz")
    assert readiness["ready"] is False
    assert "Gmail" in readiness["missing_connections"]
