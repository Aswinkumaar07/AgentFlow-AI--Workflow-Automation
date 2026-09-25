import os
import glob
import json
import logging
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.workflow_service import WorkflowService, parse_workflow_uuid

logger = logging.getLogger("agentflow.backfill")

DEFAULT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
KNOWN_USER_MAPPINGS: Dict[str, uuid.UUID] = {
    "admin@agentflow.ai": DEFAULT_USER_ID,
    "usr_1": DEFAULT_USER_ID,
    "usr_ai30_test": DEFAULT_USER_ID,
}

class WorkflowBackfillService:
    def __init__(self, db: AsyncSession, storage_dir: Optional[str] = None):
        self.db = db
        self.service = WorkflowService(db)
        if not storage_dir:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "storage"))
            storage_dir = os.path.join(base_dir, "versions")
        self.storage_dir = storage_dir

    def resolve_author_to_user_id(self, author: Optional[str]) -> Optional[uuid.UUID]:
        if not author:
            return DEFAULT_USER_ID
        if author in KNOWN_USER_MAPPINGS:
            return KNOWN_USER_MAPPINGS[author]
        try:
            return uuid.UUID(author)
        except ValueError:
            pass
        return None

    async def run_backfill(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {
            "discovered_unique_workflows": 0,
            "registered_count": 0,
            "already_existing_count": 0,
            "skipped_unmapped_count": 0,
            "skipped_owner_mismatch_count": 0,
            "malformed_count": 0,
            "malformed_files": [],
            "unmapped_authors": [],
            "final_sql_count": 0,
        }

        if not os.path.exists(self.storage_dir):
            return results

        json_files = glob.glob(os.path.join(self.storage_dir, "*.json"))
        results["discovered_unique_workflows"] = len(json_files)

        for filepath in json_files:
            filename = os.path.basename(filepath)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    snapshots = json.load(f)
            except Exception as read_err:
                logger.warning(f"Malformed JSON file skipped: {filename} - {read_err}")
                results["malformed_count"] += 1
                results["malformed_files"].append(filename)
                continue

            if not isinstance(snapshots, list) or len(snapshots) == 0:
                # If file contains a single dict snapshot instead of a list
                if isinstance(snapshots, dict):
                    snapshots = [snapshots]
                else:
                    results["malformed_count"] += 1
                    results["malformed_files"].append(filename)
                    continue

            # Select latest version snapshot (highest version_number)
            try:
                latest_snapshot = max(
                    snapshots,
                    key=lambda s: s.get("version_number", 0) if isinstance(s, dict) else 0
                )
            except Exception:
                latest_snapshot = snapshots[-1]

            if not isinstance(latest_snapshot, dict):
                results["malformed_count"] += 1
                results["malformed_files"].append(filename)
                continue

            wf_id_str = latest_snapshot.get("workflow_id") or os.path.splitext(filename)[0]
            author = latest_snapshot.get("author")
            owner_id = self.resolve_author_to_user_id(author)

            if not owner_id:
                logger.warning(f"Unmapped author skipped: '{author}' in {filename}")
                results["skipped_unmapped_count"] += 1
                if author and author not in results["unmapped_authors"]:
                    results["unmapped_authors"].append(author)
                continue

            title = latest_snapshot.get("name") or latest_snapshot.get("title") or f"Workflow {wf_id_str}"
            desc = latest_snapshot.get("description") or ""
            spec = latest_snapshot.get("workflow_spec") or latest_snapshot.get("definition") or {}
            ver = latest_snapshot.get("version_number") or 1

            wf_uuid = parse_workflow_uuid(wf_id_str)
            existing = await self.service.workflow_repo.get_by_id(wf_uuid)

            if existing:
                if existing.owner_id != owner_id:
                    results["skipped_owner_mismatch_count"] += 1
                    continue
                update_data = {
                    "title": title or existing.title,
                    "description": desc or existing.description,
                    "definition": spec or existing.definition,
                    "version": max(ver, existing.version),
                }
                await self.service.workflow_repo.update(existing, update_data)
                results["already_existing_count"] += 1
            else:
                new_data = {
                    "id": wf_uuid,
                    "title": title,
                    "description": desc,
                    "status": "active",
                    "version": ver,
                    "definition": spec,
                    "trigger_type": "manual",
                    "owner_id": owner_id,
                }
                await self.service.workflow_repo.create(new_data)
                results["registered_count"] += 1

        total_sql = await self.service.workflow_repo.count_by_owner(owner_id=DEFAULT_USER_ID)
        results["final_sql_count"] = total_sql
        return results
