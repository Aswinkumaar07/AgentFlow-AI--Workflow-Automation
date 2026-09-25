import pytest
from app.agents.planner.gmail_search_query_builder import build_gmail_search_query
from app.agents.pipeline import agentflow_pipeline
from app.agents.validator.workflow_validator import workflow_validator


def test_search_query_from_email():
    """Test 1: Find emails from john@example.com -> from:john@example.com"""
    prompt = "Find emails from john@example.com"
    q = build_gmail_search_query(prompt)
    assert q == "from:john@example.com"


def test_search_query_unread():
    """Test 2: Find unread emails -> is:unread"""
    prompt = "Find unread emails"
    q = build_gmail_search_query(prompt)
    assert q == "is:unread"


def test_search_query_subject():
    """Test 3: Find emails with subject invoice -> subject:invoice"""
    prompt = "Find emails with subject invoice"
    q = build_gmail_search_query(prompt)
    assert "subject:invoice" in q or "invoice" in q


def test_search_query_unread_and_from():
    """Test 4: Find unread emails from john@example.com -> from:john@example.com is:unread"""
    prompt = "Find unread emails from john@example.com"
    q = build_gmail_search_query(prompt)
    assert "from:john@example.com" in q
    assert "is:unread" in q


def test_search_query_from_and_about():
    """Test 5: Find emails from john@example.com about invoices"""
    prompt = "Find emails from john@example.com about invoices"
    q = build_gmail_search_query(prompt)
    assert "from:john@example.com" in q
    assert "invoice" in q


def test_search_query_bitsathy_email():
    """Test 6: Find emails from aswinkumaarsr.cs24@bitsathy.ac.in -> from:aswinkumaarsr.cs24@bitsathy.ac.in"""
    prompt = "Find emails from aswinkumaarsr.cs24@bitsathy.ac.in"
    q = build_gmail_search_query(prompt)
    assert q == "from:aswinkumaarsr.cs24@bitsathy.ac.in"

    res = agentflow_pipeline.run(prompt)
    nodes = res.workflow_graph.get("nodes", [])
    assert len(nodes) >= 1
    node_1 = nodes[0]
    assert node_1.get("operation") in ["gmail.messages.search", "gmail.messages.list"]
    assert node_1.get("parameters", {}).get("q") == "from:aswinkumaarsr.cs24@bitsathy.ac.in"


def test_search_negative_constraint_no_side_effects():
    """Test 7: Negative constraint must not generate send/reply/forward/delete side-effect nodes."""
    prompt = "Find emails from john@example.com. Do not send, reply, forward, delete, or modify anything."
    res = agentflow_pipeline.run(prompt)
    nodes = res.workflow_graph.get("nodes", [])

    assert len(nodes) >= 1
    search_node = nodes[0]
    assert search_node.get("operation") in ["gmail.messages.search", "gmail.messages.list"]
    assert search_node.get("parameters", {}).get("q") == "from:john@example.com"

    op_ids = [n.get("operation") for n in nodes]
    forbidden_ops = [
        "gmail.messages.send",
        "gmail.messages.reply",
        "gmail.messages.forward",
        "gmail.messages.delete",
        "gmail.messages.mark_read",
        "gmail.messages.mark_unread",
    ]
    for forbidden in forbidden_ops:
        assert forbidden not in op_ids


def test_search_validation_guard_sanitizes_or_rejects_raw_prompt():
    """Test 8: Validation guard cleans natural language query parameter."""
    raw_graph = {
        "user_prompt": "Find emails from test@example.com",
        "nodes": [
            {
                "id": "step_1",
                "provider": "gmail",
                "operation": "gmail.messages.search",
                "parameters": {"q": "Find emails from test@example.com"},
            }
        ],
        "edges": [],
        "trigger": {"type": "manual"},
    }
    val_res = workflow_validator.validate_workflow(raw_graph)
    # The guard should clean q in parameters to from:test@example.com
    cleaned_q = raw_graph["nodes"][0]["parameters"]["q"]
    assert cleaned_q == "from:test@example.com"
    assert val_res.is_valid is True


@pytest.mark.asyncio
async def test_ai_generate_endpoint_returns_corrected_q():
    """Test 9: AI Generator API endpoint returns workflow_json containing corrected q parameter."""
    from app.api.v1.ai import generate_workflow
    from app.schemas.ai import AIGenerateRequest
    from app.models.users import User

    mock_user = User(id="usr_1", email="user@example.com")
    req = AIGenerateRequest(prompt="Find emails from aswinkumaarsr.cs24@bitsathy.ac.in")

    res = await generate_workflow(req=req, current_user=mock_user)
    data = res.get("data", {})
    wf_json = data.get("workflow_json", {})
    nodes = wf_json.get("nodes", [])

    assert len(nodes) >= 1
    node_1 = nodes[0]
    data_params = node_1.get("data", {}).get("parameters", {})
    root_params = node_1.get("parameters", {})

    assert data_params.get("q") == "from:aswinkumaarsr.cs24@bitsathy.ac.in"
    assert root_params.get("q") == "from:aswinkumaarsr.cs24@bitsathy.ac.in"


@pytest.mark.asyncio
async def test_e2e_generate_and_execute_flow():
    """Test 10: End-to-end API flow: prompt -> generate -> inspect DAG -> execute workflow."""
    from unittest.mock import AsyncMock, patch
    from app.api.v1.ai import generate_workflow
    from app.api.v1.runtime import execute_full_workflow_dag
    from app.schemas.ai import AIGenerateRequest
    from app.models.users import User
    from app.connectors.security.secret_manager import secret_manager
    from app.connectors.models import ConnectorCredentialModel

    cred = ConnectorCredentialModel(
        tenant_id="usr_1",
        provider="Google",
        auth_type="OAuth2",
        access_token="valid_access_token_123",
        account_label="aswinkumaarsr.cs24@bitsathy.ac.in",
    )
    await secret_manager.set_secret("usr_1", "Google", cred)

    mock_user = User(id="usr_1", email="user@example.com")
    prompt = "Find emails from aswinkumaarsr.cs24@bitsathy.ac.in"
    req = AIGenerateRequest(prompt=prompt)

    gen_res = await generate_workflow(req=req, current_user=mock_user)
    wf_spec = gen_res.get("data", {}).get("workflow_json", {})

    # Verify DAG parameters before execution
    node_1 = wf_spec["nodes"][0]
    q_param = node_1.get("data", {}).get("parameters", {}).get("q")
    assert q_param == "from:aswinkumaarsr.cs24@bitsathy.ac.in"

    # Execute workflow against adapter
    search_data = {"messages": [{"id": "msg_bitsathy_123", "threadId": "thread_bitsathy_123"}], "resultSizeEstimate": 1}
    mock_exec = AsyncMock(return_value=AsyncMock(status_code=200, success=True, data=search_data, error_message=None))

    with patch("app.runtime.node_executor.connector_manager.execute", mock_exec):
        exec_res = await execute_full_workflow_dag(wf_spec)

    assert exec_res.get("success") is True
    assert exec_res.get("status") == "COMPLETED"
    assert exec_res.get("nodes_executed") == len(exec_res.get("node_results", []))


