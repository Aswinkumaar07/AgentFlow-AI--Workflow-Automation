import pytest
from app.agents.parameter_autofill import parameter_autofill_engine, parameter_autofill_service


def test_parameter_autofill_sheets_loop_gmail():
    graph = {
        "title": "Send Email to Employees",
        "nodes": [
            {
                "id": "step_1",
                "label": "Read Sheets Rows",
                "provider": "Google Sheets",
                "operation_id": "sheets.spreadsheets.values.get",
            },
            {
                "id": "step_2",
                "label": "Loop Employee Rows",
                "provider": "Loop",
                "operation_id": "loop.process",
            },
            {
                "id": "step_3",
                "label": "Gmail Send Email",
                "provider": "Gmail",
                "operation_id": "gmail.messages.send",
            },
        ],
        "edges": [
            {"id": "e1-2", "source": "step_1", "target": "step_2"},
            {"id": "e2-3", "source": "step_2", "target": "step_3"},
        ],
    }

    res = parameter_autofill_service.autofill_graph(graph)
    assert res.get("is_fully_configured") is True

    nodes = res.get("nodes", [])
    assert len(nodes) == 3

    # Google Sheets Node Verification
    sheets_params = nodes[0]["parameters"]
    assert sheets_params["spreadsheet_id"] == "Employees"
    assert sheets_params["sheet_name"] == "HR"

    # Loop Node Verification
    loop_params = nodes[1]["parameters"]
    assert loop_params["collection"] == "{{$node.step_1.values}}"

    # Gmail Node Verification
    gmail_params = nodes[2]["parameters"]
    assert gmail_params["to"] == "{{$loop.item.email}}"


def test_parameter_autofill_slack_and_drive():
    graph = {
        "nodes": [
            {
                "id": "step_1",
                "provider": "Slack",
                "operation_id": "slack.chat.postMessage",
            },
            {
                "id": "step_2",
                "provider": "Google Drive",
                "operation_id": "drive.files.upload",
            },
        ]
    }

    res = parameter_autofill_engine.autofill_workflow_nodes(graph)
    nodes = res["nodes"]

    assert nodes[0]["parameters"]["channel"] == "#general"
    assert nodes[1]["parameters"]["folder"] == "Invoices"
