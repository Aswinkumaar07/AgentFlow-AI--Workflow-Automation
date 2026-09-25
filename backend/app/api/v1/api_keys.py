import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.response import success_response
from app.dependencies.auth import get_current_user
from app.models.users import User
from app.security.rbac import require_permission, get_user_role
from app.security.api_keys import (
    api_key_manager,
    APIKeyCreatedResponse,
    APIKeyPublicResponse,
)
from app.security.audit import audit_logger

logger = logging.getLogger("agentflow.api.v1.api_keys")
router = APIRouter(prefix="/api-keys", tags=["API Key Lifecycle Management"])


class CreateAPIKeyRequest(BaseModel):
    name: str = Field(..., max_length=100, description="Friendly label for the API key")
    expires_in_days: Optional[int] = Field(30, ge=1, le=365, description="Expiration in days")


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_api_key(
    req: CreateAPIKeyRequest,
    request: Request,
    current_user: User = Depends(require_permission("api_key.create")),
):
    """
    Generate a new enterprise API key (`af_live_...`).
    The raw secret key is returned ONLY ONCE in this response.
    """
    user_id = str(current_user.id)
    user_role = get_user_role(current_user)

    meta, raw_key = api_key_manager.create_api_key(
        user_id=user_id,
        name=req.name,
        expires_in_days=req.expires_in_days,
    )

    audit_logger.log(
        actor_id=user_id,
        actor_email=current_user.email,
        actor_role=user_role,
        action="api_key.create",
        resource_type="api_key",
        resource_id=meta.id,
        status="SUCCESS",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"name": meta.name, "prefix": meta.prefix, "raw_key": raw_key},  # raw_key will be sanitized by audit logger!
    )

    resp = APIKeyCreatedResponse(
        id=meta.id,
        user_id=meta.user_id,
        name=meta.name,
        prefix=meta.prefix,
        created_at=meta.created_at,
        expires_at=meta.expires_at,
        last_used_at=meta.last_used_at,
        is_active=meta.is_active,
        raw_key=raw_key,
    )

    return success_response(
        data=resp.model_dump(),
        message="API Key created successfully. Store raw_key securely; it will not be shown again.",
    )


@router.get("", status_code=status.HTTP_200_OK)
async def list_api_keys(
    current_user: User = Depends(require_permission("api_key.read")),
):
    """
    List metadata for all API keys belonging to current user/tenant.
    Never returns raw secret keys or hashes.
    """
    user_id = str(current_user.id)
    keys = api_key_manager.list_api_keys(user_id)
    return success_response(
        data=[k.model_dump() for k in keys],
        message="API Keys metadata listed successfully.",
    )


@router.post("/{key_id}/rotate", status_code=status.HTTP_200_OK)
async def rotate_api_key(
    key_id: str,
    request: Request,
    current_user: User = Depends(require_permission("api_key.create")),
):
    """
    Revoke an existing API key and issue a new API key.
    The new raw secret key is returned ONLY ONCE.
    """
    user_id = str(current_user.id)
    user_role = get_user_role(current_user)

    res = api_key_manager.rotate_api_key(user_id, key_id)
    if not res:
        audit_logger.log(
            actor_id=user_id,
            actor_email=current_user.email,
            actor_role=user_role,
            action="api_key.rotate",
            resource_type="api_key",
            resource_id=key_id,
            status="FAILURE",
            metadata={"error": "API Key not found"},
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API Key '{key_id}' not found.",
        )

    meta, raw_key = res

    audit_logger.log(
        actor_id=user_id,
        actor_email=current_user.email,
        actor_role=user_role,
        action="api_key.rotate",
        resource_type="api_key",
        resource_id=meta.id,
        status="SUCCESS",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={"old_key_id": key_id, "new_key_id": meta.id, "raw_key": raw_key},
    )

    resp = APIKeyCreatedResponse(
        id=meta.id,
        user_id=meta.user_id,
        name=meta.name,
        prefix=meta.prefix,
        created_at=meta.created_at,
        expires_at=meta.expires_at,
        last_used_at=meta.last_used_at,
        is_active=meta.is_active,
        raw_key=raw_key,
    )

    return success_response(
        data=resp.model_dump(),
        message="API Key rotated successfully. Store new raw_key securely.",
    )


@router.delete("/{key_id}", status_code=status.HTTP_200_OK)
async def revoke_api_key(
    key_id: str,
    request: Request,
    current_user: User = Depends(require_permission("api_key.revoke")),
):
    """
    Revoke / deactivate an enterprise API key.
    """
    user_id = str(current_user.id)
    user_role = get_user_role(current_user)

    success = api_key_manager.revoke_api_key(user_id, key_id)
    if not success:
        audit_logger.log(
            actor_id=user_id,
            actor_email=current_user.email,
            actor_role=user_role,
            action="api_key.revoke",
            resource_type="api_key",
            resource_id=key_id,
            status="FAILURE",
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API Key '{key_id}' not found.",
        )

    audit_logger.log(
        actor_id=user_id,
        actor_email=current_user.email,
        actor_role=user_role,
        action="api_key.revoke",
        resource_type="api_key",
        resource_id=key_id,
        status="SUCCESS",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return success_response(
        data={"id": key_id, "revoked": True},
        message=f"API Key '{key_id}' revoked successfully.",
    )
