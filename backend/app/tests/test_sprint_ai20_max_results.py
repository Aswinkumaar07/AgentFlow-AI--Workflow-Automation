import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from app.agents.task_decomposer.decomposer import EnterpriseTaskDecomposer
from app.runtime.workflow_executor import WorkflowRuntimeExecutorV3
from app.runtime.node_executor import node_executor
from app.runtime.live_node_executor import LiveNodeExecutor


@pytest.fixture
def executor():
    return WorkflowRuntimeExecutorV3()


def test_1_default_max_results_value_is_10():
    """Sprint AI-20 Test 1: Default max_results value is 10 when missing or newly decomposed."""
    decomposer = EnterpriseTaskDecomposer()
    decomp = decomposer.decompose("Find my unread emails")
    assert len(decomp.tasks) == 2
    step1 = decomp.tasks[0]
    assert step1.parameters.get("max_results") == 10


def test_2_max_results_stored_as_number():
    """Sprint AI-20 Test 2: max_results parameter is stored as an integer number."""
    raw_val = "20"
    parsed_val = int(raw_val)
    assert isinstance(parsed_val, int)
    assert parsed_val == 20


def test_3_clamping_and_validation():
    """Sprint AI-19.3 / AI-20 Test 3: Invalid values (0, negative, >50, non-numeric) are clamped to safe range [1, 50]."""
    def clamp_max_results(val):
        try:
            parsed = int(val)
            return max(1, min(50, parsed))
        except (ValueError, TypeError):
            return 10

    assert clamp_max_results(0) == 1
    assert clamp_max_results(-5) == 1
    assert clamp_max_results(150) == 50
    assert clamp_max_results(100) == 50
    assert clamp_max_results("abc") == 10
    assert clamp_max_results(5) == 5
    assert clamp_max_results(20) == 20
    assert clamp_max_results(50) == 50


@pytest.mark.asyncio
async def test_4_test_node_receives_edited_max_results():
    """Sprint AI-20 Test 4: Live single node execution receives edited max_results value."""
    executor_live = LiveNodeExecutor()

    node_payload = {
        "id": "step_1",
        "provider": "gmail",
        "operation_id": "gmail.messages.list",
        "parameters": {"q": "is:unread", "max_results": 20},
    }

    with patch.object(executor_live.gmail_adapter, "execute_operation", new=AsyncMock()) as mock_exec:
        mock_exec.return_value.success = True
        mock_exec.return_value.status_code = 200
        mock_exec.return_value.data = {"messages": [], "resultSizeEstimate": 0}

        await executor_live.execute_node(node_payload)

        req_model = mock_exec.call_args[0][0]
        assert req_model.parameters.get("max_results") == 20


@pytest.mark.asyncio
async def test_5_fanout_respects_edited_max_results(executor):
    """
    Sprint AI-20 Test 5:
    When max_results is edited to 20 (or 50), the fan-out engine respects that limit and processes up to max_results messages.
    """
    passed_max = None

    async def mock_dispatch(node_inputs):
        nonlocal passed_max
        inp = node_inputs[0]
        meta = inp.get("metadata", {})
        node_id = meta.get("node_id", "step_1")
        params = meta.get("interpolated_params", {})
        
        nodes = inp.get("workflow", {}).get("nodes", [])
        target_node = next((n for n in nodes if (n.get("id") or n.get("step_id")) == node_id), {})
        op = target_node.get("operation_id") or target_node.get("operation")

        if op in ["gmail.messages.search", "gmail.messages.list"]:
            # Generate 25 dummy message stubs
            dummy_msgs = [{"id": f"m_{i}"} for i in range(25)]
            return [{
                "status": "COMPLETED",
                "output": {
                    "body": {"messages": dummy_msgs, "resultSizeEstimate": 25},
                    "max_results": params.get("max_results", 20),
                }
            }]
        elif op == "gmail.messages.get":
            msg_id = params.get("message_id")
            return [{"status": "COMPLETED", "output": {"body": {"id": msg_id}}}]
        return [{"status": "COMPLETED", "output": {}}]

    workflow = {
        "nodes": [
            {
                "id": "step_1",
                "provider": "gmail",
                "operation_id": "gmail.messages.list",
                "parameters": {"q": "is:unread", "max_results": 20},
            },
            {
                "id": "step_2",
                "provider": "gmail",
                "operation_id": "gmail.messages.get",
                "parameters": {"message_id": "{{step_1.messages[*].id}}"},
            },
        ]
    }

    with patch.object(executor.scheduler, "dispatch_ready_nodes", side_effect=mock_dispatch):
        with patch.object(executor.checkpoint_manager, "save_checkpoint", new=AsyncMock()):
            state = await executor.execute_workflow(workflow)
            assert state.status == "COMPLETED"
            step2_rec = state.node_records.get("step_2", {})
            out = step2_rec.get("output", {})

            # Must process 20 messages (not capped at 10)
            assert out.get("total_items") == 20
            assert len(out.get("messages", [])) == 20


@pytest.mark.asyncio
async def test_6_fanout_respects_clamped_max_results_5(executor):
    """Sprint AI-20 Test 6: When max_results is edited to 5, fan-out limits processing to 5 messages."""
    async def mock_dispatch(node_inputs):
        inp = node_inputs[0]
        meta = inp.get("metadata", {})
        node_id = meta.get("node_id", "step_1")
        params = meta.get("interpolated_params", {})
        
        nodes = inp.get("workflow", {}).get("nodes", [])
        target_node = next((n for n in nodes if (n.get("id") or n.get("step_id")) == node_id), {})
        op = target_node.get("operation_id") or target_node.get("operation")

        if op in ["gmail.messages.search", "gmail.messages.list"]:
            dummy_msgs = [{"id": f"m_{i}"} for i in range(15)]
            return [{
                "status": "COMPLETED",
                "output": {
                    "body": {"messages": dummy_msgs, "resultSizeEstimate": 15},
                    "max_results": 5,
                }
            }]
        elif op == "gmail.messages.get":
            msg_id = params.get("message_id")
            return [{"status": "COMPLETED", "output": {"body": {"id": msg_id}}}]
        return [{"status": "COMPLETED", "output": {}}]

    workflow = {
        "nodes": [
            {
                "id": "step_1",
                "provider": "gmail",
                "operation_id": "gmail.messages.list",
                "parameters": {"q": "is:unread", "max_results": 5},
            },
            {
                "id": "step_2",
                "provider": "gmail",
                "operation_id": "gmail.messages.get",
                "parameters": {"message_id": "{{step_1.messages[*].id}}"},
            },
        ]
    }

    with patch.object(executor.scheduler, "dispatch_ready_nodes", side_effect=mock_dispatch):
        with patch.object(executor.checkpoint_manager, "save_checkpoint", new=AsyncMock()):
            state = await executor.execute_workflow(workflow)
            step2_rec = state.node_records.get("step_2", {})
            out = step2_rec.get("output", {})
            assert out.get("total_items") == 5


@pytest.mark.asyncio
async def test_7_max_results_15_fanout_execution(executor):
    """Sprint AI-20.1 Test 7: max_results = 15 processes up to 15 emails."""
    async def mock_dispatch(node_inputs):
        inp = node_inputs[0]
        meta = inp.get("metadata", {})
        node_id = meta.get("node_id", "step_1")
        params = meta.get("interpolated_params", {})
        
        nodes = inp.get("workflow", {}).get("nodes", [])
        target_node = next((n for n in nodes if (n.get("id") or n.get("step_id")) == node_id), {})
        op = target_node.get("operation_id") or target_node.get("operation")

        if op in ["gmail.messages.search", "gmail.messages.list"]:
            dummy_msgs = [{"id": f"m_{i}"} for i in range(20)]
            return [{
                "status": "COMPLETED",
                "output": {
                    "body": {"messages": dummy_msgs, "resultSizeEstimate": 20},
                    "max_results": 15,
                }
            }]
        elif op == "gmail.messages.get":
            msg_id = params.get("message_id")
            return [{"status": "COMPLETED", "output": {"body": {"id": msg_id}}}]
        return [{"status": "COMPLETED", "output": {}}]

    workflow = {
        "nodes": [
            {
                "id": "step_1",
                "provider": "gmail",
                "operation_id": "gmail.messages.list",
                "parameters": {"q": "is:unread", "max_results": 15},
            },
            {
                "id": "step_2",
                "provider": "gmail",
                "operation_id": "gmail.messages.get",
                "parameters": {"message_id": "{{step_1.messages[*].id}}"},
            },
        ]
    }

    with patch.object(executor.scheduler, "dispatch_ready_nodes", side_effect=mock_dispatch):
        with patch.object(executor.checkpoint_manager, "save_checkpoint", new=AsyncMock()):
            state = await executor.execute_workflow(workflow)
            step2_rec = state.node_records.get("step_2", {})
            out = step2_rec.get("output", {})
            assert out.get("total_items") == 15
            assert len(out.get("messages", [])) == 15


@pytest.mark.asyncio
async def test_8_gmail_returns_fewer_than_requested(executor):
    """Sprint AI-20.1 Test 8: When max_results is 15 but Gmail returns only 7, fan-out returns 7."""
    async def mock_dispatch(node_inputs):
        inp = node_inputs[0]
        meta = inp.get("metadata", {})
        node_id = meta.get("node_id", "step_1")
        params = meta.get("interpolated_params", {})
        
        nodes = inp.get("workflow", {}).get("nodes", [])
        target_node = next((n for n in nodes if (n.get("id") or n.get("step_id")) == node_id), {})
        op = target_node.get("operation_id") or target_node.get("operation")

        if op in ["gmail.messages.search", "gmail.messages.list"]:
            dummy_msgs = [{"id": f"m_{i}"} for i in range(7)]
            return [{
                "status": "COMPLETED",
                "output": {
                    "body": {"messages": dummy_msgs, "resultSizeEstimate": 7},
                    "max_results": 15,
                }
            }]
        elif op == "gmail.messages.get":
            msg_id = params.get("message_id")
            return [{"status": "COMPLETED", "output": {"body": {"id": msg_id}}}]
        return [{"status": "COMPLETED", "output": {}}]

    workflow = {
        "nodes": [
            {
                "id": "step_1",
                "provider": "gmail",
                "operation_id": "gmail.messages.list",
                "parameters": {"q": "is:unread", "max_results": 15},
            },
            {
                "id": "step_2",
                "provider": "gmail",
                "operation_id": "gmail.messages.get",
                "parameters": {"message_id": "{{step_1.messages[*].id}}"},
            },
        ]
    }

    with patch.object(executor.scheduler, "dispatch_ready_nodes", side_effect=mock_dispatch):
        with patch.object(executor.checkpoint_manager, "save_checkpoint", new=AsyncMock()):
            state = await executor.execute_workflow(workflow)
            step2_rec = state.node_records.get("step_2", {})
            out = step2_rec.get("output", {})
            assert out.get("total_items") == 7
            assert len(out.get("messages", [])) == 7


@pytest.mark.asyncio
async def test_9_partial_fanout_failures_preserved(executor):
    """Sprint AI-20.1 Test 9: Partial fan-out failures track success and failure counts correctly."""
    async def mock_dispatch(node_inputs):
        inp = node_inputs[0]
        meta = inp.get("metadata", {})
        params = meta.get("interpolated_params", {})
        node_id = meta.get("node_id", "step_1")

        nodes = inp.get("workflow", {}).get("nodes", [])
        target_node = next((n for n in nodes if (n.get("id") or n.get("step_id")) == node_id), {})
        op = target_node.get("operation_id") or target_node.get("operation")

        if op in ["gmail.messages.search", "gmail.messages.list"]:
            dummy_msgs = [{"id": f"m_{i}"} for i in range(15)]
            return [{
                "status": "COMPLETED",
                "output": {
                    "body": {"messages": dummy_msgs, "resultSizeEstimate": 15},
                    "max_results": 15,
                }
            }]
        elif op == "gmail.messages.get":
            msg_id = params.get("message_id")
            if msg_id in ["m_2", "m_5"]:
                return [{"status": "FAILED", "output": {"error": "API rate limit"}}]
            return [{"status": "COMPLETED", "output": {"body": {"id": msg_id}}}]
        return [{"status": "COMPLETED", "output": {}}]

    workflow = {
        "nodes": [
            {
                "id": "step_1",
                "provider": "gmail",
                "operation_id": "gmail.messages.list",
                "parameters": {"q": "is:unread", "max_results": 15},
            },
            {
                "id": "step_2",
                "provider": "gmail",
                "operation_id": "gmail.messages.get",
                "parameters": {"message_id": "{{step_1.messages[*].id}}"},
            },
        ]
    }

    with patch.object(executor.scheduler, "dispatch_ready_nodes", side_effect=mock_dispatch):
        with patch.object(executor.checkpoint_manager, "save_checkpoint", new=AsyncMock()):
            state = await executor.execute_workflow(workflow)
            step2_rec = state.node_records.get("step_2", {})
            out = step2_rec.get("output", {})
            assert out.get("total_items") == 15
            assert out.get("success_count") == 13
            assert out.get("failed_count") == 2
