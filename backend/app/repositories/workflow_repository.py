import uuid
from typing import Sequence, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workflows import Workflow
from app.repositories.base import BaseRepository

class WorkflowRepository(BaseRepository[Workflow]):
    def __init__(self, db: AsyncSession):
        super().__init__(Workflow, db)

    async def get_by_owner(self, owner_id: uuid.UUID, skip: int = 0, limit: int = 100) -> Sequence[Workflow]:
        stmt = (
            select(Workflow)
            .where(Workflow.owner_id == owner_id, Workflow.is_deleted == False)
            .order_by(Workflow.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def count_by_owner(self, owner_id: uuid.UUID) -> int:
        stmt = select(func.count(Workflow.id)).where(Workflow.owner_id == owner_id, Workflow.is_deleted == False)
        result = await self.db.execute(stmt)
        return result.scalar_one()
