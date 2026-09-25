import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status

from app.core.response import success_response
from app.models.users import User
from app.security.rbac import require_permission
from app.security.audit import audit_logger, AuditEvent

logger = logging.getLogger("agentflow.api.v1.audit")
router = APIRouter(prefix="/audit-logs", tags=["Audit & Activity System"])


@router.get("", status_code=status.HTTP_200_OK)
async def get_audit_logs(
    action: Optional[str] = Query(None, description="Filter by event action (e.g., workflow.create)"),
    actor_id: Optional[str] = Query(None, description="Filter by actor user ID"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type (e.g., workflow, credential)"),
    event_status: Optional[str] = Query(None, alias="status", description="Filter by status (SUCCESS, FAILURE, DENIED)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_permission("audit.read")),
):
    """
    Retrieve sanitized audit trail events for organization and security auditing.
    Requires OWNER or ADMIN role (`audit.read` permission).
    """
    events = audit_logger.query(
        action=action,
        actor_id=actor_id,
        resource_type=resource_type,
        status=event_status,
        limit=limit,
        offset=offset,
    )

    data = [e.model_dump() for e in events]
    return success_response(
        data=data,
        message=f"Retrieved {len(data)} audit log event(s).",
    )
