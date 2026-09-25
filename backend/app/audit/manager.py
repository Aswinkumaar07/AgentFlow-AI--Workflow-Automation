import logging
import time
from typing import Any, Dict, List
from pydantic import BaseModel, Field

logger = logging.getLogger("agentflow.audit")


class AuditLogEntryModel(BaseModel):
    id: str
    action: str
    user_id: str = "usr_1"
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class AuditLogManager:
    """Enterprise Audit Log Manager recording all workspace security and operational events."""

    def __init__(self) -> None:
        self._logs: List[AuditLogEntryModel] = []

    async def log_action(self, action: str, user_id: str = "usr_1", details: Dict[str, Any] = None) -> AuditLogEntryModel:
        entry = AuditLogEntryModel(
            id=f"audit_{len(self._logs) + 1}",
            action=action,
            user_id=user_id,
            details=details or {},
        )
        self._logs.append(entry)
        logger.info(f"Audit Log recorded: [{action}] by [{user_id}].")
        return entry

    async def get_logs(self) -> List[AuditLogEntryModel]:
        return list(self._logs)


audit_log_manager = AuditLogManager()
