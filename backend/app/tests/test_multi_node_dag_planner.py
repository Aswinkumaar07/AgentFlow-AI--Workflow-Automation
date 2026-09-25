import pytest
from app.agents.planner.planner_v4 import intelligent_planner_v4
from app.runtime.dag_execution_engine import dag_execution_engine, DAGExecutionEngine


def test_read_summarize_send_email_dag_generation():
    prompt = "Read unread emails, summarize them, and send an email summary to user@example.com"
    plan = intelligent_planner_v4.plan(prompt)

    graph = plan.workflow_graph
    nodes = graph["nodes"]
    edges = graph["edges"]

    # AI-8: 4-node DAG: List -> Get -> Summarize -> Send
    assert len(nodes) >= 3, f"Expected >=3 nodes, got {len(nodes)}: {[n.get('operation') for n in nodes]}"
    assert len(edges) >= 2

    # Step 1: List
    assert nodes[0]["operation"] == "gmail.messages.list"
    assert nodes[0]["parameters"]["q"] == "is:unread"

    # Step 2: Get
    assert nodes[1]["operation"] == "gmail.messages.get"
    assert "{{step_1.messages[0].id}}" in nodes[1]["parameters"]["message_id"]

    # Edges: step_1 -> step_2 -> step_3
    assert edges[0]["source"] == "step_1" and edges[0]["target"] == "step_2"
    assert edges[1]["source"] == "step_2" and edges[1]["target"] == "step_3"


def test_search_invoice_drive_slack_dag_generation():
    prompt = "Search invoices, download attachment, upload to Drive, and notify Slack"
    plan = intelligent_planner_v4.plan(prompt)

    graph = plan.workflow_graph
    nodes = graph["nodes"]
    edges = graph["edges"]

    assert len(nodes) == 4
    assert len(edges) == 3

    # Operations sequence
    ops = [n["operation"] for n in nodes]
    assert ops == ["gmail.messages.search", "gmail.attachments.download", "drive.files.create", "slack.chat.postMessage"]

    # Variable references check
    assert "{{step_1.messages[0].id}}" in nodes[1]["parameters"]["message_id"]
    assert "{{step_2.filename}}" in nodes[2]["parameters"]["name"]
    assert "{{step_2.filename}}" in nodes[3]["parameters"]["text"]


def test_dag_variable_resolution_engine():
    engine = DAGExecutionEngine()

    mock_context = {
        "step_1": {
            "messages": [{"id": "msg_999888"}]
        },
        "step_2": {
            "filename": "q3_invoice.pdf",
            "savedPath": "attachments_output/q3_invoice.pdf"
        }
    }

    params_to_resolve = {
        "file_name": "{{step_2.filename}}",
        "path": "{{step_2.savedPath}}",
        "msg_id": "{{step_1.messages[0].id}}",
        "message": "Processed file {{step_2.filename}} from email {{step_1.messages[0].id}}"
    }

    resolved = engine.resolve_parameters(params_to_resolve, mock_context)
    assert resolved["file_name"] == "q3_invoice.pdf"
    assert resolved["path"] == "attachments_output/q3_invoice.pdf"
    assert resolved["msg_id"] == "msg_999888"
    assert resolved["message"] == "Processed file q3_invoice.pdf from email msg_999888"


def test_dag_runtime_execution_sequence():
    engine = DAGExecutionEngine()

    mock_graph = {
        "nodes": [
            {
                "id": "step_1",
                "provider": "gmail",
                "operation": "gmail.messages.list",
                "parameters": {"q": "is:unread", "max_results": 1}
            },
            {
                "id": "step_2",
                "provider": "gmail",
                "operation": "gmail.messages.send",
                "parameters": {
                    "to": "dev@company.com",
                    "subject": "DAG Executed",
                    "body": "Step 1 completed with query: {{step_1.q}}"
                }
            }
        ],
        "edges": [{"source": "step_1", "target": "step_2"}]
    }

    res = engine.execute_dag(mock_graph, tenant_id="usr_1")
    assert res["success"] is True
    assert res["total_nodes"] == 2
    assert len(res["steps"]) == 2
    assert res["steps"][1]["resolved_parameters"]["body"] == "Step 1 completed with query: is:unread"
