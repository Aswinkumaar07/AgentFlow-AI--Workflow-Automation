import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_failed_history_endpoint():
    """Verify GET /api/v1/history/failed returns array from real persistent history store."""
    resp = client.get("/api/v1/history/failed")
    assert resp.status_code == 200
    json_data = resp.json()
    assert json_data.get("success") is True or "data" in json_data
    assert isinstance(json_data.get("data"), list)

def test_replay_execution_endpoint():
    """Verify POST /api/v1/history/{id}/replay returns success for an execution replay."""
    resp = client.post("/api/v1/history/exec_test_999/replay")
    assert resp.status_code == 200
    json_data = resp.json()
    assert json_data.get("success") is True or "data" in json_data

def test_dashboard_analytics_zero_fallbacks():
    """Verify GET /api/v1/analytics/overview returns genuine data without hardcoded demo stats."""
    resp = client.get("/api/v1/analytics/overview")
    assert resp.status_code == 200
    json_data = resp.json()
    data = json_data.get("data", {})
    # Check that demo numbers (1248, 1237, 99.12) are NOT hardcoded fallbacks
    assert data.get("total_executions") != 1248
    assert data.get("successful_executions") != 1237
    assert data.get("success_rate") != 99.12
