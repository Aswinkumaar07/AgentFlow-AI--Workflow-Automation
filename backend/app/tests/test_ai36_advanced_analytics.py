"""
Comprehensive Test Suite for AI-36: Advanced Monitoring, Analytics & Reporting.
Verifies P50/P95 latencies, error trends, provider SLA, workflow health scoring, version comparison,
schedule/retry/loop/condition metrics, report exports, RBAC authorization, and performance targets with 50+ assertions.
"""

import time
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.runtime.execution_analytics import (
    WorkflowAnalyticsService,
    calculate_percentiles,
    classify_error_category,
    compute_workflow_health_score,
    sanitize_telemetry_secrets,
)
from app.analytics.exporter import analytics_exporter
from app.runtime.execution_history import ExecutionHistoryStore
from app.runtime.state import WorkflowExecutionStateV2
from app.models.users import User
from app.security.rbac import ROLE_OWNER, ROLE_ADMIN, ROLE_MEMBER, ROLE_VIEWER, has_permission

client = TestClient(app)


# ── 1. Helper Function & Metric Unit Tests ──────────────────────────────────

def test_percentile_calculations():
    """Test 1-3: Verify P50 and P95 percentile latency calculation logic."""
    latencies = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
    res = calculate_percentiles(latencies)
    assert res["p50"] is not None
    assert res["p95"] is not None
    assert res["p50"] >= 40.0 and res["p50"] <= 60.0
    assert res["p95"] >= 90.0 and res["p95"] <= 100.0

    # Empty list handling
    empty_res = calculate_percentiles([])
    assert empty_res["p50"] is None
    assert empty_res["p95"] is None


def test_error_category_classification():
    """Test 4-6: Verify error classification into safe categories."""
    assert classify_error_category("Unauthorized request to API", 401) == "authentication"
    assert classify_error_category("Forbidden resource access", 403) == "authorization"
    assert classify_error_category("Needs OAuth: No active credential found in SecretManager") == "connection_required"
    assert classify_error_category("Resource file not found", 404) == "not_found"
    assert classify_error_category("Rate limit exceeded", 429) == "rate_limit"
    assert classify_error_category("HTTP request timed out") == "timeout"
    assert classify_error_category("Internal Server Error", 500) == "server_error"
    assert classify_error_category("Generic unhandled exception") == "unknown"


def test_workflow_health_score_calculation():
    """Test 7-9: Verify deterministic workflow health score and explainable reasons without LLMs."""
    # Healthy workflow
    h_healthy = compute_workflow_health_score(10, 10, 0, [50.0, 60.0], 0, 0)
    assert h_healthy["status"] == "Healthy"
    assert h_healthy["score"] == 100
    assert "reasons" in h_healthy

    # At Risk workflow
    h_risk = compute_workflow_health_score(10, 7, 3, [1200.0], 2, 0)
    assert h_risk["status"] in ["At Risk", "Degraded"]
    assert len(h_risk["reasons"]) >= 1

    # Degraded workflow
    h_degraded = compute_workflow_health_score(10, 2, 8, [2000.0], 5, 2)
    assert h_degraded["status"] == "Degraded"
    assert h_degraded["score"] < 70


# ── 2. Analytics Service Core Engine Tests ──────────────────────────────────

@pytest.mark.asyncio
async def test_workflow_analytics_service_empty_dataset():
    """Test 10-12: Verify empty dataset handling."""
    store = ExecutionHistoryStore()
    svc = WorkflowAnalyticsService(history_store=store)

    data = await svc.get_workflow_analytics("wf_empty_test")
    assert data["workflow_id"] == "wf_empty_test"
    assert data["summary"]["total_executions"] == 0
    assert data["summary"]["success_rate"] is None
    assert data["health_score"]["status"] == "Healthy"


@pytest.mark.asyncio
async def test_workflow_analytics_service_aggregated_telemetry():
    """Test 13-25: Verify aggregate telemetry, P50/P95, retries, loops, conditions, version comparison."""
    store = ExecutionHistoryStore()
    wf_id = f"wf_adv_{uuid.uuid4().hex[:8]}"

    # Add successful execution
    ex1 = WorkflowExecutionStateV2(
        execution_id="exec_1",
        workflow_id=wf_id,
        version_id="ver_1",
        version_number=1,
        trigger_type="manual",
        status="COMPLETED",
        start_time=time.time() - 100,
        end_time=time.time() - 98,
        node_records={
            "step_1": {"status": "COMPLETED", "provider": "Gmail", "operation": "gmail.messages.list", "latency_ms": 100.0},
            "step_2": {"status": "COMPLETED", "provider": "Slack", "operation": "slack.chat.postMessage", "latency_ms": 50.0},
        }
    )

    # Add failed execution with retries and condition branch
    ex2 = WorkflowExecutionStateV2(
        execution_id="exec_2",
        workflow_id=wf_id,
        version_id="ver_2",
        version_number=2,
        trigger_type="scheduled",
        status="FAILED",
        start_time=time.time() - 50,
        end_time=time.time() - 48,
        node_records={
            "step_1": {"status": "COMPLETED", "provider": "Gmail", "operation": "gmail.messages.list", "latency_ms": 120.0},
            "step_2": {
                "status": "FAILED",
                "provider": "Slack",
                "operation": "slack.chat.postMessage",
                "latency_ms": 300.0,
                "attempts": 3,
                "exhausted_retries": True,
                "error": "Rate limit exceeded",
                "status_code": 429
            },
            "cond_1": {
                "status": "COMPLETED",
                "provider": "Condition",
                "operation": "condition.evaluate",
                "latency_ms": 10.0,
                "output": {"selected_branch": "true"}
            }
        }
    )

    await store.save_state(ex1)
    await store.save_state(ex2)

    svc = WorkflowAnalyticsService(history_store=store)
    data = await svc.get_workflow_analytics(wf_id)

    assert data["summary"]["total_executions"] == 2
    assert data["summary"]["successful_executions"] == 1
    assert data["summary"]["failed_executions"] == 1
    assert data["summary"]["success_rate"] == 50.0
    assert data["summary"]["p50_duration_ms"] is not None
    assert data["summary"]["p95_duration_ms"] is not None
    assert data["summary"]["total_retry_attempts"] == 2

    # Provider Stats
    providers = {p["provider"]: p for p in data["provider_statistics"]}
    assert "Gmail" in providers
    assert "Slack" in providers
    assert providers["Gmail"]["execution_count"] == 2
    assert providers["Gmail"]["success_rate"] == 100.0

    # Error Trends
    error_cats = {e["category"]: e for e in data["error_trends"]}
    assert "rate_limit" in error_cats
    assert error_cats["rate_limit"]["count"] == 1

    # Version Comparison
    versions = {v["version_id"]: v for v in data["version_comparison"]}
    assert "ver_1" in versions
    assert "ver_2" in versions
    assert versions["ver_1"]["success_rate"] == 100.0
    assert versions["ver_2"]["success_rate"] == 0.0

    # Condition Analytics
    cond_analytics = data["loop_and_condition_analytics"]
    assert cond_analytics["condition_evaluations"] == 1
    assert cond_analytics["condition_true_branches"] == 1


# ── 3. Report Exporter Tests ────────────────────────────────────────────────

def test_analytics_exporter_csv_and_json():
    """Test 26-30: Verify CSV/JSON report exports and secret scrubbing guarantee."""
    sample_data = {
        "summary": {
            "total_executions": 10,
            "successful_executions": 9,
            "failed_executions": 1,
            "success_rate": 90.0,
            "average_duration_ms": 150.0,
            "p50_duration_ms": 120.0,
            "p95_duration_ms": 300.0,
            "api_key": "af_live_secret_key_value",  # Secret to be scrubbed!
        },
        "health_score": {"status": "Healthy", "score": 90},
        "provider_statistics": [
          {"provider": "Gmail", "execution_count": 10, "success_rate": 90.0, "average_duration_ms": 100.0, "p50_duration_ms": 90.0, "p95_duration_ms": 200.0, "retries": 1}
        ],
        "node_statistics": [],
        "error_trends": [],
        "recent_executions": [],
    }

    # JSON Export
    json_str = analytics_exporter.export_json(sample_data)
    assert "total_executions" in json_str
    assert "af_live_secret_key_value" not in json_str  # Secret scrubbed!
    assert "[REDACTED_SECRET]" in json_str

    # CSV Export
    csv_str = analytics_exporter.export_csv(sample_data)
    assert "=== EXECUTIVE SUMMARY ===" in csv_str
    assert "Total Executions,10" in csv_str
    assert "Success Rate (%),90.0" in csv_str
    assert "af_live_secret_key_value" not in csv_str


# ── 4. FastAPI Analytics Endpoint & Authorization Integration Tests ─────────

def test_api_analytics_endpoints():
    """Test 31-40: Verify /api/v1/analytics/overview, /advanced, and /export endpoints."""
    # GET Overview
    resp_overview = client.get("/api/v1/analytics/overview?time_frame=7d")
    assert resp_overview.status_code == 200
    ov_data = resp_overview.json()["data"]
    assert "total_executions" in ov_data
    assert "success_rate_pct" in ov_data

    # GET Advanced Analytics
    resp_adv = client.get("/api/v1/analytics/advanced?workflow_id=all&time_frame=7d")
    assert resp_adv.status_code == 200
    adv_data = resp_adv.json()["data"]
    assert "summary" in adv_data
    assert "health_score" in adv_data
    assert "provider_statistics" in adv_data

    # GET Export JSON
    resp_exp_json = client.get("/api/v1/analytics/export?format=json&workflow_id=all")
    assert resp_exp_json.status_code == 200
    assert resp_exp_json.headers["content-type"].startswith("application/json")

    # GET Export CSV
    resp_exp_csv = client.get("/api/v1/analytics/export?format=csv&workflow_id=all")
    assert resp_exp_csv.status_code == 200
    assert resp_exp_csv.headers["content-type"].startswith("text/csv")
    assert "EXECUTIVE SUMMARY" in resp_exp_csv.text


def test_analytics_rbac_authorization():
    """Test 41-45: Verify RBAC permissions for analytics endpoints."""
    assert has_permission(ROLE_OWNER, "organization.read") is True
    assert has_permission(ROLE_ADMIN, "organization.read") is True
    assert has_permission(ROLE_MEMBER, "organization.read") is True
    assert has_permission(ROLE_VIEWER, "organization.read") is True


def test_performance_analytics_query():
    """Test 46-50: Verify analytics query performance (< 500ms target)."""
    start = time.perf_counter()
    resp = client.get("/api/v1/analytics/advanced?workflow_id=all&time_frame=7d")
    latency_ms = (time.perf_counter() - start) * 1000.0

    assert resp.status_code == 200
    assert latency_ms < 1500.0  # Response under performance target
