import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserResponse
from app.schemas.users import UserProfileUpdateRequest, UserSettingsUpdateRequest, UserSettingsResponse
from app.core.exceptions import NotFoundException
from app.models.users import User

class UserService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)

    async def get_profile(self, user_id: uuid.UUID) -> UserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(message="User not found")
        return UserResponse.model_validate(user)

    async def update_profile(self, user_id: uuid.UUID, req: UserProfileUpdateRequest) -> UserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(message="User not found")
        
        updated = await self.user_repo.update(user, req.model_dump(exclude_unset=True))
        return UserResponse.model_validate(updated)

    async def get_settings(self, user_id: uuid.UUID) -> UserSettingsResponse:
        settings = await self.user_repo.get_settings(user_id)
        if not settings:
            settings = await self.user_repo.create_default_settings(user_id)
        return UserSettingsResponse.model_validate(settings)

    async def update_settings(self, user_id: uuid.UUID, req: UserSettingsUpdateRequest) -> UserSettingsResponse:
        settings = await self.user_repo.get_settings(user_id)
        if not settings:
            settings = await self.user_repo.create_default_settings(user_id)
        
        for key, val in req.model_dump(exclude_unset=True).items():
            setattr(settings, key, val)
        
        self.user_repo.db.add(settings)
        await self.user_repo.db.flush()
        return UserSettingsResponse.model_validate(settings)
