import pytest
import asyncio
from typing import Dict, Any, List

from app.agents.task_decomposer import enterprise_task_decomposer
from app.agents.planner.planner_v4 import IntelligentPlannerEngineV4
from app.agents.validator.workflow_validator import WorkflowValidator, WorkflowValidator as validator_service
from app.runtime.live_node_executor import live_node_executor
from app.runtime.node_executor import node_executor


def test_scenario_a_gmail_read_ai_summarize_slack():
    prompt = "When I receive an unread Gmail email, summarize it and send the summary to Slack."
    res = enterprise_task_decomposer.decompose(prompt, intent="READ_AND_NOTIFY")
    assert len(res.tasks) == 4
    
    op_ids = [t.operation for t in res.tasks]
    assert op_ids[0] in ["gmail.messages.list", "gmail.messages.search"]
    assert op_ids[1] == "gmail.messages.get"
    assert op_ids[2] == "ai.summarize"
    assert op_ids[3] == "slack.chat.postMessage"

    # Verify template expression data flow
    slack_text = res.tasks[3].parameters.get("text", "")
    assert "{{step_3.summary}}" in slack_text


def test_scenario_b_gmail_read_slack_no_ai():
    prompt = "Read my latest Gmail email and send the subject and body to Slack."
    res = enterprise_task_decomposer.decompose(prompt, intent="READ_AND_NOTIFY")
    assert len(res.tasks) == 3

    op_ids = [t.operation for t in res.tasks]
    assert op_ids[0] == "gmail.messages.list"
    assert op_ids[1] == "gmail.messages.get"
    assert op_ids[2] == "slack.chat.postMessage"

    # Verify NO AI summarize node was inserted
    assert "ai.summarize" not in op_ids
    slack_text = res.tasks[2].parameters.get("text", "")
    assert "{{step_2." in slack_text


def test_scenario_c_gmail_search_fanout_ai_summarize():
    prompt = "Find unread Gmail emails and summarize them."
    res = enterprise_task_decomposer.decompose(prompt, intent="READ_AND_SUMMARIZE")
    assert len(res.tasks) >= 3

    op_ids = [t.operation for t in res.tasks]
    assert op_ids[0] in ["gmail.messages.list", "gmail.messages.search"]
    assert op_ids[1] == "gmail.messages.get"
    assert op_ids[2] == "ai.summarize"


def test_scenario_d_gmail_read_attachment_drive_upload():
    prompt = "Find my latest Gmail email and save its attachment to Google Drive."
    res = enterprise_task_decomposer.decompose(prompt, intent="DOWNLOAD_AND_UPLOAD")
    assert len(res.tasks) == 4

    op_ids = [t.operation for t in res.tasks]
    assert op_ids[0] == "gmail.messages.list"
    assert op_ids[1] == "gmail.messages.get"
    assert op_ids[2] == "gmail.attachments.download"
    assert op_ids[3] == "drive.files.create"

    # Verify Drive file name parameter consumes attachment output
    drive_file_name = res.tasks[3].parameters.get("name", "")
    assert "{{step_3.filename}}" in drive_file_name


def test_scenario_e_gmail_search_invoice_ai_summarize_slack():
    prompt = "Search Gmail for invoice emails, summarize the matching emails, and send the summary to Slack."
    res = enterprise_task_decomposer.decompose(prompt, intent="SEARCH_SUMMARIZE_NOTIFY")
    assert len(res.tasks) == 4

    op_ids = [t.operation for t in res.tasks]
    assert op_ids[0] in ["gmail.messages.search", "gmail.messages.list"]
    assert op_ids[1] == "gmail.messages.get"
    assert op_ids[2] == "ai.summarize"
    assert op_ids[3] == "slack.chat.postMessage"


def test_dag_validation_clean_multi_service():
    validator = WorkflowValidator()
    wf_graph = {
        "user_prompt": "When I receive an unread Gmail email, summarize it and send the summary to Slack.",
        "trigger": {"type": "Manual"},
        "nodes": [
            {"id": "step_1", "provider": "Gmail", "operation": "gmail.messages.list", "parameters": {"q": "is:unread"}},
            {"id": "step_2", "provider": "Gmail", "operation": "gmail.messages.get", "parameters": {"message_id": "msg_001"}},
            {"id": "step_3", "provider": "AI", "operation": "ai.summarize", "parameters": {"text": "{{step_2.snippet}}"}},
            {"id": "step_4", "provider": "Slack", "operation": "slack.chat.postMessage", "parameters": {"channel": "#general", "text": "{{step_3.summary}}"}},
        ],
        "edges": [
            {"source": "step_1", "target": "step_2"},
            {"source": "step_2", "target": "step_3"},
            {"source": "step_3", "target": "step_4"},
        ]
    }
    report = validator.validate_workflow(wf_graph)
    assert report.is_valid is True
    assert len(report.errors) == 0


def test_dag_validation_cycle_detection():
    validator = WorkflowValidator()
    wf_graph = {
        "trigger": {"type": "Manual"},
        "nodes": [
            {"id": "step_1", "provider": "Gmail", "operation": "gmail.messages.list"},
            {"id": "step_2", "provider": "Slack", "operation": "slack.chat.postMessage", "parameters": {"channel": "#gen", "text": "Hi"}},
        ],
        "edges": [
            {"source": "step_1", "target": "step_2"},
            {"source": "step_2", "target": "step_1"},  # Cycle!
        ]
    }
    report = validator.validate_workflow(wf_graph)
    assert report.is_valid is False
    assert any("cycle" in err.lower() for err in report.errors)


@pytest.mark.asyncio
async def test_live_execution_ai_node():
    node = {
        "id": "step_3",
        "provider": "AI",
        "operation": "ai.summarize",
        "parameters": {"text": "Project terraform deployment complete in 12s."}
    }
    res = await live_node_executor.execute_node(node)
    assert res.status == "SUCCESS"
    assert res.status_code == 200
    assert "summary" in res.response["body"]
    assert "Project terraform deployment" in res.response["body"]["summary"]


@pytest.mark.asyncio
async def test_live_execution_slack_node():
    node = {
        "id": "step_4",
        "provider": "Slack",
        "operation": "slack.chat.postMessage",
        "parameters": {"channel": "#dev-alerts", "text": "Build succeeded!"}
    }
    
    async def mock_slack_request(method, url, headers, json_data=None, params=None, timeout=30.0):
        if "conversations.list" in url:
            return {"ok": True, "channels": [{"id": "C_DEV_ALERTS", "name": "dev-alerts"}]}
        if "chat.postMessage" in url:
            return {"ok": True, "ts": "1726100000.000100", "channel": "C_DEV_ALERTS", "message": {"text": json_data.get("text")}}
        return {"ok": False, "error": "unknown_url"}

    from unittest.mock import patch
    from app.connectors.models import ConnectorCredentialModel
    from app.connectors.security.secret_manager import secret_manager
    cred = ConnectorCredentialModel(
        tenant_id="usr_1",
        provider="Slack",
        auth_type="OAuth2",
        access_token="xoxb-mock-test-token",
        scopes=["chat:write", "channels:read"]
    )
    await secret_manager.set_secret("usr_1", "Slack", cred)

    with patch("app.connectors.providers.slack.adapter.connection_pool.request", side_effect=mock_slack_request):
        res = await live_node_executor.execute_node(node)
        assert res.status == "SUCCESS"
        assert res.status_code == 200
        assert res.response["body"]["ok"] is True
        assert res.response["body"]["channel"] == "C_DEV_ALERTS"


@pytest.mark.asyncio
async def test_live_execution_drive_node():
    node = {
        "id": "step_4",
        "provider": "Google Drive",
        "operation": "drive.files.create",
        "parameters": {"name": "Invoice_Aug2026.pdf"}
    }
    res = await live_node_executor.execute_node(node)
    assert res.status == "SUCCESS"
    assert res.status_code == 200
    assert res.response["body"]["name"] == "Invoice_Aug2026.pdf"
