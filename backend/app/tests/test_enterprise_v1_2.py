import pytest
from app.audit.manager import audit_log_manager
from app.observability.metrics import observability_metrics
from app.secrets.manager import enterprise_secrets_store
from app.versions.manager import workflow_version_manager
from app.workspaces.manager import WorkspaceRole, workspace_manager


@pytest.mark.asyncio
async def test_workflow_version_control():
    wf_id = "wf_ver_test"
    spec = {"workflow_id": wf_id, "steps": [{"step_id": "step_1"}]}

    v1 = await workflow_version_manager.create_version_snapshot(wf_id, spec, "Initial commit")
    assert v1.version_number == 1

    v2 = await workflow_version_manager.create_version_snapshot(wf_id, spec, "Added Slack step")
    assert v2.version_number == 2

    history = await workflow_version_manager.get_version_history(wf_id)
    assert len(history) == 2

    rolled = await workflow_version_manager.rollback_to_version(wf_id, 1)
    assert rolled is not None
    assert rolled.version_number == 1


@pytest.mark.asyncio
async def test_workspace_rbac_permissions():
    ws = await workspace_manager.create_workspace("Engineering Team", "usr_owner", "owner@eng.com")
    assert ws.id == "ws_engineering_team"

    # Owner permission check
    can_edit = await workspace_manager.check_permission(ws.id, "usr_owner", "workflow:edit")
    assert can_edit is True


@pytest.mark.asyncio
async def test_audit_logs():
    entry = await audit_log_manager.log_action("OAUTH_CONNECTED", user_id="usr_1", details={"provider": "Slack"})
    assert entry.action == "OAUTH_CONNECTED"

    logs = await audit_log_manager.get_logs()
    assert len(logs) >= 1


@pytest.mark.asyncio
async def test_secrets_management():
    sec = await enterprise_secrets_store.set_secret("OPENAI_API_KEY", "sk-proj-123456789")
    assert sec.key == "OPENAI_API_KEY"

    decrypted = await enterprise_secrets_store.get_secret("OPENAI_API_KEY")
    assert decrypted == "sk-proj-123456789"

    masked = await enterprise_secrets_store.list_masked_secrets()
    target_masked = next((m for m in masked if m["key"] == "OPENAI_API_KEY"), None)
    assert target_masked is not None
    assert "****" in target_masked["masked_value"]


@pytest.mark.asyncio
async def test_observability_metrics():
    observability_metrics.record_execution("COMPLETED", 45.2)
    summary = observability_metrics.get_metrics_summary()
    assert summary["total_executions"] > 0

    prom = observability_metrics.generate_prometheus_metrics()
    assert "agentflow_executions_total" in prom
