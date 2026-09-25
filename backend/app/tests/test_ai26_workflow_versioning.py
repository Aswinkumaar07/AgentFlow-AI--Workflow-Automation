import os
import shutil
import uuid
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.versions.manager import WorkflowVersionManager, sanitize_spec
from app.runtime.execution_history import ExecutionHistoryStore
from app.runtime.checkpoint import CheckpointManager
from app.runtime.state import WorkflowExecutionStateV2
from app.runtime.workflow_executor import workflow_runtime_executor_v3

client = TestClient(app)

TEST_STORAGE_DIR = os.path.join(os.getcwd(), "storage", "test_ai26_versions")


@pytest.fixture(autouse=True)
def cleanup_test_storage():
    if os.path.exists(TEST_STORAGE_DIR):
        shutil.rmtree(TEST_STORAGE_DIR, ignore_errors=True)
    os.makedirs(TEST_STORAGE_DIR, exist_ok=True)
    yield
    if os.path.exists(TEST_STORAGE_DIR):
        shutil.rmtree(TEST_STORAGE_DIR, ignore_errors=True)


# ── 5-Node 4-Edge Graph Persistence Test ───────────────────────────────────

def test_5_node_4_edge_save_version_persistence():
    wf_id = f"wf_5node_{uuid.uuid4().hex[:6]}"
    nodes_5 = [
        {"id": "step_1", "step_id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.list", "parameters": {"max_results": 10}},
        {"id": "step_2", "step_id": "step_2", "provider": "Gmail", "operation_id": "gmail.messages.get", "parameters": {"message_id": "{{step_1.messages[0].id}}"}, "dependencies": ["step_1"]},
        {"id": "step_3", "step_id": "step_3", "provider": "AI Agent", "operation_id": "ai.summarize", "parameters": {"text": "{{step_2.body}}"}, "dependencies": ["step_2"]},
        {"id": "step_4", "step_id": "step_4", "provider": "human_approval", "operation_id": "approval.wait", "parameters": {}, "dependencies": ["step_3"]},
        {"id": "step_5", "step_id": "step_5", "provider": "Slack", "operation_id": "slack.chat.postMessage", "parameters": {"channel": "#all-agentflow-ai", "text": "{{step_3.summary}}", "api_key": "secret_key_123"}, "dependencies": ["step_4"]}
    ]
    edges_4 = [
        {"id": "e1", "source": "step_1", "target": "step_2"},
        {"id": "e2", "source": "step_2", "target": "step_3"},
        {"id": "e3", "source": "step_3", "target": "step_4"},
        {"id": "e4", "source": "step_4", "target": "step_5"}
    ]

    workflow_spec = {
        "workflow_id": wf_id,
        "nodes": nodes_5,
        "edges": edges_4,
        "steps": nodes_5
    }

    # 1. Create Version via API
    resp_create = client.post(f"/api/v1/workflows/{wf_id}/versions", json={
        "name": "Version 1 - Gmail AI Slack Approval Workflow",
        "workflow_spec": workflow_spec,
        "commit_message": "Initial 5-node workflow save"
    })
    assert resp_create.status_code == 201
    created = resp_create.json()["data"]
    version_id = created["version_id"]

    # 2. Verify persisted version contains exactly 5 nodes and 4 edges
    assert created["node_count"] == 5
    assert created["edge_count"] == 4
    assert len(created["nodes"]) == 5
    assert len(created["edges"]) == 4

    # 3. Verify Version API returns those nodes and edges
    resp_get = client.get(f"/api/v1/workflows/{wf_id}/versions/{version_id}")
    assert resp_get.status_code == 200
    fetched = resp_get.json()["data"]
    assert fetched["node_count"] == 5
    assert fetched["edge_count"] == 4

    # 4. Verify Secret Sanitization in persisted spec
    slack_node = next(n for n in fetched["nodes"] if n["id"] == "step_5")
    assert slack_node["parameters"]["api_key"] == "[REDACTED_SECRET]"
    assert slack_node["parameters"]["channel"] == "#all-agentflow-ai"

    # 5. Verify Restore loads stored 5-node graph
    resp_restore = client.post(f"/api/v1/workflows/{wf_id}/versions/{version_id}/restore")
    assert resp_restore.status_code == 200
    restored = resp_restore.json()["data"]
    assert restored["node_count"] == 5
    assert restored["edge_count"] == 4
    assert len(restored["nodes"]) == 5
    assert len(restored["edges"]) == 4


# ── A. Create Workflow Version ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_a_create_workflow_version():
    wf_id = f"wf_a_{uuid.uuid4().hex[:6]}"
    manager = WorkflowVersionManager(storage_dir=TEST_STORAGE_DIR)
    spec = {
        "workflow_id": wf_id,
        "nodes": [{"id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.list"}],
        "edges": [],
    }
    v1 = await manager.create_version_snapshot(wf_id, spec, name="Version 1 Initial")
    assert v1.workflow_id == wf_id
    assert v1.version_number == 1
    assert len(v1.nodes) == 1
    assert v1.node_count == 1


# ── B. Version Numbers Increment Correctly ──────────────────────────────────

@pytest.mark.asyncio
async def test_b_version_numbers_increment():
    wf_id = f"wf_b_{uuid.uuid4().hex[:6]}"
    manager = WorkflowVersionManager(storage_dir=TEST_STORAGE_DIR)
    v1 = await manager.create_version_snapshot(wf_id, {"workflow_id": wf_id, "nodes": [{"id": "s1"}]})
    v2 = await manager.create_version_snapshot(wf_id, {"workflow_id": wf_id, "nodes": [{"id": "s1"}, {"id": "s2"}]})
    v3 = await manager.create_version_snapshot(wf_id, {"workflow_id": wf_id, "nodes": [{"id": "s1"}, {"id": "s2"}, {"id": "s3"}]})

    assert v1.version_number == 1
    assert v2.version_number == 2
    assert v3.version_number == 3


# ── C. Version Persists After Backend Restart ───────────────────────────────

@pytest.mark.asyncio
async def test_c_version_persists_after_restart():
    wf_id = f"wf_c_{uuid.uuid4().hex[:6]}"
    mgr1 = WorkflowVersionManager(storage_dir=TEST_STORAGE_DIR)
    await mgr1.create_version_snapshot(wf_id, {"workflow_id": wf_id, "title": "Persistent V1"})

    # Re-instantiate manager (simulating restart)
    mgr2 = WorkflowVersionManager(storage_dir=TEST_STORAGE_DIR)
    history = await mgr2.get_version_history(wf_id)
    assert len(history) == 1
    assert history[0].version_number == 1


# ── D. List Versions Newest-First ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_d_list_versions_newest_first():
    wf_id = f"wf_d_{uuid.uuid4().hex[:6]}"
    mgr = WorkflowVersionManager(storage_dir=TEST_STORAGE_DIR)
    await mgr.create_version_snapshot(wf_id, {"nodes": [{"id": "1"}]})
    await mgr.create_version_snapshot(wf_id, {"nodes": [{"id": "1"}, {"id": "2"}]})
    await mgr.create_version_snapshot(wf_id, {"nodes": [{"id": "1"}, {"id": "2"}, {"id": "3"}]})

    history = await mgr.get_version_history(wf_id)
    assert len(history) == 3
    assert history[0].version_number == 3
    assert history[1].version_number == 2
    assert history[2].version_number == 1


# ── E. Retrieve Exact Version via API ──────────────────────────────────────

def test_e_retrieve_exact_version_api():
    wf_id = f"wf_e_{uuid.uuid4().hex[:6]}"
    resp_create = client.post(f"/api/v1/workflows/{wf_id}/versions", json={
        "name": "Version E",
        "workflow_spec": {"workflow_id": wf_id, "nodes": [{"id": "step_1"}]}
    })
    assert resp_create.status_code == 201
    created_data = resp_create.json()["data"]
    version_id = created_data["version_id"]

    resp_get = client.get(f"/api/v1/workflows/{wf_id}/versions/{version_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["data"]["version_id"] == version_id


# ── F. Old Version is Immutable ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_f_old_version_immutable():
    wf_id = f"wf_f_{uuid.uuid4().hex[:6]}"
    mgr = WorkflowVersionManager(storage_dir=TEST_STORAGE_DIR)

    v1_spec = {"workflow_id": wf_id, "nodes": [{"id": "step_1", "name": "V1 Step"}]}
    v1 = await mgr.create_version_snapshot(wf_id, v1_spec, name="V1")

    v2_spec = {"workflow_id": wf_id, "nodes": [{"id": "step_1", "name": "V2 Step"}, {"id": "step_2"}]}
    v2 = await mgr.create_version_snapshot(wf_id, v2_spec, name="V2")

    v1_fetched = await mgr.get_version_by_id(wf_id, v1.version_id)
    assert len(v1_fetched.nodes) == 1
    assert v1_fetched.nodes[0]["name"] == "V1 Step"
    assert len(v2.nodes) == 2


# ── G. Restore Old Version ────────────────────────────────────────────────

def test_g_restore_old_version_api():
    wf_id = f"wf_g_{uuid.uuid4().hex[:6]}"
    c1 = client.post(f"/api/v1/workflows/{wf_id}/versions", json={"name": "V1", "workflow_spec": {"nodes": [{"id": "a"}]}})
    v1_id = c1.json()["data"]["version_id"]

    c2 = client.post(f"/api/v1/workflows/{wf_id}/versions", json={"name": "V2", "workflow_spec": {"nodes": [{"id": "a"}, {"id": "b"}]}})

    res_restore = client.post(f"/api/v1/workflows/{wf_id}/versions/{v1_id}/restore")
    assert res_restore.status_code == 200
    restored = res_restore.json()["data"]
    assert len(restored["nodes"]) == 1
    assert restored["nodes"][0]["id"] == "a"


# ── H & I. Modify Restored Version Creates NEW Version ─────────────────────

@pytest.mark.asyncio
async def test_h_i_modify_restored_version_creates_new():
    wf_id = f"wf_hi_{uuid.uuid4().hex[:6]}"
    mgr = WorkflowVersionManager(storage_dir=TEST_STORAGE_DIR)

    v1 = await mgr.create_version_snapshot(wf_id, {"nodes": [{"id": "v1_node"}]})
    v2 = await mgr.create_version_snapshot(wf_id, {"nodes": [{"id": "v2_node"}]})

    restored_v1 = await mgr.rollback_to_version(wf_id, v1.version_number)
    modified_spec = dict(restored_v1.workflow_spec)
    modified_spec["nodes"].append({"id": "v3_new_node"})

    v3 = await mgr.create_version_snapshot(wf_id, modified_spec, name="V3 Restored & Modified")
    assert v3.version_number == 3

    v1_check = await mgr.get_version_by_id(wf_id, v1.version_id)
    v2_check = await mgr.get_version_by_id(wf_id, v2.version_id)
    assert len(v1_check.nodes) == 1
    assert len(v2_check.nodes) == 1
    assert len(v3.nodes) == 2


# ── J. Execution Records Exact Version Used ────────────────────────────────

@pytest.mark.asyncio
async def test_j_execution_records_exact_version():
    wf_id = f"wf_j_{uuid.uuid4().hex[:6]}"
    spec = {
        "workflow_id": wf_id,
        "version_id": f"ver_{wf_id}_v2",
        "version_number": 2,
        "steps": [
            {"step_id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.list"}
        ]
    }
    state = await workflow_runtime_executor_v3.execute_workflow(spec)
    assert state.version_number == 2
    assert state.version_id == f"ver_{wf_id}_v2"


# ── K. New Version Does Not Change Old Execution History ──────────────────

@pytest.mark.asyncio
async def test_k_new_version_does_not_change_old_execution():
    wf_id = f"wf_k_{uuid.uuid4().hex[:6]}"
    spec_v1 = {
        "workflow_id": wf_id,
        "version_id": f"ver_{wf_id}_v1",
        "version_number": 1,
        "steps": [{"step_id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.list"}]
    }
    state1 = await workflow_runtime_executor_v3.execute_workflow(spec_v1)
    exec1_id = state1.execution_id

    spec_v2 = {
        "workflow_id": wf_id,
        "version_id": f"ver_{wf_id}_v2",
        "version_number": 2,
        "steps": [{"step_id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.list"}]
    }
    await workflow_runtime_executor_v3.execute_workflow(spec_v2)

    store = ExecutionHistoryStore()
    old_state = await store.get_state(exec1_id)
    assert old_state.version_number == 1


# ── L. Execution History Survives Restart ──────────────────────────────────

@pytest.mark.asyncio
async def test_l_execution_history_survives_restart():
    wf_id = f"wf_l_{uuid.uuid4().hex[:6]}"
    spec = {
        "workflow_id": wf_id,
        "version_number": 1,
        "steps": [{"step_id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.list"}]
    }
    state = await workflow_runtime_executor_v3.execute_workflow(spec)
    exec_id = state.execution_id

    new_store = ExecutionHistoryStore()
    reloaded = await new_store.get_state(exec_id)
    assert reloaded is not None
    assert reloaded.execution_id == exec_id


# ── M. Execution History Endpoint & Inspector Telemetry ────────────────────

def test_m_execution_history_endpoint_and_inspector():
    wf_id = f"wf_m_{uuid.uuid4().hex[:6]}"
    exec_resp = client.post("/api/v1/runtime/execute", json={
        "workflow_id": wf_id,
        "version_number": 1,
        "steps": [{"step_id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.list"}]
    })
    assert exec_resp.status_code == 200
    exec_data = exec_resp.json()
    exec_id = exec_data["execution_id"]

    hist_resp = client.get(f"/api/v1/workflows/{wf_id}/executions")
    assert hist_resp.status_code == 200
    history_items = hist_resp.json()["data"]
    assert any(i["execution_id"] == exec_id for i in history_items)

    telem_resp = client.get(f"/api/v1/runtime/{exec_id}")
    assert telem_resp.status_code == 200
    assert telem_resp.json()["execution_id"] == exec_id


# ── N. AI-25 Resume Works With Historical Version ─────────────────────────

@pytest.mark.asyncio
async def test_n_resume_historical_version():
    wf_id = f"wf_n_{uuid.uuid4().hex[:6]}"
    spec = {
        "workflow_id": wf_id,
        "version_id": f"ver_{wf_id}_v1",
        "version_number": 1,
        "steps": [
            {"step_id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.list"},
            {"step_id": "step_2", "provider": "human_approval", "operation_id": "approval.wait", "dependencies": ["step_1"]},
            {"step_id": "step_3", "provider": "Slack", "operation_id": "slack.chat.postMessage", "dependencies": ["step_2"]}
        ]
    }
    state = await workflow_runtime_executor_v3.execute_workflow(spec)
    assert state.status == "WAITING"
    exec_id = state.execution_id

    res_approve = client.post(f"/api/v1/runtime/{exec_id}/approve?node_id=step_2")
    assert res_approve.status_code == 200
    data = res_approve.json()
    assert data["status"] in ("COMPLETED", "FAILED")
    assert data["version_number"] == 1


# ── O. AI-23 Conditional Workflow Version Survives Restore ───────────────

@pytest.mark.asyncio
async def test_o_conditional_workflow_version_survives_restore():
    wf_id = f"wf_o_{uuid.uuid4().hex[:6]}"
    mgr = WorkflowVersionManager(storage_dir=TEST_STORAGE_DIR)
    spec = {
        "workflow_id": wf_id,
        "nodes": [
            {"id": "c1", "provider": "condition", "operation_id": "condition.if", "parameters": {"field": "{{step_1.value}}", "operator": "equals", "value": "VIP"}},
            {"id": "t1", "provider": "Slack", "operation_id": "slack.chat.postMessage"},
            {"id": "f1", "provider": "Email", "operation_id": "email.send"}
        ],
        "edges": [
            {"source": "c1", "target": "t1", "condition": "true"},
            {"source": "c1", "target": "f1", "condition": "false"}
        ]
    }
    v1 = await mgr.create_version_snapshot(wf_id, spec, name="Conditional Spec V1")
    restored = await mgr.get_version_by_id(wf_id, v1.version_id)

    assert len(restored.nodes) == 3
    assert restored.nodes[0]["parameters"]["operator"] == "equals"
    assert restored.edges[0]["condition"] == "true"


# ── P. AI-24 Loop Workflow Version Survives Restore ───────────────────────

@pytest.mark.asyncio
async def test_p_loop_workflow_version_survives_restore():
    wf_id = f"wf_p_{uuid.uuid4().hex[:6]}"
    mgr = WorkflowVersionManager(storage_dir=TEST_STORAGE_DIR)
    spec = {
        "workflow_id": wf_id,
        "nodes": [
            {"id": "l1", "provider": "Loop", "operation_id": "loop.forEach", "parameters": {"items": "{{step_1.emails}}", "item_variable": "email_item", "index_variable": "idx"}}
        ],
        "edges": []
    }
    v1 = await mgr.create_version_snapshot(wf_id, spec, name="Loop Spec V1")
    restored = await mgr.get_version_by_id(wf_id, v1.version_id)

    params = restored.nodes[0]["parameters"]
    assert params["item_variable"] == "email_item"
    assert params["index_variable"] == "idx"


# ── Q & R. AI-22 Gmail → AI → Slack & Slack Target Channel Regression ─────

@pytest.mark.asyncio
async def test_q_r_gmail_ai_slack_regression():
    wf_id = f"wf_qr_{uuid.uuid4().hex[:6]}"
    spec = {
        "workflow_id": wf_id,
        "steps": [
            {"step_id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.list", "parameters": {"max_results": 1}},
            {"step_id": "step_2", "provider": "Gmail", "operation_id": "gmail.messages.get", "parameters": {"message_id": "{{step_1.messages[0].id}}"}, "dependencies": ["step_1"]},
            {"step_id": "step_3", "provider": "AI Agent", "operation_id": "ai.summarize", "parameters": {"text": "{{step_2.body}}"}, "dependencies": ["step_2"]},
            {"step_id": "step_4", "provider": "Slack", "operation_id": "slack.chat.postMessage", "parameters": {"channel": "#all-agentflow-ai", "text": "{{step_3.summary}}"}, "dependencies": ["step_3"]}
        ]
    }
    state = await workflow_runtime_executor_v3.execute_workflow(spec)
    assert state.status in ("COMPLETED", "FAILED")
    assert "step_4" in state.node_records


# ── S. Secrets Are Never Persisted in Workflow Versions ───────────────────

def test_s_secrets_redacted_in_versions():
    secret_spec = {
        "workflow_id": "wf_test_secrets",
        "api_key": "secret_api_key_12345",
        "access_token": "bearer_oauth_secret_token",
        "nodes": [
            {
                "id": "step_1",
                "parameters": {
                    "client_secret": "my_client_secret",
                    "normal_param": "public_data"
                }
            }
        ]
    }
    sanitized = sanitize_spec(secret_spec)
    assert sanitized["api_key"] == "[REDACTED_SECRET]"
    assert sanitized["access_token"] == "[REDACTED_SECRET]"
    assert sanitized["nodes"][0]["parameters"]["client_secret"] == "[REDACTED_SECRET]"
    assert sanitized["nodes"][0]["parameters"]["normal_param"] == "public_data"


# ── T. Invalid Version IDs Fail Cleanly ───────────────────────────────────

def test_t_invalid_version_id_returns_404():
    res = client.get("/api/v1/workflows/wf_invalid/versions/nonexistent_ver_9999")
    assert res.status_code == 404
