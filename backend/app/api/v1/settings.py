from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db_session
from app.dependencies.auth import get_current_user
from app.services.user_service import UserService
from app.schemas.users import UserSettingsUpdateRequest
from app.models.users import User
from app.core.response import success_response

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("", status_code=status.HTTP_200_OK)
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve user system configuration preferences."""
    service = UserService(db)
    settings_data = await service.get_settings(current_user.id)
    return success_response(data=settings_data.model_dump(), message="Settings retrieved successfully")

@router.put("", status_code=status.HTTP_200_OK)
async def update_user_settings(
    req: UserSettingsUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update user system preferences."""
    service = UserService(db)
    updated = await service.update_settings(current_user.id, req)
    return success_response(data=updated.model_dump(), message="Settings updated successfully")
