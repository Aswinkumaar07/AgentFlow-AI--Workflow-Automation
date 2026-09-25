import uuid
from typing import Sequence, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workflows import WorkflowExecution, ExecutionLog
from app.repositories.base import BaseRepository

class ExecutionRepository(BaseRepository[WorkflowExecution]):
    def __init__(self, db: AsyncSession):
        super().__init__(WorkflowExecution, db)

    async def get_by_workflow(self, workflow_id: uuid.UUID, skip: int = 0, limit: int = 50) -> Sequence[WorkflowExecution]:
        stmt = (
            select(WorkflowExecution)
            .where(WorkflowExecution.workflow_id == workflow_id, WorkflowExecution.is_deleted == False)
            .order_by(WorkflowExecution.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_logs(self, execution_id: uuid.UUID) -> Sequence[ExecutionLog]:
        stmt = (
            select(ExecutionLog)
            .where(ExecutionLog.execution_id == execution_id, ExecutionLog.is_deleted == False)
            .order_by(ExecutionLog.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def add_log(self, execution_id: uuid.UUID, message: str, level: str = "INFO", node_id: Optional[str] = None, payload: Optional[dict] = None) -> ExecutionLog:
        log = ExecutionLog(
            execution_id=execution_id,
            node_id=node_id,
            level=level,
            message=message,
            payload=payload,
        )
        self.db.add(log)
        await self.db.flush()
        return log
