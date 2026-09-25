import uuid
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db_session
from app.dependencies.auth import get_current_user
from app.services.user_service import UserService
from app.schemas.users import UserProfileUpdateRequest
from app.schemas.auth import UserResponse
from app.models.users import User
from app.core.response import success_response
from app.security.rbac import require_permission, ALL_ROLES, get_user_role
from app.security.audit import audit_logger

router = APIRouter(prefix="/users", tags=["Users & Organization Management"])

# In-memory user role overrides store for testing & live user management
_USER_ROLES_STORE: Dict[str, str] = {
    "00000000-0000-0000-0000-000000000001": "OWNER",
}


class UpdateUserRoleRequest(BaseModel):
    role: str = Field(..., description="Target role: OWNER, ADMIN, MEMBER, VIEWER")


class UserOrgResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool


@router.get("/me", status_code=status.HTTP_200_OK)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Retrieve details for the currently authenticated user."""
    user_id_str = str(current_user.id)
    active_role = _USER_ROLES_STORE.get(user_id_str, get_user_role(current_user))

    user_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "avatar_url": current_user.avatar_url,
        "role": active_role,
    }
    return success_response(data=user_dict, message="Current user retrieved successfully")


@router.put("/profile", status_code=status.HTTP_200_OK)
async def update_user_profile(
    req: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update profile details for the authenticated user."""
    service = UserService(db)
    updated = await service.update_profile(current_user.id, req)
    return success_response(data=updated.model_dump(), message="Profile updated successfully")


@router.get("", status_code=status.HTTP_200_OK)
async def list_organization_users(
    current_user: User = Depends(require_permission("user.read"))
):
    """
    List all organization users and their assigned roles.
    Requires 'user.read' permission.
    """
    # Build list of active users including fallback user and session users
    primary_id = "00000000-0000-0000-0000-000000000001"
    users_list = [
        UserOrgResponse(
            id=primary_id,
            email="admin@agentflow.ai",
            full_name="Principal Architect",
            role=_USER_ROLES_STORE.get(primary_id, "OWNER"),
            is_active=True,
        )
    ]

    # Include any dynamically updated users
    for uid, role_val in _USER_ROLES_STORE.items():
        if uid != primary_id:
            users_list.append(
                UserOrgResponse(
                    id=uid,
                    email=f"user_{uid[:8]}@agentflow.ai",
                    full_name=f"Org User ({uid[:8]})",
                    role=role_val,
                    is_active=True,
                )
            )

    return success_response(
        data=[u.model_dump() for u in users_list],
        message="Organization users listed successfully.",
    )


@router.put("/{user_id}/role", status_code=status.HTTP_200_OK)
async def update_user_role(
    user_id: str,
    req: UpdateUserRoleRequest,
    request: Request,
    current_user: User = Depends(require_permission("user.role_assign")),
):
    """
    Update an organization user's role.
    Requires OWNER or ADMIN role ('user.role_assign' permission).
    """
    target_role = req.role.upper()
    if target_role not in ALL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{req.role}'. Must be one of: {ALL_ROLES}",
        )

    actor_id = str(current_user.id)
    actor_role = get_user_role(current_user)

    # Store role assignment
    _USER_ROLES_STORE[user_id] = target_role

    audit_logger.log(
        actor_id=actor_id,
        actor_email=current_user.email,
        actor_role=actor_role,
        action="user.role_assign",
        resource_type="user",
        resource_id=user_id,
        status="SUCCESS",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"assigned_role": target_role},
    )

    return success_response(
        data={"user_id": user_id, "role": target_role},
        message=f"User '{user_id}' role updated to '{target_role}'.",
    )


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_organization_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(require_permission("user.delete")),
):
    """
    Remove a user from the organization.
    Requires OWNER role ('user.delete' permission).
    """
    if user_id in ["00000000-0000-0000-0000-000000000001", str(current_user.id)]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete organization primary owner account.",
        )

    _USER_ROLES_STORE.pop(user_id, None)

    audit_logger.log(
        actor_id=str(current_user.id),
        actor_email=current_user.email,
        actor_role=get_user_role(current_user),
        action="user.delete",
        resource_type="user",
        resource_id=user_id,
        status="SUCCESS",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return success_response(
        data={"user_id": user_id, "deleted": True},
        message=f"User '{user_id}' removed from organization.",
    )
