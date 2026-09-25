import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db_session
from app.dependencies.auth import get_current_user
from app.services.execution_service import ExecutionService
from app.schemas.workflows import WorkflowExecutionRequest
from app.models.users import User
from app.core.response import success_response
from app.security.rbac import require_permission

router = APIRouter(prefix="/executions", tags=["Executions"])

@router.post("/{workflow_id}/execute", status_code=status.HTTP_202_ACCEPTED)
async def execute_workflow(
    workflow_id: uuid.UUID,
    req: WorkflowExecutionRequest,
    current_user: User = Depends(require_permission("workflow.execute")),
    db: AsyncSession = Depends(get_db_session)
):
    """Trigger execution of a specified workflow pipeline."""
    service = ExecutionService(db)
    execution = await service.execute_workflow(current_user.id, workflow_id, req)
    return success_response(data=execution.model_dump(), message="Workflow execution initiated")

@router.post("/start")
async def start_workflow_execution(
    req: dict,
    current_user: User = Depends(require_permission("workflow.execute")),
):
    """Triggers DAG execution for Workflow Studio and returns complete execution telemetry."""
    from app.api.v1.runtime import execute_full_workflow_dag
    return await execute_full_workflow_dag(req)

@router.get("", status_code=status.HTTP_200_OK)
async def get_execution_history(
    workflow_id: Optional[uuid.UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_permission("execution.read")),
    db: AsyncSession = Depends(get_db_session)
):
    """List execution history across all user workflows or for a specific workflow."""
    service = ExecutionService(db)
    history = await service.get_execution_history(current_user.id, workflow_id=workflow_id, page=page, page_size=page_size)
    return success_response(data=history.model_dump(), message="Execution history retrieved successfully")

@router.get("/{execution_id}/logs", status_code=status.HTTP_200_OK)
async def get_execution_logs(
    execution_id: uuid.UUID,
    current_user: User = Depends(require_permission("execution.read")),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve detailed step-by-step telemetry logs for a specific workflow execution."""
    service = ExecutionService(db)
    logs = await service.get_execution_logs(current_user.id, execution_id)
    return success_response(data=[l.model_dump() for l in logs], message="Execution logs retrieved successfully")
