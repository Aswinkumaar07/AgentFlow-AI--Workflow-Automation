from typing import Any, Dict
from pydantic import BaseModel
from fastapi import APIRouter, Depends, status
from app.dependencies.auth import get_current_user
from app.models.users import User
from app.core.response import success_response
from app.agents.optimizer import optimizer_ai_service

router = APIRouter(prefix="/optimizer", tags=["AI Workflow Optimizer Engine"])


class OptimizeGraphRequest(BaseModel):
    graph: Dict[str, Any]


@router.post("/analyze", status_code=status.HTTP_200_OK)
async def analyze_workflow_optimization(
    req: OptimizeGraphRequest,
    current_user: User = Depends(get_current_user),
):
    """Analyze workflow DAG topology and calculate speedup, cost savings, and optimization scores."""
    result = optimizer_ai_service.analyze(req.graph)
    return success_response(data=result.model_dump(), message="Workflow optimization analysis completed successfully")


@router.post("/apply", status_code=status.HTTP_200_OK)
async def apply_one_click_optimization(
    req: OptimizeGraphRequest,
    current_user: User = Depends(get_current_user),
):
    """Apply one-click optimizations directly to the workflow DAG graph."""
    optimized_graph = optimizer_ai_service.apply_optimization(req.graph)
    return success_response(data=optimized_graph, message="One-click workflow optimization applied successfully")
