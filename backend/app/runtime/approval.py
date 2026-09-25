import logging
import os
import json
import time
from typing import Dict, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("agentflow.runtime.approval")


class ApprovalRequestModel(BaseModel):
    execution_id: str
    node_id: str
    status: str = "PENDING"  # PENDING, APPROVED, REJECTED
    requested_at: float = Field(default_factory=time.time)
    responded_at: Optional[float] = None
    approver: Optional[str] = None


class HumanApprovalEngine:
    """Manages Human Approval pause nodes and approval/rejection signals."""

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        self._approvals: Dict[str, ApprovalRequestModel] = {}  # key: execution_id:node_id
        self._storage_dir = storage_dir or os.path.join(os.getcwd(), "storage", "approvals")
        os.makedirs(self._storage_dir, exist_ok=True)

    def _make_key(self, execution_id: str, node_id: str) -> str:
        return f"{execution_id}:{node_id}"

    def _get_file_path(self, key: str) -> str:
        safe_key = "".join(c for c in key if c.isalnum() or c in ("_", "-"))
        return os.path.join(self._storage_dir, f"{safe_key}.json")

    def _save_to_disk(self, key: str, req: ApprovalRequestModel) -> None:
        try:
            os.makedirs(self._storage_dir, exist_ok=True)
            with open(self._get_file_path(key), "w", encoding="utf-8") as f:
                f.write(req.model_dump_json(indent=2))
        except Exception as exc:
            logger.warning(f"Failed to save approval request to disk for key [{key}]: {exc}")

    def _load_from_disk(self, key: str) -> Optional[ApprovalRequestModel]:
        file_path = self._get_file_path(key)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                req = ApprovalRequestModel.model_validate(data)
                self._approvals[key] = req
                return req
            except Exception as exc:
                logger.warning(f"Failed to load approval request from disk for key [{key}]: {exc}")
        return None

    async def create_approval_request(self, execution_id: str, node_id: str) -> ApprovalRequestModel:
        key = self._make_key(execution_id, node_id)
        req = ApprovalRequestModel(execution_id=execution_id, node_id=node_id, status="PENDING")
        self._approvals[key] = req
        self._save_to_disk(key, req)
        logger.info(f"Created Human Approval request for execution [{execution_id}] node [{node_id}].")
        return req

    async def approve(self, execution_id: str, node_id: str, approver: str = "admin") -> bool:
        key = self._make_key(execution_id, node_id)
        req = await self.get_approval(execution_id, node_id)
        if req and req.status == "PENDING":
            req.status = "APPROVED"
            req.responded_at = time.time()
            req.approver = approver
            self._save_to_disk(key, req)
            logger.info(f"Human Approval APPROVED for execution [{execution_id}] node [{node_id}] by [{approver}].")
            return True
        return False

    async def reject(self, execution_id: str, node_id: str, approver: str = "admin") -> bool:
        key = self._make_key(execution_id, node_id)
        req = await self.get_approval(execution_id, node_id)
        if req and req.status == "PENDING":
            req.status = "REJECTED"
            req.responded_at = time.time()
            req.approver = approver
            self._save_to_disk(key, req)
            logger.info(f"Human Approval REJECTED for execution [{execution_id}] node [{node_id}] by [{approver}].")
            return True
        return False

    async def get_approval(self, execution_id: str, node_id: str) -> Optional[ApprovalRequestModel]:
        key = self._make_key(execution_id, node_id)
        req = self._approvals.get(key)
        if not req:
            req = self._load_from_disk(key)
        return req


human_approval_engine = HumanApprovalEngine()

