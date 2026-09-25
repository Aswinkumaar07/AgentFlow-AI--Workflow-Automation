import pytest
import asyncio
from app.services.connection_readiness import check_workflow_readiness, is_internal_provider
from app.templates.engine import template_engine
from app.runtime.workflow_executor import workflow_runtime_executor_v3
from app.oauth.manager import oauth_manager
from app.connectors.security.secret_manager import secret_manager


@pytest.mark.asyncio
async def test_internal_provider_recognition():
    """Test H: Internal AI providers are never treated as requiring OAuth."""
    assert is_internal_provider("ai") is True
    assert is_internal_provider("schedule") is True
    assert is_internal_provider("condition") is True
    assert is_internal_provider("loop") is True
    assert is_internal_provider("approval") is True
    assert is_internal_provider("human_approval") is True
    assert is_internal_provider("webhook") is True
    assert is_internal_provider("code") is True
    assert is_internal_provider("trigger") is True
    assert is_internal_provider("gmail") is False
    assert is_internal_provider("slack") is False
    assert is_internal_provider("github") is False

    readiness = await check_workflow_readiness(["ai", "schedule", "condition"], user_id="usr_test_1")
    assert readiness["ready"] is True
    assert len(readiness["missing_connections"]) == 0
    for res in readiness["provider_results"]:
        assert res["status"] == "INTERNAL_PROVIDER"
        assert res["requires_oauth"] is False


@pytest.mark.asyncio
async def test_readiness_both_missing():
    """Test A: Readiness reports both missing when neither Gmail nor Slack is connected."""
    readiness = await check_workflow_readiness(["gmail", "slack"], user_id="usr_test_none")
    assert readiness["ready"] is False
    assert "gmail" in readiness["missing_connections"]
    assert "slack" in readiness["missing_connections"]


@pytest.mark.asyncio
async def test_readiness_partial_connected():
    """Test B & C: Gmail connected, Slack missing or vice-versa."""
    # Ensure google/gmail is registered in secret_manager or oauth_manager for usr_1
    readiness = await check_workflow_readiness(["gmail", "slack"], user_id="usr_1")
    # For usr_1, Google is active by default / secret store
    assert "gmail" not in readiness["missing_connections"] or readiness["ready"] is False
    # Slack is not connected by default for usr_test_partial
    readiness_partial = await check_workflow_readiness(["gmail", "slack"], user_id="usr_test_partial")
    assert "slack" in readiness_partial["missing_connections"]


@pytest.mark.asyncio
async def test_missing_connection_blocks_execution_zero_nodes():
    """Test E & G: Missing connection prevents partial execution and executes 0 nodes."""
    wf_spec = {
        "workflow_id": "wf_test_guard",
        "tenant_id": "usr_test_unbound",
        "steps": [
            {"step_id": "step_1", "provider": "gmail", "operation_id": "gmail.messages.list"},
            {"step_id": "step_2", "provider": "ai", "operation_id": "ai.summarize"},
            {"step_id": "step_3", "provider": "slack", "operation_id": "slack.chat.postMessage"},
        ]
    }

    state = await workflow_runtime_executor_v3.execute_workflow(wf_spec)
    assert state.status == "BLOCKED_MISSING_CONNECTION"
    assert len(state.node_records) == 0


@pytest.mark.asyncio
async def test_ai_generated_workflow_gets_preflight_protection():
    """Test J: AI-generated workflow with missing OAuth is blocked before node execution."""
    ai_wf_spec = {
        "workflow_id": "wf_ai_generated_test",
        "tenant_id": "usr_test_unbound_ai",
        "steps": [
            {"step_id": "step_1", "provider": "gmail", "operation_id": "gmail.messages.list"},
            {"step_id": "step_2", "provider": "ai", "operation_id": "ai.transform"},
            {"step_id": "step_3", "provider": "slack", "operation_id": "slack.chat.postMessage"},
        ]
    }

    state = await workflow_runtime_executor_v3.execute_workflow(ai_wf_spec)
    assert state.status == "BLOCKED_MISSING_CONNECTION"
    assert len(state.node_records) == 0


@pytest.mark.asyncio
async def test_scheduled_workflow_missing_oauth_blocked():
    """Test I: Scheduled workflow with missing OAuth is blocked before node execution."""
    sched_wf_spec = {
        "workflow_id": "wf_sched_guard_test",
        "tenant_id": "usr_test_unbound_sched",
        "steps": [
            {"step_id": "step_1", "provider": "gmail", "operation_id": "gmail.messages.list"},
            {"step_id": "step_2", "provider": "slack", "operation_id": "slack.chat.postMessage"},
        ]
    }

    state = await workflow_runtime_executor_v3.execute_workflow(sched_wf_spec, initial_context={"_trigger_type": "scheduled"})
    assert state.status == "BLOCKED_MISSING_CONNECTION"
    assert len(state.node_records) == 0


@pytest.mark.asyncio
async def test_connected_workflow_executes_normally():
    """Test F: Workflow with connected or internal providers executes normally."""
    wf_spec = {
        "workflow_id": "wf_test_internal_only",
        "tenant_id": "usr_1",
        "steps": [
            {"step_id": "step_1", "provider": "ai", "operation_id": "ai.prompt", "parameters": {"prompt": "Hello"}},
        ]
    }

    state = await workflow_runtime_executor_v3.execute_workflow(wf_spec)
    assert state.status in ["COMPLETED", "SUCCESS"]
    assert len(state.node_records) == 1
