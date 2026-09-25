import logging
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("agentflow.runtime.dlq")


class DLQRecordModel(BaseModel):
    id: str
    execution_id: str
    workflow: Dict[str, Any]
    node_id: str
    reason: str
    stacktrace: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)
    replayed: bool = False


class DeadLetterQueue:
    """Dead Letter Queue (DLQ) storing failed executions after max retries for inspection and manual replay."""

    def __init__(self) -> None:
        self._dlq_records: Dict[str, DLQRecordModel] = {}

    async def push_failed_execution(
        self,
        execution_id: str,
        workflow: Dict[str, Any],
        node_id: str,
        reason: str,
        stacktrace: Optional[str] = None,
    ) -> DLQRecordModel:
        dlq_id = f"dlq_{execution_id}_{node_id}"
        record = DLQRecordModel(
            id=dlq_id,
            execution_id=execution_id,
            workflow=workflow,
            node_id=node_id,
            reason=reason,
            stacktrace=stacktrace,
        )
        self._dlq_records[execution_id] = record
        logger.warning(f"Pushed failed execution [{execution_id}] at node [{node_id}] to Dead Letter Queue.")
        return record

    async def get_dlq_record(self, execution_id: str) -> Optional[DLQRecordModel]:
        return self._dlq_records.get(execution_id)

    async def replay(self, execution_id: str) -> Optional[DLQRecordModel]:
        record = self._dlq_records.get(execution_id)
        if record:
            record.replayed = True
            logger.info(f"Replay triggered for DLQ execution [{execution_id}].")
            return record
        return None


dead_letter_queue = DeadLetterQueue()
