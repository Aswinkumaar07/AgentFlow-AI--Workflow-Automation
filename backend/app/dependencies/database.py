from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import AsyncSessionLocal, engine
from app.models.base import Base

_db_initialized = False

async def get_db_session() -> AsyncGenerator[Optional[AsyncSession], None]:
    """Provides a database session."""
    global _db_initialized
    if not _db_initialized:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            _db_initialized = True
        except Exception:
            pass

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
