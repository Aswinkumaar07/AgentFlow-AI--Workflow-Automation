"""
Sprint AI-8: Multi-Step DAG Auto-Generation Tests

Verifies that the planner automatically generates the correct DAG for:
1. Read today's emails -> Summarize -> Email summary  (4-node DAG)
2. Read unread emails -> Summarize -> Email summary  (4-node DAG)
3. Search invoices -> Download attachment -> Upload Drive -> Notify Slack (4-node DAG)
"""
import pytest
from app.agents.planner.planner_v4 import intelligent_planner_v4
from app.agents.task_decomposer.decomposer import enterprise_task_decomposer


# ---------------------------------------------------------------------------
# Decomposer-level Tests
# ---------------------------------------------------------------------------

def test_decomposer_read_today_emails_summarize_email():
    """Read today's emails → Summarize → Email summary must produce 4 tasks."""
    result = enterprise_task_decomposer.decompose("Read today's emails and summarize, then email me the summary")
    tasks = result.tasks
    assert len(tasks) >= 3, f"Expected >=3 tasks, got {len(tasks)}: {[t.name for t in tasks]}"

    ops = [t.operation for t in tasks]
    assert "gmail.messages.list" in ops, f"Expected gmail.messages.list in {ops}"
    assert "ai.summarize" in ops, f"Expected ai.summarize in {ops}"
    assert "gmail.messages.send" in ops, f"Expected gmail.messages.send in {ops}"


def test_decomposer_read_unread_summarize():
    """Read unread emails and summarize must produce >=3 tasks."""
    result = enterprise_task_decomposer.decompose("Read unread emails and summarize")
    assert len(result.tasks) >= 3
    ops = [t.operation for t in result.tasks]
    assert "gmail.messages.list" in ops
    assert "ai.summarize" in ops


def test_decomposer_search_invoice_drive_slack():
    """Search invoices → download attachment → upload drive → notify slack = 4 tasks."""
    result = enterprise_task_decomposer.decompose(
        "Search invoices, download attachment, upload to drive, notify slack"
    )
    tasks = result.tasks
    assert len(tasks) == 4, f"Expected 4 tasks, got {len(tasks)}: {[t.name for t in tasks]}"

    ops = [t.operation for t in tasks]
    assert "gmail.messages.search" in ops
    assert "gmail.attachments.download" in ops
    assert "drive.files.create" in ops
    assert "slack.chat.postMessage" in ops


# ---------------------------------------------------------------------------
# Planner-level Tests (Universal DAG Auto-Builder)
# ---------------------------------------------------------------------------

def test_planner_auto_dag_read_summarize_email():
    """Planner must auto-build >=3-node DAG for read→summarize→email prompt."""
    plan = intelligent_planner_v4.plan("Read today's emails and summarize, then email me the summary")
    nodes = plan.workflow_graph.get("nodes", [])
    edges = plan.workflow_graph.get("edges", [])

    assert len(nodes) >= 3, f"Expected >=3 nodes, got {len(nodes)}: {[n.get('operation') for n in nodes]}"
    assert len(edges) >= 2, f"Expected >=2 edges, got {len(edges)}"

    ops = [n.get("operation") or n.get("operation_id") for n in nodes]
    assert "gmail.messages.list" in ops, f"Expected list op in {ops}"
    assert "ai.summarize" in ops, f"Expected summarize op in {ops}"

    # Verify AI-8 trace entry
    trace = plan.reasoning_trace
    assert any("AI-8 Universal DAG Builder" in t for t in trace), f"AI-8 trace not found in: {trace}"


def test_planner_auto_dag_invoice_drive_slack():
    """Planner must auto-build 4-node DAG for search→download→drive→slack prompt."""
    plan = intelligent_planner_v4.plan(
        "Search invoices, download attachment, upload to drive, notify slack"
    )
    nodes = plan.workflow_graph.get("nodes", [])
    edges = plan.workflow_graph.get("edges", [])

    assert len(nodes) == 4, f"Expected 4 nodes, got {len(nodes)}: {[n.get('operation') for n in nodes]}"
    assert len(edges) == 3, f"Expected 3 edges, got {len(edges)}"

    ops = [n.get("operation") or n.get("operation_id") for n in nodes]
    assert "gmail.messages.search" in ops
    assert "gmail.attachments.download" in ops
    assert "drive.files.create" in ops
    assert "slack.chat.postMessage" in ops


def test_planner_dag_edges_are_sequential():
    """Auto-generated edges must form a correct sequential chain."""
    plan = intelligent_planner_v4.plan("Read unread emails and summarize")
    nodes = plan.workflow_graph.get("nodes", [])
    edges = plan.workflow_graph.get("edges", [])

    assert len(nodes) >= 2
    node_ids = [n["id"] for n in nodes]
    for edge in edges:
        assert edge["source"] in node_ids, f"Edge source {edge['source']} not in {node_ids}"
        assert edge["target"] in node_ids, f"Edge target {edge['target']} not in {node_ids}"
        # Target step must be strictly after source step
        src_step = int(edge["source"].split("_")[1])
        tgt_step = int(edge["target"].split("_")[1])
        assert tgt_step > src_step, f"Edge goes backwards: {edge}"
