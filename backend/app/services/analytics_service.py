import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.workflow_repository import WorkflowRepository
from app.repositories.execution_repository import ExecutionRepository
from app.schemas.analytics import DashboardStatsResponse
from app.analytics.engine import analytics_engine


class AnalyticsService:
    def __init__(self, db: Optional[AsyncSession] = None):
        self.workflow_repo = WorkflowRepository(db) if db else None
        self.execution_repo = ExecutionRepository(db) if db else None

    async def get_dashboard_stats(self, user_id: uuid.UUID) -> DashboardStatsResponse:
        db_total_wfs = 0
        if self.workflow_repo:
            try:
                db_total_wfs = await self.workflow_repo.count_by_owner(user_id)
            except Exception:
                db_total_wfs = 0

        overview = analytics_engine.get_overview_metrics("7d")
        overview_24h = analytics_engine.get_overview_metrics("24h")
        connector_health = analytics_engine.get_connector_health()

        total_execs = overview["total_executions"]
        succ_execs = overview["successful_executions"]
        fail_execs = overview["failed_executions"]
        succ_rate = float(overview["success_rate_pct"])
        avg_dur = float(overview["avg_duration_ms"])

        active_wfs = overview["active_workflows"]
        total_wfs = max(db_total_wfs, active_wfs)

        api_calls_today = (
            sum(h["call_count"] for h in connector_health)
            if connector_health
            else overview_24h["total_executions"]
        )

        health_status = "operational"
        if total_execs > 0 and succ_rate < 90.0:
            health_status = "degraded"

        trend_list = []
        for b in overview.get("execution_trend", []):
            item = dict(b)
            item["day"] = b.get("timestamp", "")
            trend_list.append(item)

        return DashboardStatsResponse(
            total_workflows=total_wfs,
            active_workflows=active_wfs,
            total_executions=total_execs,
            successful_executions=succ_execs,
            failed_executions=fail_execs,
            success_rate_percentage=succ_rate,
            avg_execution_time_ms=avg_dur,
            api_calls_today=api_calls_today,
            system_health_status=health_status,
            execution_trend=trend_list,
        )
