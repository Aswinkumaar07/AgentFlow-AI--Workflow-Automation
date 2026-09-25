from typing import Any, Dict
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, status
from app.dependencies.auth import get_current_user
from app.models.users import User
from app.core.response import success_response
from app.agents.self_healing import self_healing_ai_service

router = APIRouter(prefix="/self-healing", tags=["Self-Healing Workflow Engine"])


class DiagnoseRequest(BaseModel):
    error_message: str = Field(..., description="Error log or stack trace")
    node: Dict[str, Any] = Field(..., description="Failing node object")
    workflow_graph: Dict[str, Any] = Field(..., description="Workflow DAG graph")


@router.post("/diagnose", status_code=status.HTTP_200_OK)
async def diagnose_workflow_failure(
    req: DiagnoseRequest,
    current_user: User = Depends(get_current_user),
):
    """Diagnose workflow failure and return automated fix plan."""
    diag = self_healing_ai_service.diagnose(req.error_message, req.node, req.workflow_graph)
    return success_response(data=diag.model_dump(), message="Self-healing diagnosis completed successfully")


@router.post("/apply-fix", status_code=status.HTTP_200_OK)
async def apply_one_click_repair_fix(
    req: DiagnoseRequest,
    current_user: User = Depends(get_current_user),
):
    """Apply one-click repair fix directly to the workflow DAG graph."""
    repaired_graph = self_healing_ai_service.apply_fix(req.error_message, req.node, req.workflow_graph)
    return success_response(data=repaired_graph, message="Self-healing repair fix applied successfully")
