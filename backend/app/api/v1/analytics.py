import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Query, Response, status
from app.analytics.engine import analytics_engine
from app.analytics.exporter import analytics_exporter
from app.runtime.execution_analytics import workflow_analytics_service
from app.core.response import success_response
from app.security.rbac import require_permission
from app.models.users import User

router = APIRouter(prefix="/analytics", tags=["Analytics & Monitoring"])
logger = logging.getLogger("agentflow.api.analytics")


class RecordExecutionRequest(BaseModel):
    execution_id: str
    workflow_name: str = "Workflow Execution"
    status: str = "COMPLETED"  # COMPLETED | FAILED | CANCELLED | ROLLED_BACK
    duration_ms: float = 0.0
    retries: int = 0
    steps: Optional[List[Dict[str, Any]]] = None


@router.get("/overview", status_code=status.HTTP_200_OK)
async def get_overview(
    time_frame: str = Query(default="7d"),
    current_user: User = Depends(require_permission("organization.read")),
):
    """Returns overview KPI metrics and execution trend data."""
    data = analytics_engine.get_overview_metrics(time_frame)
    return success_response(data=data, message="Overview metrics retrieved successfully")


@router.get("/connectors", status_code=status.HTTP_200_OK)
async def get_connector_health(
    current_user: User = Depends(require_permission("organization.read")),
):
    """Returns SLA health statistics and call counts for connected SaaS providers."""
    data = analytics_engine.get_connector_health()
    return success_response(data=data, message="Connector health metrics retrieved successfully")


@router.get("/insights", status_code=status.HTTP_200_OK)
async def get_ai_insights(
    current_user: User = Depends(require_permission("organization.read")),
):
    """Returns AI Optimization Insights generated from execution telemetry."""
    data = analytics_engine.get_ai_optimization_insights()
    return success_response(data=data, message="AI optimization insights retrieved successfully")


@router.get("/charts", status_code=status.HTTP_200_OK)
async def get_charts_data(
    time_frame: str = Query(default="7d"),
    current_user: User = Depends(require_permission("organization.read")),
):
    """Returns Recharts telemetry series data for latency and execution volume."""
    data = analytics_engine.get_charts_data(time_frame)
    return success_response(data=data, message="Analytics charts data retrieved successfully")


@router.get("/workflows", status_code=status.HTTP_200_OK)
async def get_workflow_analytics(
    current_user: User = Depends(require_permission("workflow.read")),
):
    """Returns real workflow execution breakdown for user workflows."""
    import os
    from app.runtime.execution_history import execution_history_store
    from app.runtime.execution_analytics import workflow_analytics_service
    from app.versions.manager import workflow_version_manager

    user_executions = await execution_history_store.list_user_executions("usr_1")
    wf_ids_from_history = {ex.workflow_id for ex in user_executions if ex.workflow_id}

    wf_ids_from_versions = set()
    versions_dir = workflow_version_manager._storage_dir
    if os.path.exists(versions_dir):
        try:
            for fname in os.listdir(versions_dir):
                if fname.endswith(".json"):
                    wf_id = fname[:-5]
                    wf_ids_from_versions.add(wf_id)
        except Exception:
            pass

    all_wf_ids = sorted(list(wf_ids_from_history | wf_ids_from_versions))

    result = []
    for wf_id in all_wf_ids:
        history = await workflow_version_manager.get_version_history(wf_id)
        latest_spec = history[0].workflow_spec if (history and len(history) > 0) else None
        wf_name = (
            (history[0].name if history and len(history) > 0 else None)
            or (latest_spec.get("name") or latest_spec.get("workflow_name") if latest_spec else None)
            or wf_id
        )

        analytics = await workflow_analytics_service.get_workflow_analytics(wf_id, workflow_spec=latest_spec)
        summary = analytics.get("summary", {})

        total_runs = summary.get("total_executions", 0)
        succ_rate = summary.get("success_rate")
        if succ_rate is None:
            succ_rate = 100.0 if total_runs == 0 else 0.0
        avg_lat = summary.get("average_duration_ms")
        if avg_lat is None:
            avg_lat = 0.0

        result.append({
            "workflow_id": wf_id,
            "name": wf_name,
            "total_runs": total_runs,
            "success_rate": round(float(succ_rate), 2),
            "avg_latency_ms": round(float(avg_lat), 1),
        })

    return success_response(data=result, message="Workflow analytics retrieved successfully")


@router.get("/advanced", status_code=status.HTTP_200_OK)
async def get_advanced_analytics(
    workflow_id: str = Query("all", description="Target workflow ID or 'all'"),
    version_id: Optional[str] = Query(None, description="Filter by workflow version ID"),
    time_frame: Optional[str] = Query("7d", description="Time window: 24h, 7d, 30d, 90d"),
    execution_status: Optional[str] = Query(None, alias="status", description="Filter by status: COMPLETED, FAILED, WAITING, CANCELLED, BLOCKED"),
    provider: Optional[str] = Query(None, description="Filter by provider: Gmail, Slack, GitHub, Drive, Notion, etc."),
    trigger_type: Optional[str] = Query(None, description="Filter by trigger: manual, scheduled, webhook, event"),
    current_user: User = Depends(require_permission("organization.read")),
):
    """
    AI-36 Extended Advanced Analytics Endpoint.
    Returns P50/P95 latencies, error trends, provider SLA, workflow health scores, and version comparison metrics.
    """
    data = await workflow_analytics_service.get_workflow_analytics(
        workflow_id=workflow_id,
        version_id=version_id,
        time_frame=time_frame,
        status=execution_status,
        provider=provider,
        trigger_type=trigger_type,
    )
    return success_response(data=data, message="Advanced analytics retrieved successfully")


@router.get("/export", status_code=status.HTTP_200_OK)
async def export_analytics_report(
    export_format: str = Query("csv", alias="format", description="Export format: csv or json"),
    workflow_id: str = Query("all"),
    version_id: Optional[str] = Query(None),
    time_frame: Optional[str] = Query("7d"),
    execution_status: Optional[str] = Query(None, alias="status"),
    provider: Optional[str] = Query(None),
    trigger_type: Optional[str] = Query(None),
    current_user: User = Depends(require_permission("organization.read")),
):
    """
    AI-36 Report Export Endpoint.
    Returns downloadable CSV or JSON file containing sanitized telemetry metrics.
    """
    data = await workflow_analytics_service.get_workflow_analytics(
        workflow_id=workflow_id,
        version_id=version_id,
        time_frame=time_frame,
        status=execution_status,
        provider=provider,
        trigger_type=trigger_type,
    )

    fmt = export_format.lower()
    if fmt == "json":
        content = analytics_exporter.export_json(data)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="analytics_report_{workflow_id}.json"'}
        )

    csv_content = analytics_exporter.export_csv(data)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="analytics_report_{workflow_id}.csv"'}
    )


@router.post("/record", status_code=status.HTTP_200_OK)
async def record_execution_telemetry(req: RecordExecutionRequest):
    """Records a live execution event into the telemetry analytics engine."""
    rec = analytics_engine.record_execution(
        execution_id=req.execution_id,
        workflow_name=req.workflow_name,
        status=req.status,
        duration_ms=req.duration_ms,
        retries=req.retries,
        steps=req.steps,
    )
    return success_response(data=rec.model_dump(), message="Execution telemetry recorded successfully")
