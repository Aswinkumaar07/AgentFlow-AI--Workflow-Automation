import pytest
import os
import asyncio
import time
from typing import Dict, Any

from app.runtime.workflow_executor import workflow_runtime_executor_v3, WorkflowRuntimeExecutorV3
from app.runtime.error_classifier import classify_error
from app.runtime.execution_history import execution_history_store
from app.runtime.execution_analytics import workflow_analytics_service, sanitize_telemetry_secrets
from app.services.workflow_scheduler import workflow_scheduler_service, WorkflowSchedulerService
from app.versions.manager import workflow_version_manager
from app.runtime.approval import human_approval_engine


@pytest.mark.asyncio
async def test_ai29_error_classifier_unit():
    # Retryable errors
    c1 = classify_error({"status_code": 500, "error": "Internal Server Error"})
    assert c1["retryable"] is True

    c2 = classify_error({"status_code": 429, "error": "Rate limit exceeded"})
    assert c2["retryable"] is True

    c3 = classify_error("Request timed out after 3000ms")
    assert c3["retryable"] is True

    # Non-retryable errors
    c4 = classify_error({"status_code": 400, "error": "Bad Request: missing param"})
    assert c4["retryable"] is False

    c5 = classify_error({"status_code": 401, "error": "Unauthorized: invalid OAuth token"})
    assert c5["retryable"] is False

    c6 = classify_error("Validation error: Invalid email format")
    assert c6["retryable"] is False


@pytest.mark.asyncio
async def test_ai29_retry_execution_suite():
    executor = WorkflowRuntimeExecutorV3()
    wf_id = "wf_ai29_test_suite"

    spec = {
        "workflow_id": wf_id,
        "nodes": [
            {
                "id": "step_1",
                "provider": "Slack",
                "operation_id": "slack.chat.postMessage",
                "parameters": {"text": "Hello world", "channel": "#general"},
                "retry": {"enabled": True, "max_attempts": 3, "delay_seconds": 0.01},
            }
        ],
        "edges": [],
    }

    # Scenario A: Success on first attempt
    call_count = {"cnt": 0}

    async def mock_first_success(n_id, attempt, payload):
        call_count["cnt"] += 1
        return {"status": "SUCCESS", "output": {"ok": True, "ts": "1234.56"}}

    state_a = await executor.execute_workflow(
        workflow_spec=spec,
        initial_context={"_mock_dispatch_fn": mock_first_success},
    )
    assert state_a.status in ["COMPLETED", "SUCCESS"]
    rec_a = state_a.node_records["step_1"]
    assert rec_a["attempts"] == 1
    assert rec_a["recovered_after_retry"] is False

    # Scenario B & C: Fail once/twice with 500, then succeed on 3rd attempt
    call_count_b = {"cnt": 0}

    async def mock_retry_then_succeed(n_id, attempt, payload):
        call_count_b["cnt"] += 1
        if attempt < 3:
            return {"status": "FAILED", "output": {"error": "HTTP 500 Internal Server Error", "code": 500}}
        return {"status": "SUCCESS", "output": {"ok": True, "ts": "9999.88"}}

    state_b = await executor.execute_workflow(
        workflow_spec=spec,
        initial_context={"_mock_dispatch_fn": mock_retry_then_succeed},
    )
    assert state_b.status in ["COMPLETED", "SUCCESS"]
    rec_b = state_b.node_records["step_1"]
    assert rec_b["attempts"] == 3
    assert rec_b["recovered_after_retry"] is True
    assert len(rec_b["attempts_history"]) == 3

    # Scenario D: Exhausted retries (all 3 fail with 503)
    async def mock_all_fail(n_id, attempt, payload):
        return {"status": "FAILED", "output": {"error": "HTTP 503 Service Unavailable", "code": 503}}

    state_d = await executor.execute_workflow(
        workflow_spec=spec,
        initial_context={"_mock_dispatch_fn": mock_all_fail},
    )
    assert state_d.status == "FAILED"
    rec_d = state_d.node_records["step_1"]
    assert rec_d["attempts"] == 3
    assert rec_d["exhausted_retries"] is True

    # Scenario E & F: Non-retryable error 400/401 (stops at attempt 1)
    call_count_e = {"cnt": 0}

    async def mock_non_retryable_401(n_id, attempt, payload):
        call_count_e["cnt"] += 1
        return {"status": "FAILED", "output": {"error": "HTTP 401 Unauthorized", "code": 401}}

    state_e = await executor.execute_workflow(
        workflow_spec=spec,
        initial_context={"_mock_dispatch_fn": mock_non_retryable_401},
    )
    assert state_e.status == "FAILED"
    assert call_count_e["cnt"] == 1
    rec_e = state_e.node_records["step_1"]
    assert rec_e["attempts"] == 1
    assert rec_e["retryable"] is False

    # Scenario I, J, K: Execution ID immutability & single analytics run count
    exec_id_original = state_b.execution_id
    assert exec_id_original.startswith("exec_v3_")

    # Analytics calculation verification
    analytics = await workflow_analytics_service.get_workflow_analytics(wf_id)
    summary = analytics["summary"]
    assert summary["total_retry_attempts"] >= 2
    assert summary["nodes_retried"] >= 2
    assert summary["successful_after_retry"] >= 1
    assert summary["exhausted_retries"] >= 1

    # Scenario M: Telemetry secret sanitization
    secret_test = {
        "access_token": "ya29.secret_token_value",
        "nested": {"api_key": "secret_key_123"},
        "normal": "public_data",
    }
    cleaned = sanitize_telemetry_secrets(secret_test)
    assert cleaned["access_token"] == "[REDACTED_SECRET]"
    assert cleaned["nested"]["api_key"] == "[REDACTED_SECRET]"
    assert cleaned["normal"] == "public_data"


@pytest.mark.asyncio
async def test_ai29_integrations_suite():
    executor = WorkflowRuntimeExecutorV3()

    # N: Human Approval + Retry compatibility
    wf_app = "wf_ai29_approval_retry"
    app_spec = {
        "workflow_id": wf_app,
        "nodes": [
            {"id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.list", "parameters": {}},
            {"id": "step_2", "provider": "Approval", "operation_id": "approval.wait", "parameters": {}, "dependencies": ["step_1"]},
            {"id": "step_3", "provider": "Slack", "operation_id": "slack.chat.postMessage", "parameters": {}, "dependencies": ["step_2"], "retry": {"enabled": True, "max_attempts": 2, "delay_seconds": 0.01}},
        ],
        "edges": [
            {"id": "e1", "source": "step_1", "target": "step_2"},
            {"id": "e2", "source": "step_2", "target": "step_3"},
        ],
    }

    state_app1 = await executor.execute_workflow(app_spec)
    assert state_app1.status in ["WAITING", "WAITING_FOR_APPROVAL"]
    exec_id_app = state_app1.execution_id

    # Approve
    await human_approval_engine.approve(exec_id_app, "step_2")

    async def mock_slack_recovered(n_id, attempt, payload):
        if n_id == "step_3" and attempt == 1:
            return {"status": "FAILED", "output": {"error": "HTTP 503 Service Unavailable", "code": 503}}
        return {"status": "SUCCESS", "output": {"ok": True}}

    resumed_app = await executor.execute_workflow(
        workflow_spec=app_spec,
        resume_execution_id=exec_id_app,
        initial_context={"_mock_dispatch_fn": mock_slack_recovered},
    )
    assert resumed_app.execution_id == exec_id_app
    assert resumed_app.status in ["COMPLETED", "SUCCESS"]
    assert resumed_app.node_records["step_3"]["attempts"] == 2
    assert resumed_app.node_records["step_3"]["recovered_after_retry"] is True

    # P: Conditional Branching + Retry compatibility
    wf_cond = "wf_ai29_cond_retry"
    cond_spec = {
        "workflow_id": wf_cond,
        "nodes": [
            {"id": "step_1", "provider": "Condition", "operation_id": "condition.if", "parameters": {"left": 10, "operator": ">", "right": 5, "true_branch": "step_2", "false_branch": "step_3"}},
            {"id": "step_2", "provider": "Slack", "operation_id": "slack.chat.postMessage", "parameters": {}, "dependencies": ["step_1"], "retry": {"enabled": True, "max_attempts": 2, "delay_seconds": 0.01}},
            {"id": "step_3", "provider": "Slack", "operation_id": "slack.chat.postMessage", "parameters": {}, "dependencies": ["step_1"]},
        ],
        "edges": [
            {"id": "e1", "source": "step_1", "target": "step_2"},
            {"id": "e2", "source": "step_1", "target": "step_3"},
        ],
    }

    def mock_cond_dispatch(n_id, attempt, payload):
        if n_id in ["step_2", "step_3"]:
            return {"status": "SUCCESS", "output": {"ok": True}}
        return None

    state_cond = await executor.execute_workflow(
        cond_spec,
        initial_context={"_mock_dispatch_fn": mock_cond_dispatch},
    )
    assert state_cond.status in ["COMPLETED", "SUCCESS"]
    assert "step_2" in state_cond.node_records
    assert state_cond.node_records["step_3"]["status"] == "SKIPPED"

    # S: Default non-configured workflow behaves unchanged
    wf_default = "wf_ai29_default"
    def_spec = {
        "workflow_id": wf_default,
        "nodes": [
            {"id": "step_1", "provider": "Slack", "operation_id": "slack.chat.postMessage", "parameters": {}},
        ],
        "edges": [],
    }
    cfg_def = executor._get_node_retry_config(def_spec["nodes"][0], def_spec)
    assert cfg_def["enabled"] is False
    assert cfg_def["max_attempts"] == 1
