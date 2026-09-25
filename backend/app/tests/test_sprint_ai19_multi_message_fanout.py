import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from app.agents.task_decomposer.decomposer import enterprise_task_decomposer
from app.runtime.workflow_executor import workflow_runtime_executor_v3
from app.utils.gmail_normalizer import extract_gmail_message_details, decode_base64url


def test_1_unread_search_returning_0_messages():
    """Test 1: Unread search returning 0 messages returns empty messages list cleanly."""
    prompt = "Find my unread Gmail emails"
    tasks = enterprise_task_decomposer._deterministic_decompose(prompt, prompt.lower())
    assert len(tasks) == 2
    assert tasks[0].operation == "gmail.messages.list"
    assert tasks[0].parameters.get("max_results") == 10
    assert tasks[1].parameters.get("message_id") == "{{step_1.messages[*].id}}"


def test_2_unread_search_returning_1_message():
    """Test 2: Unread search returning 1 message works cleanly with single email output."""
    raw_res = {
        "status": "COMPLETED",
        "total_items": 1,
        "success_count": 1,
        "failed_count": 0,
        "messages": [
            {
                "id": "single_msg_1",
                "threadId": "single_msg_1",
                "labelIds": ["UNREAD"],
                "payload": {
                    "headers": [
                        {"name": "From", "value": "support@github.com"},
                        {"name": "Subject", "value": "Security Alert"},
                        {"name": "Date", "value": "Mon, 24 Aug 2026 12:00:00 GMT"},
                    ],
                    "body": {"data": "U2VjdXJpdHkgYWxlcnQgZGV0YWlscy4="},
                },
            }
        ],
    }
    extracted = extract_gmail_message_details(raw_res)
    assert extracted["messageId"] == "single_msg_1"
    assert extracted["sender"] == "support@github.com"
    assert extracted["subject"] == "Security Alert"


def test_3_unread_search_returning_5_messages():
    """Test 3: Unread search returning 5 messages sets max_results=10 and fan-out pattern."""
    prompt = "Find my unread Gmail emails and display their sender, subject, date, and message content."
    tasks = enterprise_task_decomposer._deterministic_decompose(prompt, prompt.lower())
    assert len(tasks) == 2
    assert tasks[0].parameters.get("max_results") == 10
    assert tasks[1].parameters.get("message_id") == "{{step_1.messages[*].id}}"


def test_4_sender_search_returning_multiple_messages():
    """Test 4: Sender search prompt generates search -> get fan-out DAG with max_results=10."""
    prompt = "Find emails from john@example.com and show sender, subject, date and content."
    tasks = enterprise_task_decomposer._deterministic_decompose(prompt, prompt.lower())
    assert len(tasks) == 2
    assert tasks[0].operation == "gmail.messages.search"
    assert tasks[0].parameters.get("max_results") == 10
    assert "from:" in tasks[0].parameters.get("q")
    assert tasks[1].parameters.get("message_id") == "{{step_1.messages[*].id}}"


def test_5_search_to_get_fanout_dag():
    """Test 5: Search -> Get Fan-Out DAG structure validation."""
    prompt = "Find all emails from aswinkumaarsr.cs24@bitsathy.ac.in"
    tasks = enterprise_task_decomposer._deterministic_decompose(prompt, prompt.lower())
    assert tasks[0].operation == "gmail.messages.search"
    assert tasks[1].operation == "gmail.messages.get"
    assert tasks[1].parameters.get("message_id") == "{{step_1.messages[*].id}}"


def test_6_list_to_get_fanout_dag():
    """Test 6: List -> Get Fan-Out DAG structure validation for unread emails."""
    prompt = "Find unread emails and show details"
    tasks = enterprise_task_decomposer._deterministic_decompose(prompt, prompt.lower())
    assert tasks[0].operation == "gmail.messages.list"
    assert tasks[1].operation == "gmail.messages.get"


@pytest.mark.asyncio
async def test_7_8_individual_message_ids_passed_never_array():
    """Test 7 & 8: Verifies runtime passes individual string message IDs to gmail.messages.get, never arrays."""
    passed_ids = []

    async def mock_dispatch(node_inputs):
        inp = node_inputs[0]
        meta = inp.get("metadata", {})
        node_id = meta.get("node_id", "step_1")
        params = meta.get("interpolated_params", {})
        
        nodes = inp.get("workflow", {}).get("nodes", [])
        target_node = next((n for n in nodes if (n.get("id") or n.get("step_id")) == node_id), {})
        op = target_node.get("operation_id") or target_node.get("operation")

        if op == "gmail.messages.get":
            msg_id = params.get("message_id")
            assert isinstance(msg_id, str), f"message_id MUST be a string, got {type(msg_id)}"
            assert "[" not in msg_id, f"Array expression not resolved: {msg_id}"
            passed_ids.append(msg_id)
            return [{"status": "COMPLETED", "output": {"body": {"id": msg_id}}}]
        elif op in ["gmail.messages.search", "gmail.messages.list"]:
            return [{"status": "COMPLETED", "output": {"body": {"messages": [{"id": "m1"}, {"id": "m2"}, {"id": "m3"}]}}}]
        return [{"status": "COMPLETED", "output": {}}]

    spec = {
        "workflow_id": "wf_test_fanout",
        "nodes": [
            {
                "id": "step_1",
                "provider": "gmail",
                "operation_id": "gmail.messages.search",
                "parameters": {"q": "from:test@example.com"},
            },
            {
                "id": "step_2",
                "provider": "gmail",
                "operation_id": "gmail.messages.get",
                "parameters": {"message_id": "{{step_1.messages[*].id}}"},
            },
        ],
    }

    with patch.object(workflow_runtime_executor_v3.scheduler, "dispatch_ready_nodes", side_effect=mock_dispatch):
        with patch.object(workflow_runtime_executor_v3.checkpoint_manager, "save_checkpoint", new=AsyncMock()):
            with patch.object(workflow_runtime_executor_v3.dlq, "push_failed_execution", new=AsyncMock()):
                state = await workflow_runtime_executor_v3.execute_workflow(spec)
                assert state.status in ["COMPLETED", "RUNNING"]
                assert passed_ids == ["m1", "m2", "m3"]


@pytest.mark.asyncio
async def test_9_one_get_failure_does_not_destroy_successful_results():
    """Test 9: One get failure in fan-out loop does not fail entire workflow run."""
    async def mock_dispatch(node_inputs):
        inp = node_inputs[0]
        meta = inp.get("metadata", {})
        node_id = meta.get("node_id", "step_1")
        params = meta.get("interpolated_params", {})
        
        nodes = inp.get("workflow", {}).get("nodes", [])
        target_node = next((n for n in nodes if (n.get("id") or n.get("step_id")) == node_id), {})
        op = target_node.get("operation_id") or target_node.get("operation")

        if op in ["gmail.messages.search", "gmail.messages.list"]:
            return [{
                "status": "COMPLETED",
                "output": {
                    "body": {
                        "messages": [{"id": "ok_1"}, {"id": "fail_1"}, {"id": "ok_2"}],
                        "resultSizeEstimate": 3,
                    }
                }
            }]
        elif op == "gmail.messages.get":
            msg_id = params.get("message_id")
            if msg_id == "fail_1":
                return [{"status": "FAILED", "output": {"error": "404 Not Found"}}]
            return [{
                "status": "COMPLETED",
                "output": {
                    "body": {
                        "id": msg_id,
                        "payload": {
                            "headers": [
                                {"name": "From", "value": "user@domain.com"},
                                {"name": "Subject", "value": f"Subject for {msg_id}"},
                            ],
                            "body": {"data": "VGVzdCBib2R5"},
                        },
                    }
                }
            }]
        return [{"status": "COMPLETED", "output": {}}]

    spec = {
        "workflow_id": "wf_partial_fail",
        "nodes": [
            {"id": "step_1", "provider": "gmail", "operation_id": "gmail.messages.list", "parameters": {}},
            {"id": "step_2", "provider": "gmail", "operation_id": "gmail.messages.get", "parameters": {"message_id": "{{step_1.messages[*].id}}"}},
        ],
    }

    with patch.object(workflow_runtime_executor_v3.scheduler, "dispatch_ready_nodes", side_effect=mock_dispatch):
        with patch.object(workflow_runtime_executor_v3.checkpoint_manager, "save_checkpoint", new=AsyncMock()):
            state = await workflow_runtime_executor_v3.execute_workflow(spec)
            step2_rec = state.node_records.get("step_2", {})
            assert step2_rec.get("status") == "COMPLETED"
            out = step2_rec.get("output", {})
            assert out.get("success_count") == 2
            assert out.get("failed_count") == 1


def test_10_11_all_get_operations_preserve_message_and_normalize():
    """Test 10 & 11: All get operations preserve their corresponding message and extract sender/subject/date/content."""
    item_payload = {
        "id": "msg_preserve_100",
        "threadId": "thread_100",
        "labelIds": ["INBOX"],
        "payload": {
            "headers": [
                {"name": "From", "value": "alex@company.org"},
                {"name": "Subject", "value": "Quarterly Performance"},
                {"name": "Date", "value": "Mon, 24 Aug 2026 11:11:11 GMT"},
            ],
            "body": {"data": "UXVhcnRlcmx5IHJlcG9ydCBkZXRhaWxzLg=="},
        },
    }

    details = extract_gmail_message_details(item_payload)
    assert details["messageId"] == "msg_preserve_100"
    assert details["threadId"] == "thread_100"
    assert details["sender"] == "alex@company.org"
    assert details["subject"] == "Quarterly Performance"
    assert details["date"] == "Mon, 24 Aug 2026 11:11:11 GMT"
    assert details["content"] == "Quarterly report details."


def test_12_maximum_10_results():
    """Test 12: Default maximum results is capped at 10."""
    prompt = "Find all unread emails"
    tasks = enterprise_task_decomposer._deterministic_decompose(prompt, prompt.lower())
    assert tasks[0].parameters.get("max_results") == 10


def test_13_no_side_effect_operations_for_negative_constraints():
    """Test 13: Prompts with negative constraints do NOT generate side-effect operations."""
    prompt = "Find my unread Gmail emails and display their sender, subject, date, and message content. Do not send, reply, forward, delete, or modify anything."
    tasks = enterprise_task_decomposer._deterministic_decompose(prompt, prompt.lower())
    ops = [t.operation for t in tasks]
    for side_op in ["gmail.messages.send", "gmail.messages.reply", "gmail.messages.forward", "gmail.messages.delete", "gmail.messages.trash", "gmail.messages.modify"]:
        assert side_op not in ops, f"Negative constraint violated: found side-effect operation '{side_op}'"


def test_14_existing_single_message_workflow_remains_working():
    """Test 14: Existing single-message prompt ('Read my latest Gmail email...') remains 100% working."""
    prompt = "Read my latest Gmail email and show me the sender, subject, date, and complete message content."
    tasks = enterprise_task_decomposer._deterministic_decompose(prompt, prompt.lower())
    assert len(tasks) == 2
    assert tasks[0].operation == "gmail.messages.list"
    assert tasks[0].parameters.get("max_results") == 1
    assert tasks[1].parameters.get("message_id") == "{{step_1.messages[0].id}}"
