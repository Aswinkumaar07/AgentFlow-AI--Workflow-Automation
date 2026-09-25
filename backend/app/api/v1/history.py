import datetime
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db_session
from app.dependencies.auth import get_current_user
from app.models.users import User
from app.core.response import success_response
from app.runtime.execution_history import execution_history_store

router = APIRouter(prefix="/history", tags=["History"])

@router.get("", status_code=status.HTTP_200_OK)
async def get_recent_activity(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve recent workflow execution history telemetry."""
    all_states = await execution_history_store.list_user_executions("usr_1")
    sorted_states = sorted(all_states, key=lambda s: s.start_time, reverse=True)[:limit]
    
    history_data = []
    for s in sorted_states:
        providers = sorted(set(
            rec.get("provider", "Step")
            for rec in s.node_records.values()
            if isinstance(rec, dict) and rec.get("provider")
        ))
        provider_str = ", ".join(providers) if providers else "Generic"
        
        executed_at_iso = datetime.datetime.fromtimestamp(s.start_time, datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        duration_ms = round((s.end_time - s.start_time) * 1000.0, 2) if (s.end_time and s.end_time >= s.start_time) else 0.0
        
        history_data.append({
            "id": s.execution_id,
            "workflow_name": f"Workflow {s.workflow_id}",
            "provider": provider_str,
            "status": s.status,
            "executed_at": executed_at_iso,
            "duration_ms": duration_ms,
            "steps_count": len(s.node_records),
        })
        
    return success_response(data=history_data, message="Recent execution history retrieved successfully")


@router.get("/failed", status_code=status.HTTP_200_OK)
async def get_failed_history():
    """Retrieve all failed workflow executions from real persistent history store."""
    from app.runtime.execution_history import execution_history_store
    all_states = await execution_history_store.list_user_executions("usr_1")
    failed_states = [s for s in all_states if s.status == "FAILED"]
    out = []
    for s in failed_states:
        failed_node = None
        err_msg = "Execution failed"
        for nid, rec in s.node_records.items():
            if isinstance(rec, dict) and rec.get("status") == "FAILED":
                failed_node = f"{nid} ({rec.get('provider', 'Step')})"
                err_msg = rec.get("error") or err_msg
                break
        
        out.append({
            "id": s.execution_id,
            "execution_id": s.execution_id,
            "workflow_id": s.workflow_id,
            "version_id": s.version_id,
            "version_number": s.version_number,
            "workflow_name": f"Workflow {s.workflow_id}",
            "failed_node": failed_node or "Node Step Failure",
            "reason": err_msg,
            "error": err_msg,
            "status": s.status,
            "timestamp": s.start_time,
            "retries": sum(rec.get("attempts", 1) - 1 for rec in s.node_records.values() if isinstance(rec, dict)),
            "stack_trace": f"Error: {err_msg}\n  Execution ID: {s.execution_id}\n  Workflow ID: {s.workflow_id}",
            "node_records": s.node_records,
        })
    return success_response(data=out, message="Failed execution history retrieved successfully")


@router.post("/{execution_id}/replay", status_code=status.HTTP_200_OK)
async def replay_failed_execution_history(execution_id: str):
    """Replays a failed execution using canonical runtime engine resume."""
    from app.services.runtime_service import perform_canonical_resume
    result = await perform_canonical_resume(execution_id)

    if not result.get("success") and result.get("status") == "NOT_FOUND":
        return success_response(
            data={"replayed": False, "execution_id": execution_id, "status": "NOT_FOUND"},
            message=f"Execution state [{execution_id}] not found or missing checkpoint."
        )

    return success_response(
        data=result,
        message=f"Replayed execution [{execution_id}] through runtime engine."
    )
