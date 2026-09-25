import time
import logging
from typing import Any, Dict, List, Optional
from app.runtime.execution_history import execution_history_store
from app.runtime.state import WorkflowExecutionStateV2

logger = logging.getLogger("agentflow.runtime.execution_analytics")

SECRET_KEYWORDS = {
    "access_token",
    "refresh_token",
    "api_key",
    "apikey",
    "client_secret",
    "secret",
    "authorization",
    "auth",
    "bearer",
    "password",
    "cookie",
    "token",
}


def sanitize_telemetry_secrets(obj: Any) -> Any:
    """Recursively scrub sensitive keys and token values from telemetry data."""
    if isinstance(obj, dict):
        cleaned = {}
        for key, val in obj.items():
            key_lower = str(key).lower()
            if any(s in key_lower for s in SECRET_KEYWORDS):
                cleaned[key] = "[REDACTED_SECRET]"
            else:
                cleaned[key] = sanitize_telemetry_secrets(val)
        return cleaned
    elif isinstance(obj, list):
        return [sanitize_telemetry_secrets(item) for item in obj]
    elif isinstance(obj, str):
        if obj.lower().startswith("bearer ") or (len(obj) > 30 and ("ya29." in obj or "xoxb-" in obj or "xoxp-" in obj)):
            return "[REDACTED_SECRET]"
    return obj


def calculate_percentiles(values: List[float]) -> Dict[str, Optional[float]]:
    """Calculates exact P50 and P95 percentiles for a list of latency measurements."""
    if not values:
        return {"p50": None, "p95": None}
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    p50_idx = int(0.50 * (n - 1))
    p95_idx = int(0.95 * (n - 1))
    return {
        "p50": round(sorted_vals[p50_idx], 2),
        "p95": round(sorted_vals[p95_idx], 2),
    }


def classify_error_category(error_msg: str, status_code: Optional[int] = None) -> str:
    """Classifies execution or node errors into safe aggregated categories."""
    err = str(error_msg).lower()
    if "missing connection" in err or "connection required" in err or "unbound" in err or "oauth" in err:
        return "connection_required"
    elif status_code in (401, 403) or "unauthorized" in err or "permission" in err or "auth" in err:
        if "permission" in err or "forbidden" in err or status_code == 403:
            return "authorization"
        return "authentication"
    elif status_code == 404 or "not found" in err:
        return "not_found"
    elif status_code == 429 or "rate limit" in err or "too many requests" in err:
        return "rate_limit"
    elif "timeout" in err or "timed out" in err:
        return "timeout"
    elif "validation" in err or "invalid parameter" in err or status_code == 422:
        return "validation"
    elif "network" in err or "connection error" in err or "dns" in err:
        return "network"
    elif status_code and status_code >= 500 or "server error" in err:
        return "server_error"
    return "unknown"


def compute_workflow_health_score(
    total_executions: int,
    successful_executions: int,
    failed_executions: int,
    durations_ms: List[float],
    total_retries: int,
    blocked_missing_connections: int,
) -> Dict[str, Any]:
    """Deterministically computes workflow health score and explainable reasons without LLM calls."""
    if total_executions == 0:
        return {"status": "Healthy", "score": 100, "reasons": ["No execution history recorded yet."]}

    reasons = []
    eval_total = successful_executions + failed_executions
    success_rate = (successful_executions / eval_total) * 100.0 if eval_total > 0 else 100.0

    if failed_executions > 0:
        reasons.append(f"{failed_executions} failed execution(s) recorded out of {total_executions} total runs.")
    if blocked_missing_connections > 0:
        reasons.append(f"{blocked_missing_connections} execution(s) blocked due to missing connection(s).")
    if total_retries > 0:
        reasons.append(f"{total_retries} automatic step retry attempt(s) triggered.")

    percentiles = calculate_percentiles(durations_ms)
    p95 = percentiles.get("p95")
    if p95 and p95 > 1000:
        reasons.append(f"95th percentile latency is high: {p95}ms.")

    if success_rate >= 90.0 and blocked_missing_connections == 0 and failed_executions <= 1:
        status = "Healthy"
        score = int(success_rate)
        if not reasons:
            reasons.append("High success rate with stable execution latencies.")
    elif success_rate >= 70.0 or failed_executions <= 3:
        status = "At Risk"
        score = int(success_rate * 0.85)
    else:
        status = "Degraded"
        score = int(success_rate * 0.70)

    return {
        "status": status,
        "score": max(0, min(100, score)),
        "reasons": reasons,
    }


class WorkflowAnalyticsService:
    """Computes advanced workflow observability metrics derived from persisted ExecutionHistoryStore."""

    def __init__(self, history_store=None):
        self.history_store = history_store or execution_history_store

    async def get_workflow_analytics(
        self,
        workflow_id: str,
        workflow_spec: Optional[Dict[str, Any]] = None,
        version_id: Optional[str] = None,
        status: Optional[str] = None,
        provider: Optional[str] = None,
        trigger_type: Optional[str] = None,
        time_frame: Optional[str] = "7d",
    ) -> Dict[str, Any]:
        raw_executions = await self.history_store.list_workflow_executions(workflow_id)

        if workflow_id != "all":
            executions = [
                ex for ex in raw_executions
                if ex.workflow_id == workflow_id or ex.workflow_id.lower() == workflow_id.lower()
            ]
        else:
            executions = raw_executions

        # Apply Filters
        if version_id:
            executions = [ex for ex in executions if getattr(ex, "version_id", None) == version_id]

        if status:
            st_upper = status.upper()
            executions = [ex for ex in executions if (ex.status or "").upper() == st_upper]

        if trigger_type:
            tt_lower = trigger_type.lower()
            executions = [ex for ex in executions if (getattr(ex, "trigger_type", "manual") or "manual").lower() == tt_lower]

        if time_frame:
            now = time.time()
            tf_seconds = {"24h": 86400, "7d": 7 * 86400, "30d": 30 * 86400, "90d": 90 * 86400}.get(time_frame, 7 * 86400)
            cutoff = now - tf_seconds
            executions = [ex for ex in executions if ex.start_time and ex.start_time >= cutoff]

        total_executions = len(executions)

        if total_executions == 0:
            return {
                "workflow_id": workflow_id,
                "summary": {
                    "total_executions": 0,
                    "successful_executions": 0,
                    "failed_executions": 0,
                    "waiting_executions": 0,
                    "paused_executions": 0,
                    "cancelled_executions": 0,
                    "blocked_executions": 0,
                    "success_rate": None,
                    "average_duration_ms": None,
                    "p50_duration_ms": None,
                    "p95_duration_ms": None,
                    "latest_execution_at": None,
                    "oldest_execution_at": None,
                },
                "status_distribution": {"COMPLETED": 0, "FAILED": 0, "WAITING": 0, "PAUSED": 0, "CANCELLED": 0, "BLOCKED": 0},
                "health_score": {"status": "Healthy", "score": 100, "reasons": ["No executions matching filter."]},
                "provider_statistics": [],
                "node_statistics": [],
                "error_trends": [],
                "version_comparison": [],
                "recent_executions": [],
            }

        successful = 0
        failed = 0
        waiting = 0
        paused = 0
        cancelled = 0
        blocked = 0

        durations_ms = []
        timestamps = []

        status_counts: Dict[str, int] = {
            "COMPLETED": 0,
            "FAILED": 0,
            "WAITING": 0,
            "PAUSED": 0,
            "CANCELLED": 0,
            "BLOCKED": 0,
        }
        trigger_counts: Dict[str, int] = {
            "manual": 0,
            "scheduled": 0,
            "webhook": 0,
            "event": 0,
        }

        error_category_counts: Dict[str, int] = {}
        error_category_details: Dict[str, List[Dict[str, Any]]] = {}

        provider_stats_map: Dict[str, Dict[str, Any]] = {}
        node_stats_map: Dict[str, Dict[str, Any]] = {}
        version_stats_map: Dict[str, Dict[str, Any]] = {}

        step_meta_map: Dict[str, Dict[str, Any]] = {}
        if workflow_spec:
            steps = workflow_spec.get("steps") or workflow_spec.get("nodes") or []
            for s in steps:
                s_id = s.get("step_id") or s.get("id")
                if s_id:
                    s_data = s.get("data") if isinstance(s.get("data"), dict) else {}
                    prov = s.get("provider") or s_data.get("provider") or "Generic"
                    op_id = s.get("operation_id") or s.get("operation") or s_data.get("operation_id") or "generic.http.request"
                    step_meta_map[str(s_id)] = {"provider": prov, "operation_id": op_id}

        recent_executions = []

        total_retry_attempts = 0
        nodes_retried = 0
        successful_after_retry = 0
        exhausted_retries = 0

        loop_executions = 0
        loop_total_iterations = 0
        loop_failed_iterations = 0

        condition_evaluations = 0
        condition_true_branches = 0
        condition_false_branches = 0
        condition_skipped_branches = 0

        for ex in executions:
            st = (ex.status or "UNKNOWN").upper()

            if st in ["COMPLETED", "SUCCESS"]:
                successful += 1
                status_counts["COMPLETED"] = status_counts.get("COMPLETED", 0) + 1
            elif st in ["FAILED", "ERROR"]:
                failed += 1
                status_counts["FAILED"] = status_counts.get("FAILED", 0) + 1
            elif st in ["WAITING", "WAITING_FOR_APPROVAL"]:
                waiting += 1
                status_counts["WAITING"] = status_counts.get("WAITING", 0) + 1
            elif st in ["PAUSED"]:
                paused += 1
                status_counts["PAUSED"] = status_counts.get("PAUSED", 0) + 1
            elif st in ["CANCELLED"]:
                cancelled += 1
                status_counts["CANCELLED"] = status_counts.get("CANCELLED", 0) + 1
            elif st in ["BLOCKED_MISSING_CONNECTION", "BLOCKED"]:
                blocked += 1
                status_counts["BLOCKED"] = status_counts.get("BLOCKED", 0) + 1
            else:
                status_counts[st] = status_counts.get(st, 0) + 1

            # Version tracking
            ver_id = str(getattr(ex, "version_id", "v1"))
            ver_num = getattr(ex, "version_number", 1)
            if ver_id not in version_stats_map:
                version_stats_map[ver_id] = {
                    "version_id": ver_id,
                    "version_number": ver_num,
                    "total_runs": 0,
                    "successful_runs": 0,
                    "failed_runs": 0,
                    "durations": [],
                }
            v_stat = version_stats_map[ver_id]
            v_stat["total_runs"] += 1
            if st in ["COMPLETED", "SUCCESS"]:
                v_stat["successful_runs"] += 1
            elif st in ["FAILED", "ERROR"]:
                v_stat["failed_runs"] += 1

            if ex.start_time:
                timestamps.append(ex.start_time)

            dur_ms = None
            if ex.end_time and ex.start_time and ex.end_time >= ex.start_time:
                dur_ms = round((ex.end_time - ex.start_time) * 1000.0, 2)
            elif ex.node_records:
                total_lat = 0.0
                has_lat = False
                for nrec in ex.node_records.values():
                    lat = nrec.get("latency_ms") or nrec.get("latency")
                    if lat is not None:
                        has_lat = True
                        total_lat += float(lat)
                if has_lat and total_lat > 0:
                    dur_ms = round(total_lat, 2)

            if dur_ms is not None:
                durations_ms.append(dur_ms)
                v_stat["durations"].append(dur_ms)

            # Node Records & Provider Telemetry Processing
            node_recs = ex.node_records or {}
            for nid, rec in node_recs.items():
                nid_str = str(nid)
                prov_name = rec.get("provider") or step_meta_map.get(nid_str, {}).get("provider") or "Generic REST API"
                op_id = rec.get("operation") or rec.get("operation_id") or step_meta_map.get(nid_str, {}).get("operation_id") or "generic.http.request"

                # Filter by provider if specified
                if provider and provider.lower() not in prov_name.lower():
                    continue

                # Provider Stats
                if prov_name not in provider_stats_map:
                    provider_stats_map[prov_name] = {
                        "provider": prov_name,
                        "execution_count": 0,
                        "success_count": 0,
                        "failure_count": 0,
                        "durations": [],
                        "retries": 0,
                    }
                p_stat = provider_stats_map[prov_name]
                p_stat["execution_count"] += 1

                # Node Stats
                if nid_str not in node_stats_map:
                    node_stats_map[nid_str] = {
                        "node_id": nid_str,
                        "provider": prov_name,
                        "operation_id": op_id,
                        "execution_count": 0,
                        "success_count": 0,
                        "failure_count": 0,
                        "skipped_count": 0,
                        "durations": [],
                        "total_iterations": 0,
                        "successful_iterations": 0,
                        "failed_iterations": 0,
                        "retry_count": 0,
                        "recovered_count": 0,
                    }
                ns = node_stats_map[nid_str]
                ns["execution_count"] += 1

                n_status = (rec.get("status") or "").upper()
                if n_status in ["COMPLETED", "SUCCESS"]:
                    ns["success_count"] += 1
                    p_stat["success_count"] += 1
                elif n_status in ["FAILED", "ERROR"]:
                    ns["failure_count"] += 1
                    p_stat["failure_count"] += 1
                    # Error category tracking
                    err_msg = rec.get("error") or rec.get("error_message") or "Node execution failure"
                    code = rec.get("status_code")
                    cat = classify_error_category(err_msg, code)
                    error_category_counts[cat] = error_category_counts.get(cat, 0) + 1
                    error_category_details.setdefault(cat, []).append({
                        "node_id": nid_str,
                        "provider": prov_name,
                        "error": str(err_msg)[:150],
                        "execution_id": ex.execution_id,
                    })
                elif n_status in ["SKIPPED"]:
                    ns["skipped_count"] += 1

                n_attempts = rec.get("attempts") or len(rec.get("attempts_history", [])) or 1
                n_retries = max(0, n_attempts - 1)
                if n_retries > 0 or rec.get("recovered_after_retry") or rec.get("exhausted_retries"):
                    nodes_retried += 1
                    total_retry_attempts += n_retries
                    ns["retry_count"] += n_retries
                    p_stat["retries"] += n_retries

                if rec.get("recovered_after_retry") or (n_status in ["COMPLETED", "SUCCESS"] and n_retries > 0):
                    successful_after_retry += 1
                    ns["recovered_count"] += 1

                if rec.get("exhausted_retries"):
                    exhausted_retries += 1

                n_lat = rec.get("latency_ms") or rec.get("latency")
                if n_lat is not None:
                    try:
                        n_lat_f = float(n_lat)
                        ns["durations"].append(n_lat_f)
                        p_stat["durations"].append(n_lat_f)
                    except (ValueError, TypeError):
                        pass

                # Loop Telemetry
                out_obj = rec.get("output") or {}
                if isinstance(out_obj, dict) and "iterations" in out_obj:
                    iters = out_obj.get("iterations") or []
                    if isinstance(iters, list):
                        loop_executions += 1
                        loop_total_iterations += len(iters)
                        loop_failed_iterations += sum(1 for it in iters if isinstance(it, dict) and it.get("status") in ["FAILED", "ERROR"])
                        ns["total_iterations"] += len(iters)
                        ns["successful_iterations"] += sum(1 for it in iters if isinstance(it, dict) and it.get("status") in ["COMPLETED", "SUCCESS"])
                        ns["failed_iterations"] += sum(1 for it in iters if isinstance(it, dict) and it.get("status") in ["FAILED", "ERROR"])

                # Condition Telemetry
                if "condition" in prov_name.lower() or "condition" in op_id.lower() or "branch" in op_id.lower():
                    condition_evaluations += 1
                    cond_branch = (out_obj.get("selected_branch") or out_obj.get("result") or "").lower()
                    if cond_branch in ("true", "yes", "success"):
                        condition_true_branches += 1
                    elif cond_branch in ("false", "no"):
                        condition_false_branches += 1
                    else:
                        condition_skipped_branches += 1

            trig_t = getattr(ex, "trigger_type", "manual") or "manual"
            trigger_counts[trig_t] = trigger_counts.get(trig_t, 0) + 1

            total_nodes = len(step_meta_map) if step_meta_map else len(node_recs)
            rec_item = {
                "execution_id": ex.execution_id,
                "version_id": getattr(ex, "version_id", None),
                "version_number": getattr(ex, "version_number", None),
                "trigger_type": trig_t,
                "status": ex.status,
                "started_at": ex.start_time,
                "completed_at": ex.end_time,
                "duration_ms": dur_ms,
                "nodes_executed": len(node_recs),
                "total_nodes": max(total_nodes, len(node_recs)),
            }
            recent_executions.append(sanitize_telemetry_secrets(rec_item))

        # Overall Percentiles & Metrics
        eval_total = successful + failed
        success_rate = round((successful / eval_total) * 100.0, 1) if eval_total > 0 else (100.0 if total_executions > 0 and failed == 0 else 0.0)
        avg_duration_ms = round(sum(durations_ms) / len(durations_ms), 2) if durations_ms else None
        workflow_percentiles = calculate_percentiles(durations_ms)
        latest_execution_at = max(timestamps) if timestamps else None
        oldest_execution_at = min(timestamps) if timestamps else None

        # Health Score
        health_score = compute_workflow_health_score(
            total_executions=total_executions,
            successful_executions=successful,
            failed_executions=failed,
            durations_ms=durations_ms,
            total_retries=total_retry_attempts,
            blocked_missing_connections=blocked,
        )

        # Provider Statistics List
        provider_statistics = []
        for prov_name, ps in provider_stats_map.items():
            p_exec = ps["execution_count"]
            p_succ = ps["success_count"]
            p_fail = ps["failure_count"]
            p_eval = p_succ + p_fail
            p_sr = round((p_succ / p_eval) * 100.0, 1) if p_eval > 0 else 100.0
            p_avg = round(sum(ps["durations"]) / len(ps["durations"]), 2) if ps["durations"] else None
            p_perc = calculate_percentiles(ps["durations"])

            provider_statistics.append({
                "provider": prov_name,
                "execution_count": p_exec,
                "success_count": p_succ,
                "failure_count": p_fail,
                "success_rate": p_sr,
                "average_duration_ms": p_avg,
                "p50_duration_ms": p_perc.get("p50"),
                "p95_duration_ms": p_perc.get("p95"),
                "retries": ps["retries"],
            })
        provider_statistics.sort(key=lambda x: x["execution_count"], reverse=True)

        # Node Statistics List
        node_statistics = []
        for nid, ns in node_stats_map.items():
            exec_cnt = ns["execution_count"]
            succ_cnt = ns["success_count"]
            fail_cnt = ns["failure_count"]
            skip_cnt = ns["skipped_count"]
            dur_list = ns["durations"]
            avg_node_dur = round(sum(dur_list) / len(dur_list), 2) if dur_list else None
            n_perc = calculate_percentiles(dur_list)

            eval_count = succ_cnt + fail_cnt
            fail_rate = round((fail_cnt / eval_count) * 100.0, 1) if eval_count > 0 else 0.0

            n_item = {
                "node_id": nid,
                "provider": ns["provider"],
                "operation_id": ns["operation_id"],
                "execution_count": exec_cnt,
                "success_count": succ_cnt,
                "failure_count": fail_cnt,
                "skipped_count": skip_cnt,
                "retry_count": ns["retry_count"],
                "recovered_count": ns["recovered_count"],
                "average_duration_ms": avg_node_dur,
                "p50_duration_ms": n_perc.get("p50"),
                "p95_duration_ms": n_perc.get("p95"),
                "failure_rate": fail_rate,
            }
            if ns["total_iterations"] > 0:
                n_item["iterations"] = ns["total_iterations"]
                n_item["successful_iterations"] = ns["successful_iterations"]
                n_item["failed_iterations"] = ns["failed_iterations"]

            node_statistics.append(n_item)
        node_statistics.sort(key=lambda x: str(x["node_id"]))

        # Error Trends List
        error_trends = []
        total_errors = sum(error_category_counts.values())
        for cat, cnt in error_category_counts.items():
            pct = round((cnt / total_errors) * 100.0, 1) if total_errors > 0 else 0.0
            details = error_category_details.get(cat, [])
            affected_wfs = list({d.get("execution_id") for d in details if d.get("execution_id")})
            affected_nodes = list({d.get("node_id") for d in details if d.get("node_id")})

            error_trends.append({
                "category": cat,
                "count": cnt,
                "percentage": pct,
                "affected_workflows": affected_wfs[:5],
                "affected_nodes": affected_nodes[:5],
                "recent_occurrence": details[0].get("error") if details else None,
            })
        error_trends.sort(key=lambda x: x["count"], reverse=True)

        # Version Comparison List
        version_comparison = []
        for vid, vs in version_stats_map.items():
            v_runs = vs["total_runs"]
            v_succ = vs["successful_runs"]
            v_fail = vs["failed_runs"]
            v_eval = v_succ + v_fail
            v_sr = round((v_succ / v_eval) * 100.0, 1) if v_eval > 0 else 100.0
            v_avg = round(sum(vs["durations"]) / len(vs["durations"]), 2) if vs["durations"] else None
            v_perc = calculate_percentiles(vs["durations"])

            version_comparison.append({
                "version_id": vid,
                "version_number": vs["version_number"],
                "total_runs": v_runs,
                "successful_runs": v_succ,
                "failed_runs": v_fail,
                "success_rate": v_sr,
                "average_duration_ms": v_avg,
                "p50_duration_ms": v_perc.get("p50"),
                "p95_duration_ms": v_perc.get("p95"),
            })
        version_comparison.sort(key=lambda x: (x["version_number"] or 0), reverse=True)

        res_payload = {
            "workflow_id": workflow_id,
            "summary": {
                "total_executions": total_executions,
                "successful_executions": successful,
                "failed_executions": failed,
                "waiting_executions": waiting,
                "paused_executions": paused,
                "cancelled_executions": cancelled,
                "blocked_executions": blocked,
                "total_retry_attempts": total_retry_attempts,
                "nodes_retried": nodes_retried,
                "successful_after_retry": successful_after_retry,
                "exhausted_retries": exhausted_retries,
                "success_rate": success_rate,
                "average_duration_ms": avg_duration_ms,
                "p50_duration_ms": workflow_percentiles.get("p50"),
                "p95_duration_ms": workflow_percentiles.get("p95"),
                "latest_execution_at": latest_execution_at,
                "oldest_execution_at": oldest_execution_at,
                "trigger_distribution": trigger_counts,
            },
            "status_distribution": status_counts,
            "trigger_distribution": trigger_counts,
            "health_score": health_score,
            "provider_statistics": provider_statistics,
            "node_statistics": node_statistics,
            "error_trends": error_trends,
            "version_comparison": version_comparison,
            "loop_and_condition_analytics": {
                "loop_executions": loop_executions,
                "loop_total_iterations": loop_total_iterations,
                "loop_failed_iterations": loop_failed_iterations,
                "condition_evaluations": condition_evaluations,
                "condition_true_branches": condition_true_branches,
                "condition_false_branches": condition_false_branches,
                "condition_skipped_branches": condition_skipped_branches,
            },
            "recent_executions": recent_executions[:20],
        }

        return sanitize_telemetry_secrets(res_payload)


workflow_analytics_service = WorkflowAnalyticsService()
