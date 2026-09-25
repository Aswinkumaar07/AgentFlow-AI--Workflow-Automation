import pytest
import time
from app.analytics.engine import AnalyticsEngine, ExecutionRecord


def test_blocked_only_executions_accounting():
    """Test A & F: Blocked-only executions increment total & blocked_executions, with 0% success rate."""
    engine = AnalyticsEngine()
    t_now = time.time()

    rec1 = ExecutionRecord(execution_id="exec_b1", status="BLOCKED_MISSING_CONNECTION", timestamp=t_now)
    rec2 = ExecutionRecord(execution_id="exec_b2", status="BLOCKED", timestamp=t_now)
    engine._executions = [rec1, rec2]
    engine._get_all_executions = lambda: engine._executions

    metrics = engine.get_overview_metrics("7d")

    assert metrics["total_executions"] == 2
    assert metrics["successful_executions"] == 0
    assert metrics["failed_executions"] == 0
    assert metrics["blocked_executions"] == 2
    assert metrics["success_rate_pct"] == 0.0


def test_mixed_terminal_executions_accounting():
    """Test B: Mixed COMPLETED, FAILED, and BLOCKED_MISSING_CONNECTION executions."""
    engine = AnalyticsEngine()
    t_now = time.time()

    recs = [
        ExecutionRecord(execution_id="exec_c1", status="COMPLETED", timestamp=t_now),
        ExecutionRecord(execution_id="exec_c2", status="COMPLETED", timestamp=t_now),
        ExecutionRecord(execution_id="exec_f1", status="FAILED", timestamp=t_now),
        ExecutionRecord(execution_id="exec_b1", status="BLOCKED_MISSING_CONNECTION", timestamp=t_now),
    ]
    engine._executions = recs
    engine._get_all_executions = lambda: engine._executions

    metrics = engine.get_overview_metrics("7d")

    assert metrics["total_executions"] == 4
    assert metrics["successful_executions"] == 2
    assert metrics["failed_executions"] == 1
    assert metrics["blocked_executions"] == 1
    # eval_total = 2 + 1 + 1 = 4. success_rate = 2/4 = 50.0%
    assert metrics["success_rate_pct"] == 50.0


def test_waiting_running_non_terminal_executions_not_counted_as_failures_or_blocked():
    """Test C: WAITING and RUNNING in-flight executions do not penalize success rate or count as blocked."""
    engine = AnalyticsEngine()
    t_now = time.time()

    recs = [
        ExecutionRecord(execution_id="exec_c1", status="COMPLETED", timestamp=t_now),
        ExecutionRecord(execution_id="exec_w1", status="WAITING", timestamp=t_now),
        ExecutionRecord(execution_id="exec_r1", status="RUNNING", timestamp=t_now),
    ]
    engine._executions = recs
    engine._get_all_executions = lambda: engine._executions

    metrics = engine.get_overview_metrics("7d")

    assert metrics["total_executions"] == 3
    assert metrics["successful_executions"] == 1
    assert metrics["failed_executions"] == 0
    assert metrics["blocked_executions"] == 0
    assert metrics["success_rate_pct"] == 100.0


def test_failed_and_cancelled_execution_behavior_unchanged():
    """Test D & E: Existing FAILED and CANCELLED execution accounting preserved."""
    engine = AnalyticsEngine()
    t_now = time.time()

    recs = [
        ExecutionRecord(execution_id="exec_c1", status="COMPLETED", timestamp=t_now),
        ExecutionRecord(execution_id="exec_f1", status="FAILED", timestamp=t_now),
        ExecutionRecord(execution_id="exec_cx1", status="CANCELLED", timestamp=t_now),
    ]
    engine._executions = recs
    engine._get_all_executions = lambda: engine._executions

    metrics = engine.get_overview_metrics("7d")

    assert metrics["total_executions"] == 3
    assert metrics["successful_executions"] == 1
    assert metrics["failed_executions"] == 1
    assert metrics["cancelled_executions"] == 1
    assert metrics["blocked_executions"] == 0
    # eval_total = 1 + 1 = 2 -> 50.0%
    assert metrics["success_rate_pct"] == 50.0
