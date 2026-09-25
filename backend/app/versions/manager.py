import logging
import os
import json
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("agentflow.versions")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_STORAGE_DIR = os.path.join(BASE_DIR, "storage", "versions")

SENSITIVE_KEYS = {
    "access_token", "refresh_token", "api_key", "secret", "client_secret",
    "password", "authorization", "auth_header", "bot_token", "token",
    "credentials", "oauth_token", "oauth_secret", "private_key"
}


def sanitize_spec(obj: Any) -> Any:
    """Recursively redacts secrets and sensitive keys from specs before persistence."""
    if isinstance(obj, dict):
        sanitized = {}
        for k, v in obj.items():
            if any(s in str(k).lower() for s in SENSITIVE_KEYS):
                sanitized[k] = "[REDACTED_SECRET]"
            else:
                sanitized[k] = sanitize_spec(v)
        return sanitized
    elif isinstance(obj, list):
        return [sanitize_spec(item) for item in obj]
    return obj


class WorkflowVersionSnapshot(BaseModel):
    version_id: str
    workflow_id: str
    version_number: int
    name: str = ""
    description: str = ""
    status: str = "PUBLISHED"  # DRAFT, PUBLISHED, ARCHIVED
    workflow_spec: Dict[str, Any]
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0
    commit_message: str = "Updated workflow definition"
    author: str = "admin@agentflow.ai"
    created_at: float = Field(default_factory=time.time)


class WorkflowVersionManager:
    """Enterprise Workflow Version Manager with durable disk persistence, secret sanitization, and rollbacks."""

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        self._versions: Dict[str, List[WorkflowVersionSnapshot]] = {}
        self._storage_dir = storage_dir or DEFAULT_STORAGE_DIR
        os.makedirs(self._storage_dir, exist_ok=True)

    def _get_file_path(self, workflow_id: str) -> str:
        safe_id = "".join(c for c in workflow_id if c.isalnum() or c in ("_", "-"))
        return os.path.join(self._storage_dir, f"{safe_id}.json")

    def _load_from_disk(self, workflow_id: str) -> List[WorkflowVersionSnapshot]:
        file_path = self._get_file_path(workflow_id)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                snapshots = [WorkflowVersionSnapshot.model_validate(item) for item in data]
                self._versions[workflow_id] = snapshots
                return snapshots
            except Exception as exc:
                logger.warning(f"Failed to load versions from disk for workflow [{workflow_id}]: {exc}")
        return []

    def _save_to_disk(self, workflow_id: str) -> None:
        try:
            os.makedirs(self._storage_dir, exist_ok=True)
            snapshots = self._versions.get(workflow_id, [])
            data = [s.model_dump() for s in snapshots]
            with open(self._get_file_path(workflow_id), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as exc:
            logger.warning(f"Failed to persist versions to disk for workflow [{workflow_id}]: {exc}")

    async def create_version_snapshot(
        self,
        workflow_id: str,
        workflow_spec: Dict[str, Any],
        name: str = "",
        description: str = "",
        commit_message: str = "Updated workflow definition",
        author: str = "admin@agentflow.ai",
    ) -> WorkflowVersionSnapshot:
        history = await self.get_version_history(workflow_id)
        next_ver_num = max([v.version_number for v in history], default=0) + 1
        ver_id = f"ver_{workflow_id}_v{next_ver_num}"

        sanitized_spec = sanitize_spec(workflow_spec)
        nodes = sanitized_spec.get("nodes") or sanitized_spec.get("steps") or []
        edges = sanitized_spec.get("edges") or []

        wf_name = name or sanitized_spec.get("workflow_name") or sanitized_spec.get("name") or f"Version {next_ver_num}"
        wf_desc = description or sanitized_spec.get("description") or ""

        snapshot = WorkflowVersionSnapshot(
            version_id=ver_id,
            workflow_id=workflow_id,
            version_number=next_ver_num,
            name=wf_name,
            description=wf_desc,
            status="PUBLISHED",
            workflow_spec=sanitized_spec,
            nodes=nodes,
            edges=edges,
            node_count=len(nodes),
            edge_count=len(edges),
            commit_message=commit_message,
            author=author,
            created_at=time.time(),
        )

        if workflow_id not in self._versions:
            self._versions[workflow_id] = []
        self._versions[workflow_id].append(snapshot)
        self._save_to_disk(workflow_id)

        logger.info(f"Created Workflow Snapshot v{next_ver_num} ({ver_id}) for workflow [{workflow_id}].")
        return snapshot.model_copy(deep=True)

    async def get_version_history(self, workflow_id: str) -> List[WorkflowVersionSnapshot]:
        self._load_from_disk(workflow_id)
        history = self._versions.get(workflow_id, [])
        return sorted([v.model_copy(deep=True) for v in history], key=lambda x: x.version_number, reverse=True)

    async def get_version_by_id(self, workflow_id: str, version_id: str) -> Optional[WorkflowVersionSnapshot]:
        history = await self.get_version_history(workflow_id)
        for v in history:
            if v.version_id == version_id or str(v.version_number) == str(version_id) or version_id == f"v{v.version_number}":
                return v.model_copy(deep=True)
        return None

    async def rollback_to_version(self, workflow_id: str, version_number_or_id: Any) -> Optional[WorkflowVersionSnapshot]:
        history = await self.get_version_history(workflow_id)
        for v in history:
            if str(v.version_number) == str(version_number_or_id) or v.version_id == str(version_number_or_id):
                logger.info(f"Retrieved version [{v.version_id}] for rollback/restore on workflow [{workflow_id}].")
                return v.model_copy(deep=True)
        return None


workflow_version_manager = WorkflowVersionManager()
