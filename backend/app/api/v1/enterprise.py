import logging
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Response
from app.audit.manager import audit_log_manager
from app.observability.metrics import observability_metrics
from app.secrets.manager import enterprise_secrets_store
from app.versions.manager import workflow_version_manager
from app.workspaces.manager import workspace_manager

router = APIRouter(prefix="/enterprise", tags=["Enterprise Platform & Collaboration"])
logger = logging.getLogger("agentflow.api.enterprise")


@router.get("/versions/{workflow_id}")
async def get_workflow_versions(workflow_id: str):
    """Returns version history snapshots for a workflow."""
    return [v.model_dump() for v in await workflow_version_manager.get_version_history(workflow_id)]


@router.post("/versions/{workflow_id}/snapshot")
async def create_version_snapshot(workflow_id: str, payload: Dict[str, Any]):
    """Creates a new version snapshot of a workflow definition."""
    workflow_spec = payload.get("workflow_spec", {})
    msg = payload.get("commit_message", "Updated workflow definition")
    snapshot = await workflow_version_manager.create_version_snapshot(workflow_id, workflow_spec, commit_message=msg)
    await audit_log_manager.log_action("WORKFLOW_SNAPSHOT_CREATED", details={"workflow_id": workflow_id, "version": snapshot.version_number})
    return snapshot.model_dump()


@router.post("/versions/{workflow_id}/rollback/{version_number}")
async def rollback_workflow_version(workflow_id: str, version_number: int):
    """Rolls back a workflow to a target version number."""
    rolled = await workflow_version_manager.rollback_to_version(workflow_id, version_number)
    if not rolled:
        raise HTTPException(status_code=404, detail=f"Version {version_number} not found for workflow {workflow_id}")
    await audit_log_manager.log_action("WORKFLOW_ROLLED_BACK", details={"workflow_id": workflow_id, "version": version_number})
    return rolled.model_dump()


@router.get("/audit-logs")
async def get_audit_logs():
    """Returns audit log history entries."""
    logs = await audit_log_manager.get_logs()
    return [l.model_dump() for l in logs]


@router.get("/secrets")
async def list_masked_secrets():
    """Lists masked workspace secrets."""
    return await enterprise_secrets_store.list_masked_secrets()


@router.post("/secrets")
async def store_secret(payload: Dict[str, Any]):
    """Stores an encrypted secret key-value pair."""
    key = payload.get("key")
    val = payload.get("value")
    if not key or not val:
        raise HTTPException(status_code=400, detail="Key and value are required")
    sec = await enterprise_secrets_store.set_secret(key, val)
    await audit_log_manager.log_action("SECRET_STORED", details={"key": key})
    return {"message": f"Successfully stored secret [{key}]", "key": sec.key}


@router.get("/metrics")
async def get_observability_metrics():
    """Returns observability metrics summary."""
    return observability_metrics.get_metrics_summary()


@router.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """Exposes Prometheus format metrics endpoint."""
    content = observability_metrics.generate_prometheus_metrics()
    return Response(content=content, media_type="text/plain")
