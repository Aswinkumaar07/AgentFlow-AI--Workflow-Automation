import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.runtime.workflow_executor import workflow_runtime_executor_v3
from app.runtime.variable_store import VariableStore
from app.api.v1.runtime import execute_full_workflow_dag

@pytest.mark.asyncio
async def test_execute_single_node_workflow():
    """Test 1: Single node workflow execution."""
    spec = {
        "workflow_id": "wf_single_node",
        "steps": [
            {
                "step_id": "step_1",
                "provider": "Gmail",
                "operation_id": "gmail.messages.list",
                "parameters": {"q": "is:unread"},
                "dependencies": []
            }
        ]
    }
    
    mock_res = {
        "status_code": 200,
        "latency_ms": 45.2,
        "response": {"messages": [{"id": "msg_001"}]},
        "body": {"messages": [{"id": "msg_001"}]},
        "messageId": "msg_001",
    }
    
    with patch("app.runtime.node_executor.connector_manager.execute", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = AsyncMock(status_code=200, success=True, data=mock_res["response"], error_message=None)
        state = await workflow_runtime_executor_v3.execute_workflow(spec)
        
        assert state.status == "COMPLETED"
        assert "step_1" in state.node_records
        assert state.node_records["step_1"]["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_execute_two_node_dag():
    """Test 2: Two node DAG execution."""
    spec = {
        "workflow_id": "wf_two_node",
        "steps": [
            {
                "step_id": "step_1",
                "provider": "Gmail",
                "operation_id": "gmail.messages.list",
                "parameters": {"q": "is:unread"},
                "dependencies": []
            },
            {
                "step_id": "step_2",
                "provider": "Gmail",
                "operation_id": "gmail.messages.get",
                "parameters": {"message_id": "{{step_1.messages[0].id}}"},
                "dependencies": ["step_1"]
            }
        ]
    }
    
    list_output = {"messages": [{"id": "1a032c70b2090044"}]}
    get_output = {"id": "1a032c70b2090044", "snippet": "Hello World"}
    
    async def mock_connector_execute(provider, operation_id, parameters, tenant_id):
        if operation_id == "gmail.messages.list":
            return AsyncMock(status_code=200, success=True, data=list_output, error_message=None)
        else:
            return AsyncMock(status_code=200, success=True, data=get_output, error_message=None)
            
    with patch("app.runtime.node_executor.connector_manager.execute", side_effect=mock_connector_execute):
        state = await workflow_runtime_executor_v3.execute_workflow(spec)
        assert state.status == "COMPLETED"
        assert len(state.node_records) == 2
        assert state.node_records["step_1"]["status"] == "COMPLETED"
        assert state.node_records["step_2"]["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_dag_execution_order():
    """Test 3: Verify DAG nodes execute in strict topological order (step_1 before step_2)."""
    execution_order = []
    
    async def mock_execute(provider, operation_id, parameters, tenant_id):
        execution_order.append(operation_id)
        return AsyncMock(status_code=200, success=True, data={"result": "ok", "messages": [{"id": "abc"}]}, error_message=None)
        
    spec = {
        "workflow_id": "wf_order",
        "steps": [
            {"step_id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.list", "parameters": {}, "dependencies": []},
            {"step_id": "step_2", "provider": "Gmail", "operation_id": "gmail.messages.get", "parameters": {"message_id": "{{step_1.messages[0].id}}"}, "dependencies": ["step_1"]},
        ]
    }
    
    with patch("app.runtime.node_executor.connector_manager.execute", side_effect=mock_execute):
        await workflow_runtime_executor_v3.execute_workflow(spec)
        assert execution_order == ["gmail.messages.list", "gmail.messages.get"]


@pytest.mark.asyncio
async def test_node_output_propagation():
    """Test 4: Node 1 output is stored and accessible in context."""
    spec = {
        "workflow_id": "wf_prop",
        "steps": [
            {"step_id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.list", "parameters": {}, "dependencies": []}
        ]
    }
    list_output = {"messages": [{"id": "test_msg_99"}]}
    with patch("app.runtime.node_executor.connector_manager.execute", return_value=AsyncMock(status_code=200, success=True, data=list_output, error_message=None)):
        state = await workflow_runtime_executor_v3.execute_workflow(spec)
        assert "step_1" in state.context_data
        assert state.context_data["step_1"]["response"]["messages"][0]["id"] == "test_msg_99"


@pytest.mark.asyncio
async def test_template_variable_resolution():
    """Test 5: VariableStore resolves bracket indexed template expressions."""
    vs = VariableStore()
    scope = {
        "step_1": {
            "messages": [{"id": "1a032c70b2090044"}]
        }
    }
    target_params = {"message_id": "{{step_1.messages[0].id}}"}
    resolved = vs.interpolate(target_params, scope)
    assert resolved["message_id"] == "1a032c70b2090044"


@pytest.mark.asyncio
async def test_second_node_receives_first_output():
    """Test 6: Node 2 receives resolved parameter from Node 1 output."""
    received_params = []
    
    async def mock_execute(provider, operation_id, parameters, tenant_id):
        received_params.append(parameters)
        if operation_id == "gmail.messages.list":
            return AsyncMock(status_code=200, success=True, data={"messages": [{"id": "msg_real_123"}]}, error_message=None)
        return AsyncMock(status_code=200, success=True, data={"id": "msg_real_123", "snippet": "Body"}, error_message=None)

    spec = {
        "workflow_id": "wf_receive",
        "steps": [
            {"step_id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.list", "parameters": {}, "dependencies": []},
            {"step_id": "step_2", "provider": "Gmail", "operation_id": "gmail.messages.get", "parameters": {"message_id": "{{step_1.messages[0].id}}"}, "dependencies": ["step_1"]},
        ]
    }
    
    with patch("app.runtime.node_executor.connector_manager.execute", side_effect=mock_execute):
        await workflow_runtime_executor_v3.execute_workflow(spec)
        assert len(received_params) == 2
        assert received_params[1]["message_id"] == "msg_real_123"


@pytest.mark.asyncio
async def test_workflow_execution_result_contains_all_nodes():
    """Test 7: Workflow execution result API returns all node results."""
    spec = {
        "workflow_id": "wf_result_all",
        "steps": [
            {"step_id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.list", "parameters": {}, "dependencies": []},
            {"step_id": "step_2", "provider": "Gmail", "operation_id": "gmail.messages.get", "parameters": {"message_id": "{{step_1.messages[0].id}}"}, "dependencies": ["step_1"]},
        ]
    }
    
    async def mock_execute(provider, operation_id, parameters, tenant_id):
        return AsyncMock(status_code=200, success=True, data={"messages": [{"id": "msg_77"}]}, error_message=None)

    with patch("app.runtime.node_executor.connector_manager.execute", side_effect=mock_execute):
        res = await execute_full_workflow_dag(spec)
        assert res["success"] is True
        assert res["nodes_executed"] == 2
        assert len(res["node_results"]) == 2
        assert res["node_results"][0]["node_id"] == "step_1"
        assert res["node_results"][1]["node_id"] == "step_2"


@pytest.mark.asyncio
async def test_final_output_contains_last_node():
    """Test 8: final_output field in response contains output of last node."""
    spec = {
        "workflow_id": "wf_final_out",
        "steps": [
            {"step_id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.list", "parameters": {}, "dependencies": []},
            {"step_id": "step_2", "provider": "Gmail", "operation_id": "gmail.messages.get", "parameters": {"message_id": "{{step_1.messages[0].id}}"}, "dependencies": ["step_1"]},
        ]
    }
    
    async def mock_execute(provider, operation_id, parameters, tenant_id):
        if operation_id == "gmail.messages.list":
            return AsyncMock(status_code=200, success=True, data={"messages": [{"id": "m1"}]}, error_message=None)
        return AsyncMock(status_code=200, success=True, data={"id": "m1", "subject": "Test Email Subject"}, error_message=None)

    with patch("app.runtime.node_executor.connector_manager.execute", side_effect=mock_execute):
        res = await execute_full_workflow_dag(spec)
        assert res["final_output"]["response"]["subject"] == "Test Email Subject"


@pytest.mark.asyncio
async def test_dependency_failure_stops_downstream_node():
    """Test 9: If Node 1 fails, Node 2 is SKIPPED and workflow status is FAILED."""
    async def mock_execute(provider, operation_id, parameters, tenant_id):
        return AsyncMock(status_code=500, success=False, data={"error": "Gmail API Error"}, error_message="Gmail API Error")

    spec = {
        "workflow_id": "wf_fail",
        "steps": [
            {"step_id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.list", "parameters": {}, "dependencies": []},
            {"step_id": "step_2", "provider": "Gmail", "operation_id": "gmail.messages.get", "parameters": {"message_id": "{{step_1.messages[0].id}}"}, "dependencies": ["step_1"]},
        ]
    }
    
    with patch("app.runtime.node_executor.connector_manager.execute", side_effect=mock_execute):
        res = await execute_full_workflow_dag(spec)
        assert res["success"] is False
        assert res["status"] == "FAILED"
        assert res["nodes_executed"] == 0
        assert res["node_results"][1]["status"] == "SKIPPED"


@pytest.mark.asyncio
async def test_execute_button_uses_workflow_executor():
    """Test 10: Top-level execute endpoint invokes workflow_runtime_executor_v3."""
    spec = {
        "workflow_id": "wf_execute_button",
        "nodes": [
            {"id": "step_1", "provider": "Gmail", "operation_id": "gmail.messages.list", "parameters": {}}
        ]
    }
    with patch("app.runtime.node_executor.connector_manager.execute", return_value=AsyncMock(status_code=200, success=True, data={"messages": []}, error_message=None)):
        res = await execute_full_workflow_dag(spec)
        assert res["status"] == "COMPLETED"
        assert res["nodes_executed"] == 1
