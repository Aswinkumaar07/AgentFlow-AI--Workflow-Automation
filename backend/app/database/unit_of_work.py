from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import AsyncSessionLocal
from app.repositories.user_repository import UserRepository
from app.repositories.workflow_repository import WorkflowRepository
from app.repositories.execution_repository import ExecutionRepository

class UnitOfWork:
    """
    Unit of Work Pattern for managing atomic database transactions across multiple repositories.
    Ensures that all operations within a service workflow commit or rollback together.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.workflows = WorkflowRepository(session)
        self.executions = ExecutionRepository(session)

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

async def get_unit_of_work() -> AsyncGenerator[UnitOfWork, None]:
    async with AsyncSessionLocal() as session:
        uow = UnitOfWork(session)
        try:
            yield uow
            await uow.commit()
        except Exception:
            await uow.rollback()
            raise
        finally:
            await session.close()
