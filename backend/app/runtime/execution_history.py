import logging
import os
import json
import time
from typing import Dict, List, Optional
from app.runtime.state import WorkflowExecutionStateV2

logger = logging.getLogger("agentflow.runtime.execution_history")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_STORAGE_DIR = os.path.join(BASE_DIR, "storage", "history")


class ExecutionHistoryStore:
    """Thread-safe persistent execution history store for Runtime Engine v2 & v3."""

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        self._history: Dict[str, WorkflowExecutionStateV2] = {}
        self._storage_dir = storage_dir or DEFAULT_STORAGE_DIR
        os.makedirs(self._storage_dir, exist_ok=True)
        self._disk_loaded = False

    def _get_file_path(self, execution_id: str) -> str:
        safe_id = "".join(c for c in execution_id if c.isalnum() or c in ("_", "-"))
        return os.path.join(self._storage_dir, f"{safe_id}.json")

    def _ensure_disk_loaded(self) -> None:
        if self._disk_loaded:
            return
        try:
            if os.path.exists(self._storage_dir):
                entries = []
                with os.scandir(self._storage_dir) as it:
                    for entry in it:
                        if entry.is_file() and entry.name.endswith(".json"):
                            try:
                                entries.append((entry.stat().st_mtime, entry.path))
                            except OSError:
                                pass
                # Sort newest first, load latest 200
                entries.sort(key=lambda x: x[0], reverse=True)
                for _, fpath in entries[:200]:
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        state = WorkflowExecutionStateV2.model_validate(data)
                        if state.execution_id not in self._history:
                            self._history[state.execution_id] = state
                    except Exception:
                        pass
            self._disk_loaded = True
        except Exception as exc:
            logger.warning(f"Failed loading execution history from disk: {exc}")

    async def save_state(self, state: WorkflowExecutionStateV2) -> None:
        self._history[state.execution_id] = state.model_copy(deep=True)
        try:
            os.makedirs(self._storage_dir, exist_ok=True)
            with open(self._get_file_path(state.execution_id), "w", encoding="utf-8") as f:
                f.write(state.model_dump_json(indent=2))
        except Exception as exc:
            logger.warning(f"Failed to write execution state to disk for [{state.execution_id}]: {exc}")
        logger.debug(f"Persisted state for execution [{state.execution_id}] status [{state.status}].")

    async def get_state(self, execution_id: str) -> Optional[WorkflowExecutionStateV2]:
        state = self._history.get(execution_id)
        if not state:
            file_path = self._get_file_path(execution_id)
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    state = WorkflowExecutionStateV2.model_validate(data)
                    self._history[execution_id] = state
                    logger.info(f"Loaded execution state from disk for [{execution_id}].")
                except Exception as exc:
                    logger.warning(f"Failed to read execution state from disk for [{execution_id}]: {exc}")

        return state.model_copy(deep=True) if state else None

    async def list_user_executions(self, tenant_id: str = "usr_1") -> List[WorkflowExecutionStateV2]:
        self._ensure_disk_loaded()
        user_states = [s.model_copy(deep=False) for s in self._history.values() if s.tenant_id.lower() == tenant_id.lower()]
        return sorted(user_states, key=lambda x: x.start_time, reverse=True)

    async def list_workflow_executions(self, workflow_id: str) -> List[WorkflowExecutionStateV2]:
        self._ensure_disk_loaded()
        matched = [
            s.model_copy(deep=False)
            for s in self._history.values()
            if s.workflow_id == workflow_id or s.workflow_id.lower() == workflow_id.lower() or workflow_id == "all"
        ]
        return sorted(matched, key=lambda x: x.start_time, reverse=True)


execution_history_store = ExecutionHistoryStore()
