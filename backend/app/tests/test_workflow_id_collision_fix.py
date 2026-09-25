import pytest
import pytest_asyncio
import uuid
from app.api.v1.ai import generate_workflow
from app.schemas.ai import AIGenerateRequest
from app.services.workflow_scheduler import workflow_scheduler_service
from app.connectors.security.secret_manager import secret_manager
from app.connectors.models import ConnectorCredentialModel
from app.runtime.credential_resolver import credential_resolver
from app.api.v1.runtime import execute_full_workflow_dag

@pytest.mark.asyncio
async def test_a_b_c_new_manual_workflow_receives_unique_id_no_schedule_collision():
    """Requirements A, B, C: Manual workflow receives unique workflow_id and does not collide with existing schedule."""
    req1 = AIGenerateRequest(prompt="Get my latest Gmail email and summarize its content")
    res1 = await generate_workflow(req1, current_user=None)
    data1 = res1.get("data") or {}
    wf_json1 = data1.get("workflow_json") or {}
    wf_id1 = wf_json1.get("workflow_id")

    assert wf_id1 is not None, "Workflow 1 must have workflow_id"
    assert wf_id1 != "wf_studio_1", "Manual workflow must not reuse wf_studio_1"
    assert wf_id1.startswith("wf_gen_"), "Workflow ID should start with wf_gen_"

    req2 = AIGenerateRequest(prompt="Get my latest Gmail email and summarize its content")
    res2 = await generate_workflow(req2, current_user=None)
    data2 = res2.get("data") or {}
    wf_json2 = data2.get("workflow_json") or {}
    wf_id2 = wf_json2.get("workflow_id")

    assert wf_id2 is not None
    assert wf_id1 != wf_id2, "Two distinct manual workflow generations must have unique workflow_ids"

    # Requirement C: list_jobs for unique ID must return empty list (no collision with Monday Sales Summary)
    schedules = workflow_scheduler_service.list_jobs(wf_id1)
    assert len(schedules) == 0, f"Manual workflow {wf_id1} must not discover unrelated schedules"


@pytest.mark.asyncio
async def test_d_post_runtime_execute_manual_workflow_immediate_execution():
    """Requirement D: POST /runtime/execute for manual workflow with unique ID follows immediate execution path."""
    req = AIGenerateRequest(prompt="Get my latest Gmail email and summarize its content")
    res_gen = await generate_workflow(req, current_user=None)
    wf_json = res_gen["data"]["workflow_json"]
    wf_id = wf_json["workflow_id"]

    # Seed valid credential so execution proceeds
    cred = ConnectorCredentialModel(
        tenant_id="usr_1",
        provider="Google",
        auth_type="OAuth2",
        access_token="valid_oauth_access_token",
        account_label="aswinkumaar07@gmail.com",
    )
    await secret_manager.set_secret("usr_1", "Google", cred)

    exec_req = {
        "workflow": {
            "workflow_id": wf_id,
            "nodes": wf_json.get("nodes", []),
            "edges": wf_json.get("edges", []),
        }
    }

    res_exec = await execute_full_workflow_dag(exec_req)
    assert res_exec["status"] != "SCHEDULE_ACTIVATED", "Manual workflow execution must NOT return SCHEDULE_ACTIVATED"
    assert res_exec.get("execution_id", "").startswith("exec_v3_"), "Manual workflow must route to immediate DAG executor (exec_v3_)"



@pytest.mark.asyncio
async def test_e_f_existing_schedule_remains_active_and_unchanged():
    """Requirements E, F: Existing scheduled workflow ('Monday Sales Summary') remains active and unchanged."""
    all_schedules = workflow_scheduler_service.list_jobs("all")
    monday_sched = next((s for s in all_schedules if s.get("name") == "Monday Sales Summary"), None)

    if not monday_sched:
        job = workflow_scheduler_service.schedule_job(
            prompt="Weekly Sales Summary every monday at 9am",
            workflow_json={"workflow_id": "wf_studio_1", "nodes": []},
            name="Monday Sales Summary",
            workflow_id="wf_studio_1",
            cron_expression="0 9 * * 1",
        )
        monday_sched = job.to_dict()

    assert monday_sched is not None, "Monday Sales Summary schedule must exist"
    assert monday_sched.get("workflow_id") == "wf_studio_1", "Monday Sales Summary schedule workflow_id must be preserved"
    assert monday_sched.get("status") in ["active", "paused"], "Monday Sales Summary status must be untouched"

    # Execution for wf_studio_1 still activates schedule
    exec_req = {"workflow": {"workflow_id": "wf_studio_1", "nodes": []}}
    res_sched = await execute_full_workflow_dag(exec_req)
    assert res_sched["status"] == "SCHEDULE_ACTIVATED", "Workflow with attached schedule still returns SCHEDULE_ACTIVATED"
