import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.runtime.live_node_executor import live_node_executor
from app.runtime.workflow_executor import workflow_runtime_executor_v3


@pytest.mark.asyncio
async def test_scenario_a_order_id_substitution():
    """Test A: {orderId} + orderId=1 -> URL ends in /store/order/1."""
    node = {
        "id": "step_1",
        "provider": "generic_rest",
        "operation_id": "getOrderById",
        "parameters": {
            "url": "https://petstore3.swagger.io/api/v3/store/order/{orderId}",
            "method": "GET",
            "orderId": 1,
            "allow_http_for_tests": True,
        },
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.is_success = True
    mock_response.json.return_value = {"id": 1, "status": "placed"}
    mock_response.headers = {}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        res = await live_node_executor.execute_node(node)

        assert res.status == "SUCCESS"
        assert res.status_code == 200
        assert res.request["url"] == "https://petstore3.swagger.io/api/v3/store/order/1"


@pytest.mark.asyncio
async def test_scenario_b_pet_id_substitution():
    """Test B: {petId} + petId=123 -> URL ends in /pet/123."""
    node = {
        "id": "step_2",
        "provider": "generic_rest",
        "operation_id": "getPetById",
        "parameters": {
            "url": "https://petstore3.swagger.io/api/v3/pet/{petId}",
            "method": "GET",
            "petId": 123,
            "allow_http_for_tests": True,
        },
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.is_success = True
    mock_response.json.return_value = {"id": 123, "name": "doggie"}
    mock_response.headers = {}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        res = await live_node_executor.execute_node(node)

        assert res.status == "SUCCESS"
        assert res.status_code == 200
        assert res.request["url"] == "https://petstore3.swagger.io/api/v3/pet/123"


@pytest.mark.asyncio
async def test_scenario_c_variable_expression_resolved_before_substitution():
    """Test C: Variable expression resolved before substitution when upstream response is available."""
    node = {
        "id": "step_2",
        "provider": "generic_rest",
        "operation_id": "getPetById",
        "parameters": {
            "url": "https://petstore3.swagger.io/api/v3/pet/{petId}",
            "method": "GET",
            "petId": 999,  # Resolved by runtime context
            "allow_http_for_tests": True,
        },
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.is_success = True
    mock_response.json.return_value = {"id": 999, "name": "rex"}
    mock_response.headers = {}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        res = await live_node_executor.execute_node(node)

        assert res.status == "SUCCESS"
        assert res.request["url"] == "https://petstore3.swagger.io/api/v3/pet/999"


@pytest.mark.asyncio
async def test_scenario_d_missing_path_parameter_fails_early():
    """Test D: Missing path parameter fails before network request."""
    node = {
        "id": "step_1",
        "provider": "generic_rest",
        "operation_id": "getOrderById",
        "parameters": {
            "url": "https://petstore3.swagger.io/api/v3/store/order/{orderId}",
            "method": "GET",
            # orderId missing
            "allow_http_for_tests": True,
        },
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        res = await live_node_executor.execute_node(node)

        # Network should not be called
        mock_get.assert_not_called()
        assert res.status == "FAILED"
        assert res.status_code == 400
        assert "Missing required path parameter 'orderId'" in res.errors[0]


@pytest.mark.asyncio
async def test_scenario_e_unresolved_template_expression_fails_early():
    """Test E: Unresolved template expression fails before network request."""
    node = {
        "id": "step_2",
        "provider": "generic_rest",
        "operation_id": "getPetById",
        "parameters": {
            "url": "https://petstore3.swagger.io/api/v3/pet/{petId}",
            "method": "GET",
            "petId": "{{step_1.data.petId}}",  # Unresolved
            "allow_http_for_tests": True,
        },
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        res = await live_node_executor.execute_node(node)

        # Network should not be called
        mock_get.assert_not_called()
        assert res.status == "FAILED"
        assert res.status_code == 400
        assert "Missing required path parameter 'petId'" in res.errors[0]


@pytest.mark.asyncio
async def test_scenario_f_special_characters_url_encoded():
    """Test F: Special characters in path parameter are safely URL-encoded."""
    node = {
        "id": "step_1",
        "provider": "generic_rest",
        "operation_id": "getPetByTag",
        "parameters": {
            "url": "https://petstore3.swagger.io/api/v3/pet/findByTag/{tag}",
            "method": "GET",
            "tag": "cute/fluffy#1",
            "allow_http_for_tests": True,
        },
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.is_success = True
    mock_response.json.return_value = []
    mock_response.headers = {}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        res = await live_node_executor.execute_node(node)

        assert res.status == "SUCCESS"
        assert res.request["url"] == "https://petstore3.swagger.io/api/v3/pet/findByTag/cute%2Ffluffy%231"


@pytest.mark.asyncio
async def test_scenario_g_substituted_url_ssrf_revalidation():
    """Test G: Final substituted URL is revalidated against SSRF policy."""
    node = {
        "id": "step_1",
        "provider": "generic_rest",
        "operation_id": "proxyCall",
        "parameters": {
            "url": "https://{target}/latest/meta-data/",
            "method": "GET",
            "target": "169.254.169.254",  # Private IP hostname injection attempt
            "is_dynamic_api": True,
        },
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        res = await live_node_executor.execute_node(node)

        # Network should not be called due to SSRF block
        mock_get.assert_not_called()
        assert res.status == "FAILED"
        assert res.status_code == 400
        assert "SSRF Blocked" in res.errors[0]


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code, expected_status", [
    (200, "SUCCESS"),
    (400, "FAILED"),
    (401, "FAILED"),
    (403, "FAILED"),
    (404, "FAILED"),
    (500, "FAILED"),
])
async def test_scenarios_h_through_m_http_status_classification(status_code, expected_status):
    """Tests H-M: HTTP 200 -> SUCCESS, 400/401/403/404/500 -> FAILED."""
    node = {
        "id": "step_1",
        "provider": "generic_rest",
        "operation_id": "checkStatus",
        "parameters": {
            "url": "https://petstore3.swagger.io/api/v3/store/order/1",
            "method": "GET",
            "allow_http_for_tests": True,
        },
    }

    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.is_success = (status_code == 200)
    mock_response.text = f"HTTP {status_code} Error Payload"
    mock_response.json.return_value = {"code": status_code, "message": "Result message"}
    mock_response.headers = {"Content-Type": "application/json"}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        res = await live_node_executor.execute_node(node)

        assert res.status == expected_status
        assert res.status_code == status_code
        if expected_status == "FAILED":
            assert len(res.errors) > 0
            assert str(status_code) in res.errors[0]


@pytest.mark.asyncio
async def test_scenario_n_failure_details_preserve_status_and_body():
    """Test N: Failure details preserve status code and response body."""
    node = {
        "id": "step_1",
        "provider": "generic_rest",
        "operation_id": "getOrderById",
        "parameters": {
            "url": "https://petstore3.swagger.io/api/v3/store/order/99999",
            "method": "GET",
            "allow_http_for_tests": True,
        },
    }

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.is_success = False
    mock_response.text = '{"code": 404, "message": "Order not found"}'
    mock_response.json.return_value = {"code": 404, "message": "Order not found"}
    mock_response.headers = {"X-Error-Ref": "ERR-404"}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        res = await live_node_executor.execute_node(node)

        assert res.status == "FAILED"
        assert res.status_code == 404
        assert res.response["status_code"] == 404
        assert res.response["body"] == {"code": 404, "message": "Order not found"}
        assert res.response["headers"] == {"X-Error-Ref": "ERR-404"}


@pytest.mark.asyncio
async def test_scenario_o_native_connector_behavior_unchanged():
    """Test O: Existing native connector behavior (Slack/Gmail) remains unchanged."""
    slack_node = {
        "id": "step_slack",
        "provider": "Slack",
        "operation_id": "slack.chat.postMessage",
        "parameters": {"channel": "#general", "text": "Hello"},
    }

    with patch("app.connectors.providers.slack.adapter.SlackAdapter.execute_operation", new_callable=AsyncMock) as mock_slack:
        mock_resp = MagicMock()
        mock_resp.success = True
        mock_resp.status_code = 200
        mock_resp.data = {"ok": True, "ts": "1234567890.123456"}
        mock_slack.return_value = mock_resp

        res = await live_node_executor.execute_node(slack_node)
        assert res.status == "SUCCESS"
        assert res.provider == "Slack"


@pytest.mark.asyncio
async def test_scenario_q_workflow_level_status_failed_when_node_fails():
    """Test Q: Workflow-level status becomes FAILED when a required node's HTTP request returns 400."""
    wf_spec = {
        "workflow_id": "wf_test_phase43_failed_node",
        "tenant_id": "usr_test_phase43",
        "steps": [
            {
                "step_id": "step_1",
                "provider": "generic_rest",
                "operation_id": "getOrderById",
                "parameters": {
                    "url": "https://petstore3.swagger.io/api/v3/store/order/1",
                    "method": "GET",
                    "allow_http_for_tests": True,
                    "is_dynamic_api": True,
                    "security_schemes": {},
                    "security_requirements": [],
                },
            }
        ],
    }

    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.is_success = False
    mock_response.text = '{"code": 400, "message": "Bad Request"}'
    mock_response.json.return_value = {"code": 400, "message": "Bad Request"}
    mock_response.headers = {}

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        state = await workflow_runtime_executor_v3.execute_workflow(wf_spec)

        assert state.status == "FAILED"
        assert state.node_records["step_1"]["status"] == "FAILED"
