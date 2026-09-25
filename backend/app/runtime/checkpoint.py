import logging
import os
import json
import time
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field
from app.runtime.lifecycle import WorkflowLifecycleState

logger = logging.getLogger("agentflow.runtime.checkpoint")


class CheckpointSnapshotModel(BaseModel):
    execution_id: str
    workflow_id: str
    tenant_id: str = "usr_1"
    current_state: WorkflowLifecycleState = WorkflowLifecycleState.CREATED
    variables: Dict[str, Any] = Field(default_factory=dict)
    completed_nodes: List[str] = Field(default_factory=list)
    pending_nodes: List[str] = Field(default_factory=list)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    retries: Dict[str, int] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class CheckpointManager:
    """Enterprise Checkpoint Manager facilitating durable execution recovery across backend restarts."""

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        self._checkpoints: Dict[str, CheckpointSnapshotModel] = {}
        self._storage_dir = storage_dir or os.path.join(os.getcwd(), "storage", "checkpoints")
        os.makedirs(self._storage_dir, exist_ok=True)

    def _get_file_path(self, execution_id: str) -> str:
        safe_id = "".join(c for c in execution_id if c.isalnum() or c in ("_", "-"))
        return os.path.join(self._storage_dir, f"{safe_id}.json")

    async def save_checkpoint(
        self,
        execution_id: str,
        workflow_id: str,
        state: WorkflowLifecycleState,
        variables: Dict[str, Any],
        completed_nodes: Set[str],
        pending_nodes: List[str],
        outputs: Dict[str, Any],
        retries: Dict[str, int],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CheckpointSnapshotModel:
        snapshot = CheckpointSnapshotModel(
            execution_id=execution_id,
            workflow_id=workflow_id,
            current_state=state,
            variables=dict(variables),
            completed_nodes=list(completed_nodes),
            pending_nodes=list(pending_nodes),
            outputs=dict(outputs),
            retries=dict(retries),
            metadata=dict(metadata or {}),
        )
        self._checkpoints[execution_id] = snapshot
        try:
            os.makedirs(self._storage_dir, exist_ok=True)
            with open(self._get_file_path(execution_id), "w", encoding="utf-8") as f:
                f.write(snapshot.model_dump_json(indent=2))
        except Exception as exc:
            logger.warning(f"Failed to write checkpoint snapshot to disk for [{execution_id}]: {exc}")

        logger.debug(f"Saved durable checkpoint for execution [{execution_id}] at state [{state.value}].")
        return snapshot

    async def restore(self, execution_id: str) -> Optional[CheckpointSnapshotModel]:
        snapshot = self._checkpoints.get(execution_id)
        if not snapshot:
            file_path = self._get_file_path(execution_id)
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    snapshot = CheckpointSnapshotModel.model_validate(data)
                    self._checkpoints[execution_id] = snapshot
                    logger.info(f"Loaded durable checkpoint snapshot from disk for [{execution_id}].")
                except Exception as exc:
                    logger.warning(f"Failed to read checkpoint snapshot from disk for [{execution_id}]: {exc}")

        if snapshot:
            logger.info(f"Restored durable execution [{execution_id}] from node checkpoint ({len(snapshot.completed_nodes)} nodes completed).")
            return snapshot.model_copy(deep=True)
        return None


checkpoint_manager = CheckpointManager()
