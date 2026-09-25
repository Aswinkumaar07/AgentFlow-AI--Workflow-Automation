import pytest
from app.agents.planner.planner_v4 import intelligent_planner_v4
from app.runtime.dag_execution_engine import DAGExecutionEngine


def test_ai4_read_summarize_send_dag():
    prompt = "Read unread emails, summarize them, and send an email summary to user@example.com"
    plan = intelligent_planner_v4.plan(prompt)

    graph = plan.workflow_graph
    nodes = graph["nodes"]
    edges = graph["edges"]

    # AI-8: 4-node DAG: List -> Get -> Summarize -> Send
    assert len(nodes) >= 3, f"Expected >=3 nodes, got {len(nodes)}: {[n.get('operation') for n in nodes]}"
    assert len(edges) >= 2

    # Node operations in order
    ops = [n.get("operation") or n.get("operation_id") for n in nodes]
    assert "gmail.messages.list" in ops
    assert "gmail.messages.get" in ops

    assert nodes[0]["operation"] == "gmail.messages.list"
    assert nodes[0]["parameters"]["q"] == "is:unread"

    assert nodes[1]["operation"] == "gmail.messages.get"
    assert "{{step_1.messages[0].id}}" in nodes[1]["parameters"]["message_id"]

    # Edges wiring
    assert edges[0]["source"] == "step_1" and edges[0]["target"] == "step_2"
    assert edges[1]["source"] == "step_2" and edges[1]["target"] == "step_3"


def test_ai4_search_download_drive_slack_dag():
    prompt = "Search invoices, download attachment, upload to Drive, and notify Slack"
    plan = intelligent_planner_v4.plan(prompt)

    graph = plan.workflow_graph
    nodes = graph["nodes"]
    edges = graph["edges"]

    assert len(nodes) == 4
    assert len(edges) == 3

    # Operations chain
    ops = [n["operation"] for n in nodes]
    assert ops == [
        "gmail.messages.search",
        "gmail.attachments.download",
        "drive.files.create",
        "slack.chat.postMessage",
    ]

    # Parameters & Variable references
    assert "{{step_1.messages[0].id}}" in nodes[1]["parameters"]["message_id"]
    assert "{{step_2.filename}}" in nodes[2]["parameters"]["name"]
    assert "{{step_2.filename}}" in nodes[3]["parameters"]["text"]

    # Edges
    assert edges[0]["source"] == "step_1" and edges[0]["target"] == "step_2"
    assert edges[1]["source"] == "step_2" and edges[1]["target"] == "step_3"
    assert edges[2]["source"] == "step_3" and edges[2]["target"] == "step_4"


def test_ai4_dynamic_dag_execution_with_runtime_engine():
    engine = DAGExecutionEngine()

    mock_graph = {
        "nodes": [
            {
                "id": "step_1",
                "provider": "gmail",
                "operation": "gmail.messages.search",
                "parameters": {"q": "invoice", "max_results": 1},
            },
            {
                "id": "step_2",
                "provider": "gmail",
                "operation": "gmail.attachments.download",
                "parameters": {"message_id": "msg_invoice_101", "filename": "statement.pdf"},
            },
            {
                "id": "step_3",
                "provider": "google_drive",
                "operation": "drive.files.create",
                "parameters": {"name": "{{step_2.filename}}", "file_path": "attachments_output/statement.pdf"},
            },
            {
                "id": "step_4",
                "provider": "slack",
                "operation": "slack.chat.postMessage",
                "parameters": {"channel": "#finance", "text": "Uploaded {{step_2.filename}} to Google Drive"},
            },
        ],
        "edges": [
            {"source": "step_1", "target": "step_2"},
            {"source": "step_2", "target": "step_3"},
            {"source": "step_3", "target": "step_4"},
        ],
    }

    res = engine.execute_dag(mock_graph, tenant_id="usr_1")
    assert res["success"] is True
    assert res["total_nodes"] == 4
    assert res["steps"][3]["resolved_parameters"]["text"] == "Uploaded statement.pdf to Google Drive"
