import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.runtime.variable_store import VariableStore
from app.runtime.context import ExecutionContext
from app.runtime.live_node_executor import live_node_executor
from app.runtime.node_executor import node_executor


def test_variable_store_bidirectional_body_data_resolution():
    """
    Focused test: VariableStore resolves both .data and .body when output contains only body or only data.
    """
    vs = VariableStore()

    # Case A: Live HTTP execution output storing response JSON in body
    scope_http = {
        "step_1": {
            "status_code": 200,
            "body": {"petId": 10, "status": "available"},
            "headers": {"content-type": "application/json"}
        }
    }
    # Planner generates .data -> must resolve to 10
    assert vs._resolve_path("step_1.data.petId", scope_http) == 10
    # Direct .body reference -> must resolve to 10
    assert vs._resolve_path("step_1.body.petId", scope_http) == 10
    # Interpolation of full template expressions
    assert vs.interpolate("{{step_1.data.petId}}", scope_http) == 10
    assert vs.interpolate("{{step_1.body.petId}}", scope_http) == 10

    # Case B: Wrapped in output payload
    scope_wrapped = {
        "step_1": {
            "output": {
                "status_code": 200,
                "body": {"petId": 10}
            }
        }
    }
    assert vs._resolve_path("step_1.data.petId", scope_wrapped) == 10
    assert vs._resolve_path("step_1.body.petId", scope_wrapped) == 10
    assert vs.interpolate("{{step_1.data.petId}}", scope_wrapped) == 10
    assert vs.interpolate("{{step_1.body.petId}}", scope_wrapped) == 10

    # Case C: Backward-compatibility with legacy payload storing only 'data'
    scope_legacy = {
        "step_1": {
            "data": {"petId": 10}
        }
    }
    assert vs._resolve_path("step_1.data.petId", scope_legacy) == 10
    assert vs._resolve_path("step_1.body.petId", scope_legacy) == 10
    assert vs.interpolate("{{step_1.data.petId}}", scope_legacy) == 10
    assert vs.interpolate("{{step_1.body.petId}}", scope_legacy) == 10


def test_execution_context_interpolates_body_to_downstream_parameter():
    """
    Focused test: ExecutionContext interpolates {{step_1.data.petId}} into downstream parameter
    when previous_outputs has step_1 with body: {'petId': 10}.
    """
    ctx = ExecutionContext(
        execution_id="exec_test_var_bridge",
        workflow_id="wf_petstore_test",
    )
    # Simulate step_1 completion storing HTTP response body
    ctx.record_step_output("step_1", {
        "status_code": 200,
        "body": {"petId": 10, "name": "doggie"},
    })

    # Step 2 expects petId path parameter mapped via planner syntax {{step_1.data.petId}}
    node2_params = {
        "url": "https://petstore3.swagger.io/api/v3/pet/{petId}",
        "petId": "{{step_1.data.petId}}",
    }
    payload = ctx.build_node_input_payload("step_2", node2_params, {})

    # Assert petId is successfully interpolated from template to integer 10
    assert payload["parameters"]["petId"] == 10


@pytest.mark.asyncio
async def test_live_node_executor_substitutes_interpolated_path_parameter():
    """
    Focused test: End-to-end node execution verifies that an upstream response containing
    {'body': {'petId': 10}} supplies 10 to downstream node's required path parameter.
    """
    ctx = ExecutionContext(
        execution_id="exec_test_live_node",
        workflow_id="wf_petstore_e2e",
    )
    # Step 1 output recorded in context
    ctx.record_step_output("step_1", {
        "status_code": 200,
        "body": {"petId": 10},
    })

    # Step 2 node with template expression {{step_1.data.petId}}
    node2_def = {
        "id": "step_2",
        "provider": "generic_rest",
        "operation_id": "getPetById",
        "parameters": {
            "url": "https://petstore3.swagger.io/api/v3/pet/{petId}",
            "method": "GET",
            "petId": "{{step_1.data.petId}}",
            "allow_http_for_tests": True,
        },
    }

    # Context builds payload and interpolates petId to 10
    built_payload = ctx.build_node_input_payload("step_2", node2_def["parameters"], {"nodes": [node2_def]})
    assert built_payload["parameters"]["petId"] == 10

    # Execute node with interpolated parameters
    node_to_execute = dict(node2_def)
    node_to_execute["parameters"] = built_payload["parameters"]

    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.json = lambda: {"id": 10, "name": "doggie", "status": "available"}
    mock_resp.is_success = True

    with patch("httpx.AsyncClient.get", return_value=mock_resp) as mock_get:
        res = await live_node_executor.execute_node(node_to_execute)

        assert res.status == "SUCCESS"
        assert res.status_code == 200
        # Verify the requested URL had {petId} substituted with 10
        mock_get.assert_called_once()
        called_url = mock_get.call_args[0][0]
        assert called_url == "https://petstore3.swagger.io/api/v3/pet/10"
        # Verify response object has both body and data keys
        assert res.response["body"]["id"] == 10
        assert res.response["data"]["id"] == 10
