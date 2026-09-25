from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, status
from app.dependencies.auth import get_current_user
from app.models.users import User
from app.core.response import success_response
from app.agents.autonomous_agent import autonomous_agent_ai_service, AutonomousExecutionResult

router = APIRouter(prefix="/autonomous", tags=["Autonomous Workflow Agent Engine"])


class ExecuteGoalRequest(BaseModel):
    goal: str = Field(..., description="High-level outcome goal, e.g. 'Handle customer refunds automatically'")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


@router.post("/execute-goal", status_code=status.HTTP_200_OK)
async def execute_autonomous_goal(
    req: ExecuteGoalRequest,
    current_user: User = Depends(get_current_user),
):
    """Execute high-level outcome goal autonomously without predefined DAG templates."""
    result = autonomous_agent_ai_service.execute_goal(req.goal, req.context)
    return success_response(data=result.model_dump(), message="Autonomous goal executed successfully")


@router.post("/rollback", status_code=status.HTTP_200_OK)
async def rollback_autonomous_execution(
    req: AutonomousExecutionResult,
    current_user: User = Depends(get_current_user),
):
    """Rollback actions executed during autonomous outcome goal run."""
    rolled_back = autonomous_agent_ai_service.rollback(req)
    return success_response(data=rolled_back.model_dump(), message="Autonomous execution rolled back successfully")
