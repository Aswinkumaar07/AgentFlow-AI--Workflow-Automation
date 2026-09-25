import pytest
import asyncio
from typing import Dict, Any

from app.runtime.workflow_executor import WorkflowRuntimeExecutorV3
from app.runtime.context import ExecutionContext
from app.agents.task_decomposer.decomposer import EnterpriseTaskDecomposer
from app.agents.planner.gmail_search_query_builder import build_gmail_search_query


@pytest.fixture
def executor():
    return WorkflowRuntimeExecutorV3()


@pytest.mark.asyncio
async def test_1_empty_gmail_search_returns_completed_status(executor):
    """
    Sprint AI-19.1 Test 1:
    Prompt: "Find all emails from nonexistent-user-12345@example.com."
    Search query must be valid Gmail syntax 'from:nonexistent-user-12345@example.com'.
    Workflow execution must return COMPLETED with 0 results and 0 fan-out executions.
    """
    q = build_gmail_search_query("Find all emails from nonexistent-user-12345@example.com.")
    assert q == "from:nonexistent-user-12345@example.com"

    workflow = {
        "nodes": [
            {
                "id": "step_1",
                "type": "custom",
                "data": {
                    "label": "Search Emails",
                    "provider": "gmail",
                    "operation_id": "gmail.messages.search",
                    "parameters": {"q": q, "max_results": 10},
                    "step_id": "step_1",
                },
                "parameters": {"q": q, "max_results": 10},
                "provider": "gmail",
                "operation": "gmail.messages.search",
            },
            {
                "id": "step_2",
                "type": "custom",
                "data": {
                    "label": "Get Message Details",
                    "provider": "gmail",
                    "operation_id": "gmail.messages.get",
                    "parameters": {"message_id": "{{step_1.messages[*].id}}"},
                    "step_id": "step_2",
                },
                "parameters": {"message_id": "{{step_1.messages[*].id}}"},
                "provider": "gmail",
                "operation": "gmail.messages.get",
            },
        ],
        "edges": [{"id": "e1-2", "source": "step_1", "target": "step_2"}],
    }

    state = await executor.execute_workflow(workflow)

    assert state.status == "COMPLETED"
    step2_rec = state.node_records.get("step_2", {})
    assert step2_rec.get("status") == "COMPLETED"
    out = step2_rec.get("output", {})
    assert out.get("total_items") == 0
    assert out.get("success_count") == 0
    assert out.get("failed_count") == 0
    assert out.get("messages") == []


@pytest.mark.asyncio
async def test_2_zero_fanout_calls_dispatched_for_empty_array(executor):
    """
    Sprint AI-19.1 Test 2:
    When step 1 returns empty array, 0 get child calls must be made.
    """
    workflow = {
        "nodes": [
            {
                "id": "step_1",
                "type": "custom",
                "data": {
                    "provider": "gmail",
                    "operation_id": "gmail.messages.list",
                    "parameters": {"q": "is:unread", "max_results": 10},
                },
                "parameters": {"q": "is:unread", "max_results": 10},
                "provider": "gmail",
                "operation": "gmail.messages.list",
            },
            {
                "id": "step_2",
                "type": "custom",
                "data": {
                    "provider": "gmail",
                    "operation_id": "gmail.messages.get",
                    "parameters": {"message_id": "{{step_1.messages[*].id}}"},
                },
                "parameters": {"message_id": "{{step_1.messages[*].id}}"},
                "provider": "gmail",
                "operation": "gmail.messages.get",
            },
        ]
    }

    state = await executor.execute_workflow(workflow)
    step2_rec = state.node_records.get("step_2", {})

    assert step2_rec.get("status") == "COMPLETED"
    assert step2_rec.get("output", {}).get("total_items") == 0
    assert step2_rec.get("output", {}).get("items") == []


@pytest.mark.asyncio
async def test_3_no_uninterpolated_message_ids_dispatched(executor):
    """
    Sprint AI-19.1 Test 3:
    Never dispatch null/undefined or raw '{{step_1.messages[*].id}}' string to Gmail API.
    """
    from app.runtime.node_executor import node_executor

    node_input = {
        "metadata": {
            "node_id": "step_2",
            "interpolated_params": {"message_id": "{{step_1.messages[0].id}}"},
        },
        "workflow": {
            "nodes": [
                {
                    "id": "step_2",
                    "provider": "gmail",
                    "operation": "gmail.messages.get",
                    "parameters": {"message_id": "{{step_1.messages[0].id}}"},
                }
            ]
        },
        "tenant_id": "usr_test",
    }

    res = await node_executor.execute_node(node_input)
    assert res["status"] == "COMPLETED"
    assert res["output"]["body"]["total_items"] == 0
    assert res["output"]["body"]["messages"] == []


@pytest.mark.asyncio
async def test_4_read_only_negative_constraint_safety():
    """
    Sprint AI-19.1 Test 4:
    Prompt with negative constraint 'do not delete or send anything' must produce ONLY read operations.
    """
    decomposer = EnterpriseTaskDecomposer()
    decomp = decomposer.decompose(
        "Find all emails from nonexistent-user-12345@example.com. Do not send, reply, forward, delete, or modify anything."
    )
    ops = [task.operation for task in decomp.tasks]

    assert "gmail.messages.search" in ops or "gmail.messages.list" in ops
    assert "gmail.messages.get" in ops
    assert "gmail.messages.send" not in ops
    assert "gmail.messages.delete" not in ops
    assert "gmail.messages.reply" not in ops


@pytest.mark.asyncio
async def test_5_positive_multi_message_search_preserves_cards(executor):
    """
    Sprint AI-19.1 Test 5:
    Positive search with returned emails continues to produce multi-email details.
    """
    from app.utils.gmail_normalizer import extract_gmail_message_details

    mock_exec_data = {
        "node_results": [
            {"node_id": "step_1", "operation": "gmail.messages.search", "status": "SUCCESS"},
            {
                "node_id": "step_2",
                "operation": "gmail.messages.get",
                "status": "SUCCESS",
                "output": {
                    "status_code": 200,
                    "total_items": 2,
                    "success_count": 2,
                    "failed_count": 0,
                    "messages": [
                        {
                            "id": "m101",
                            "threadId": "t101",
                            "payload": {
                                "headers": [
                                    {"name": "From", "value": "Alice <alice@example.com>"},
                                    {"name": "Subject", "value": "Project Alpha Update"},
                                ],
                                "snippet": "Here is the status of Alpha.",
                            },
                        },
                        {
                            "id": "m102",
                            "threadId": "t102",
                            "payload": {
                                "headers": [
                                    {"name": "From", "value": "Bob <bob@example.com>"},
                                    {"name": "Subject", "value": "Invoice #55"},
                                ],
                                "snippet": "Attached invoice #55.",
                            },
                        },
                    ],
                },
            },
        ]
    }

    from app.utils.gmail_normalizer import extract_gmail_message_details
    details = extract_gmail_message_details(mock_exec_data)
    assert details["messageId"] == "m101"
    assert details["sender"] == "Alice <alice@example.com>"
    assert details["subject"] == "Project Alpha Update"
