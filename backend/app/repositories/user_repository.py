import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.users import User, Session
from app.models.system import Settings
from app.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email, User.is_deleted == False)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_session(self, user_id: uuid.UUID, refresh_token: str, expires_at: any, user_agent: Optional[str] = None, ip_address: Optional[str] = None) -> Session:
        session = Session(
            user_id=user_id,
            refresh_token=refresh_token,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_settings(self, user_id: uuid.UUID) -> Optional[Settings]:
        stmt = select(Settings).where(Settings.user_id == user_id, Settings.is_deleted == False)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_default_settings(self, user_id: uuid.UUID) -> Settings:
        settings = Settings(user_id=user_id)
        self.db.add(settings)
        await self.db.flush()
        return settings
