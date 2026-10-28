import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.connectors.providers.generic_rest.adapter import GenericRESTAdapter
from app.connectors.models import ConnectorRequestModel
from app.agents.api_discovery.fetcher import validate_runtime_target_url


def test_dynamic_get_filtering_removes_internal_metadata():
    adapter = GenericRESTAdapter()
    req = ConnectorRequestModel(
        operation_id="getInventory",
        parameters={
            "url": "https://petstore3.swagger.io/api/v3/store/inventory",
            "http_method": "GET",
            "method": "GET",
            "is_dynamic_api": True,
            "instruction": "Get the store inventory...",
            "auth_provider": "Generic_rest",
            "credential_id": None,
            "auth_account_label": None,
            "auth_status": "unbound",
            "allow_http_for_tests": True,
        }
    )

    with patch("app.agents.api_discovery.fetcher.validate_runtime_target_url", return_value=True), \
         patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"status": "available"}
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is True
        
        # Verify connection_pool.request call arguments
        mock_req.assert_called_once()
        args, kwargs = mock_req.call_args
        assert args[0] == "GET"
        assert args[1] == "https://petstore3.swagger.io/api/v3/store/inventory"
        assert kwargs["params"] is None  # No internal metadata leaked into params!


def test_legitimate_query_parameter_preservation():
    adapter = GenericRESTAdapter()
    req = ConnectorRequestModel(
        operation_id="findPetsByStatus",
        parameters={
            "url": "https://petstore3.swagger.io/api/v3/pet/findByStatus",
            "http_method": "GET",
            "method": "GET",
            "is_dynamic_api": True,
            "instruction": "Find pets by status...",
            "auth_provider": "Generic_rest",
            "auth_status": "unbound",
            "status": "available",
            "limit": 10,
            "allow_http_for_tests": True,
        }
    )

    with patch("app.agents.api_discovery.fetcher.validate_runtime_target_url", return_value=True), \
         patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = [{"id": 1, "name": "doggie"}]
        res = asyncio.run(adapter.execute_operation(req))
        assert res.success is True

        mock_req.assert_called_once()
        _, kwargs = mock_req.call_args
        sent_params = kwargs["params"]
        assert sent_params == {"status": "available", "limit": 10}
        
        # Verify internal control keys are absent
        internal_keys = ["url", "http_method", "method", "is_dynamic_api", "instruction", "auth_provider", "auth_status"]
        for key in internal_keys:
            assert key not in sent_params


def test_url_and_method_never_appear_in_outbound_params():
    adapter = GenericRESTAdapter()
    req = ConnectorRequestModel(
        operation_id="getInventory",
        parameters={
            "url": "https://petstore3.swagger.io/api/v3/store/inventory",
            "http_method": "GET",
            "method": "GET",
            "is_dynamic_api": True,
            "allow_http_for_tests": True,
        }
    )

    with patch("app.agents.api_discovery.fetcher.validate_runtime_target_url", return_value=True), \
         patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {}
        asyncio.run(adapter.execute_operation(req))
        _, kwargs = mock_req.call_args
        sent_params = kwargs.get("params") or {}
        assert "url" not in sent_params
        assert "http_method" not in sent_params
        assert "method" not in sent_params


def test_security_control_remains_intact():
    adapter = GenericRESTAdapter()
    ssrf_req = ConnectorRequestModel(
        operation_id="maliciousOp",
        parameters={
            "url": "http://169.254.169.254/latest/meta-data",
            "http_method": "GET",
            "is_dynamic_api": True,
        }
    )
    with patch("app.connectors.providers.generic_rest.adapter.connection_pool.request", new_callable=AsyncMock) as mock_req:
        res = asyncio.run(adapter.execute_operation(ssrf_req))
        assert res.success is False
        assert res.status_code == 400
        assert "SSRF Blocked" in res.data.get("error", "")
        mock_req.assert_not_called()
