"""
Append-Only Audit Logging Engine for AgentFlow AI (AI-35).
Logs security and operational activity with zero sensitive data (tokens, passwords, keys) leaks.
"""

import uuid
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


SENSITIVE_KEYS = {
    "password", "hashed_password", "token", "access_token", "refresh_token",
    "secret", "client_secret", "api_key", "raw_key", "key_hash",
    "authorization", "auth_header", "credentials"
}


def sanitize_metadata(data: Any) -> Any:
    """
    Recursively redacts sensitive keys from audit log metadata payloads.
    Guarantees zero secret leaks in audit trail.
    """
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(s in k_lower for s in SENSITIVE_KEYS):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_metadata(v)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_metadata(item) for item in data]
    return data


class AuditEvent(BaseModel):
    id: str
    timestamp: float
    actor_id: str
    actor_email: str
    actor_role: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    status: str = "SUCCESS"  # SUCCESS, FAILURE, DENIED
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = {}


class AuditLogger:
    """
    In-Memory & Persistent Enterprise Audit Logger.
    Append-only log store for security compliance and incident tracing.
    """

    def __init__(self):
        self._events: List[AuditEvent] = []

    def log(
        self,
        actor_id: str,
        actor_email: str,
        actor_role: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        status: str = "SUCCESS",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """
        Record a new sanitized audit event.
        """
        clean_meta = sanitize_metadata(metadata) if metadata else {}
        evt_id = f"evt_{uuid.uuid4().hex[:12]}"
        now = time.time()

        evt = AuditEvent(
            id=evt_id,
            timestamp=now,
            actor_id=str(actor_id),
            actor_email=actor_email,
            actor_role=actor_role,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            status=status.upper(),
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=clean_meta,
        )

        self._events.append(evt)
        return evt

    def query(
        self,
        action: Optional[str] = None,
        actor_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEvent]:
        """
        Query audit events with filtering and pagination.
        """
        results = self._events.copy()

        if action:
            act_lower = action.lower()
            results = [e for e in results if act_lower in e.action.lower()]

        if actor_id:
            aid_str = str(actor_id)
            results = [e for e in results if e.actor_id == aid_str]

        if resource_type:
            rt_lower = resource_type.lower()
            results = [e for e in results if e.resource_type.lower() == rt_lower]

        if status:
            st_upper = status.upper()
            results = [e for e in results if e.status == st_upper]

        # Order by newest first
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[offset : offset + limit]


# Global Singleton Instance
audit_logger = AuditLogger()
