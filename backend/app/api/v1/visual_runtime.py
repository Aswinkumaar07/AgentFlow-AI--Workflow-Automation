from typing import Any, Dict, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, status
from app.dependencies.auth import get_current_user
from app.models.users import User
from app.core.response import success_response
from app.agents.visual_runtime import visual_runtime_service

router = APIRouter(prefix="/visual-runtime", tags=["Visual Runtime Engine"])


class RecordNodeEventRequest(BaseModel):
    execution_id: str
    node_id: str
    status: str  # 'Pending', 'Running', 'Success', 'Failed', 'Waiting'
    latency_ms: int = 0
    retries: int = 0
    output_response: Optional[Dict[str, Any]] = None
    log_message: Optional[str] = None


@router.get("/timeline/{execution_id}", status_code=status.HTTP_200_OK)
async def get_execution_timeline(
    execution_id: str,
    current_user: User = Depends(get_current_user),
):
    """Retrieve visual execution timeline, step inspection data, and payload snapshots."""
    timeline = visual_runtime_service.get_timeline_snapshot(execution_id)
    return success_response(data=timeline.model_dump(), message="Execution timeline retrieved successfully")


@router.post("/record-event", status_code=status.HTTP_200_OK)
async def record_visual_node_event(
    req: RecordNodeEventRequest,
    current_user: User = Depends(get_current_user),
):
    """Record live node status animation event (Pending/Running/Success/Failed/Waiting)."""
    snapshot = visual_runtime_service.record_node_event(
        req.execution_id,
        req.node_id,
        req.status,
        req.latency_ms,
        req.retries,
        req.output_response,
        req.log_message,
    )
    return success_response(data=snapshot.model_dump(), message="Node execution event recorded successfully")
