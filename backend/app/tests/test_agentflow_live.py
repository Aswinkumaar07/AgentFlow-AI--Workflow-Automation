import pytest
from app.connectors.manager import connector_manager
from app.connectors.providers.sheets.adapter import GoogleSheetsAdapter
from app.runtime.workflow_executor import workflow_runtime_executor_v3
from app.triggers.engine import TriggerEngine, TriggerType, WorkflowActivationStatus, trigger_engine


@pytest.mark.asyncio
async def test_google_sheets_adapter_execution():
    res = await connector_manager.execute(
        provider="Google Sheets",
        operation_id="sheets.spreadsheets.values.append",
        parameters={"spreadsheet_id": "sheet_123", "range": "Sheet1!A1"},
        tenant_id="usr_1",
    )
    assert res.success is True
    assert res.status_code == 200
    assert "updates" in res.data or "status" in res.data


@pytest.mark.asyncio
async def test_phase7_end_to_end_workflow():
    """Phase 7 Demo Workflow Verification:

    Gmail Email Trigger -> Drive Upload -> Slack Alert -> Sheets Row Append
    """
    e2e_workflow = {
        "workflow_id": "wf_e2e_demo",
        "steps": [
            {
                "step_id": "step_1",
                "provider": "Gmail",
                "operation_id": "gmail.messages.list",
                "parameters": {"query": "label:invoices"},
            },
            {
                "step_id": "step_2",
                "provider": "Google Drive",
                "operation_id": "drive.files.create",
                "parameters": {"folder": "Invoices"},
                "dependencies": ["step_1"],
            },
            {
                "step_id": "step_3",
                "provider": "Slack",
                "operation_id": "slack.chat.postMessage",
                "parameters": {"channel": "#finance-alerts"},
                "dependencies": ["step_2"],
            },
            {
                "step_id": "step_4",
                "provider": "Google Sheets",
                "operation_id": "sheets.spreadsheets.values.append",
                "parameters": {"spreadsheet_id": "sheet_invoice_ledger"},
                "dependencies": ["step_3"],
            },
        ],
    }

    state = await workflow_runtime_executor_v3.execute_workflow(e2e_workflow)
    assert state.status == "COMPLETED"
    assert len(state.node_records) == 4
    assert state.node_records["step_1"]["status"] == "COMPLETED"
    assert state.node_records["step_2"]["status"] == "COMPLETED"
    assert state.node_records["step_3"]["status"] == "COMPLETED"
    assert state.node_records["step_4"]["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_trigger_engine_event_dispatch():
    # Register active webhook trigger
    wf_spec = {
        "workflow_id": "wf_trig_test",
        "steps": [{"step_id": "step_1", "provider": "Generic", "operation_id": "generic.http.request"}],
    }
    sub = await trigger_engine.register_trigger(
        workflow_id="wf_trig_test",
        trigger_type=TriggerType.GITHUB,
        config={"repo": "AgentFlow-AI"},
        workflow_spec=wf_spec,
    )
    assert sub.status == WorkflowActivationStatus.ACTIVE

    # Fire incoming event
    results = await trigger_engine.process_incoming_event(
        trigger_type=TriggerType.GITHUB, payload={"action": "opened", "pr_id": 42}
    )
    assert len(results) >= 1
    assert results[0]["status"] == "COMPLETED"
