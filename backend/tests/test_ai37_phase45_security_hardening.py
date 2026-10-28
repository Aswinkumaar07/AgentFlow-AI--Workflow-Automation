import os
import socket
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import httpx
from app.agents.api_discovery.fetcher import (
    SpecFetcher,
    SSRFBlockedError,
    InvalidURLError,
    PinnedNetworkBackend,
    SecurePinnedTransport,
)
from app.runtime.live_node_executor import live_node_executor


# ---------------------------------------------------------------------------
# 1. DNS REBINDING & DESTINATION PINNING TESTS
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dns_rebinding_connection_time_rejection():
    """
    Simulates DNS rebinding attack:
    Initial validation sees public IP, but connect_tcp time DNS resolution returns 127.0.0.1.
    PinnedNetworkBackend must catch the private IP at connect_tcp time and raise SSRFBlockedError.
    """
    backend = PinnedNetworkBackend(allow_http_for_tests=False)

    with patch("asyncio.get_running_loop") as mock_loop_getter:
        mock_loop = MagicMock()
        mock_loop_getter.return_value = mock_loop
        # Mock getaddrinfo returning 127.0.0.1 at connection time
        mock_loop.getaddrinfo = AsyncMock(return_value=[
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))
        ])

        with pytest.raises(SSRFBlockedError) as exc_info:
            await backend.connect_tcp("rebound-domain.com", 443)

        assert "blocked for SSRF security" in str(exc_info.value)
        assert "127.0.0.1" in str(exc_info.value)


@pytest.mark.asyncio
async def test_private_ip_rejection_at_network_level():
    """Verifies that connect_tcp blocks private IPv4 and IPv6 targets."""
    backend = PinnedNetworkBackend(allow_http_for_tests=False)
    private_ips = ["10.0.0.5", "192.168.1.1", "172.16.0.1", "169.254.169.254", "::1"]

    for priv_ip in private_ips:
        with patch("asyncio.get_running_loop") as mock_loop_getter:
            mock_loop = MagicMock()
            mock_loop_getter.return_value = mock_loop
            mock_loop.getaddrinfo = AsyncMock(return_value=[
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", (priv_ip, 443))
            ])

            with pytest.raises(SSRFBlockedError):
                await backend.connect_tcp("internal-host.com", 443)


# ---------------------------------------------------------------------------
# 2. REMOVAL OF SYNTHETIC HTTPBIN.ORG SUCCESS FALLBACK TESTS
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [400, 401, 403, 404, 500])
async def test_httpbin_failures_remain_failed(status_code):
    """
    Proves that HTTP 4xx and 5xx responses for httpbin.org URLs remain FAILED.
    No synthetic SUCCESS fallback is executed.
    """
    node = {
        "id": "step_httpbin_fail",
        "provider": "generic_rest",
        "operation_id": "postData",
        "parameters": {
            "url": "https://httpbin.org/status/" + str(status_code),
            "method": "POST",
        },
    }

    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.is_success = False
    mock_resp.text = f"HTTP {status_code} Error"
    mock_resp.json.side_effect = Exception("Not JSON")
    mock_resp.headers = {}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        res = await live_node_executor.execute_node(node)

        assert res.status == "FAILED"
        assert res.status_code == status_code
        assert len(res.errors) > 0
        assert str(status_code) in res.errors[0]


@pytest.mark.asyncio
async def test_httpbin_network_exception_remains_failed():
    """Proves that network exceptions on httpbin.org URLs remain FAILED."""
    node = {
        "id": "step_httpbin_net_err",
        "provider": "generic_rest",
        "operation_id": "postData",
        "parameters": {
            "url": "https://httpbin.org/delay/10",
            "method": "POST",
        },
    }

    with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection timed out")):
        res = await live_node_executor.execute_node(node)

        assert res.status == "FAILED"
        assert res.status_code == 500
        assert len(res.errors) > 0
        assert "Network Exception" in res.errors[0]


# ---------------------------------------------------------------------------
# 3. CREDENTIAL REDACTION IN EXECUTION HISTORY TESTS
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execution_history_credential_redaction():
    """
    Verifies that sensitive request headers, query parameters, and payload fields
    are redacted in the returned LiveNodeExecutionResult request record.
    """
    node = {
        "id": "step_redact_test",
        "provider": "generic_rest",
        "operation_id": "secureOp",
        "parameters": {
            "url": "https://api.example.com/v1/data?api_key=secret_12345&access_token=tok_999&filter=active",
            "method": "POST",
            "user_id": "usr_777",
            "secret_key": "super_secret_val",
            "nested_config": {
                "password": "my_password_123",
                "client_id": "public_client_id",
            },
        },
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.is_success = True
    mock_resp.json.return_value = {"status": "ok"}
    mock_resp.headers = {}

    with patch("socket.getaddrinfo") as mock_dns:
        mock_dns.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))
        ]
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp
            res = await live_node_executor.execute_node(node)

            assert res.status == "SUCCESS"
            req_record = res.request

            # 1. URL Query Parameter Redaction
            assert "secret_12345" not in req_record["url"]
            assert "tok_999" not in req_record["url"]
            assert "filter=active" in req_record["url"]

            # 2. Payload Redaction
            payload_params = req_record["payload"]["parameters"]
            assert payload_params["user_id"] == "usr_777"
            assert payload_params["secret_key"] == "***"
            assert payload_params["nested_config"]["password"] == "***"
            assert payload_params["nested_config"]["client_id"] == "public_client_id"


# ---------------------------------------------------------------------------
# 4. HTTPS ENFORCEMENT & TEST_MODE ENVIRONMENT GATING TESTS
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_production_http_scheme_rejected_despite_workflow_flag():
    """
    Proves that a workflow payload containing allow_http_for_tests=True CANNOT enable
    insecure HTTP when TEST_MODE environment variable is absent or False.
    """
    node = {
        "id": "step_insecure_http",
        "provider": "generic_rest",
        "operation_id": "insecureCall",
        "parameters": {
            "url": "http://insecure-server.com/api/v1",
            "method": "GET",
            "allow_http_for_tests": True,  # Attacker attempt in workflow payload
            "is_dynamic_api": True,
        },
    }

    with patch.dict(os.environ, {"TEST_MODE": "false", "ALLOW_HTTP_FOR_TESTS": "false"}, clear=False):
        res = await live_node_executor.execute_node(node)

        assert res.status == "FAILED"
        assert res.status_code == 400
        assert "SSRF Blocked" in res.errors[0]


@pytest.mark.asyncio
async def test_test_mode_environment_allows_http():
    """
    Verifies that when TEST_MODE=true is explicitly set in environment,
    HTTP scheme is allowed for local test execution.
    """
    node = {
        "id": "step_local_http",
        "provider": "generic_rest",
        "operation_id": "localCall",
        "parameters": {
            "url": "http://public-test-server.org/api",
            "method": "GET",
            "is_dynamic_api": True,
        },
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.is_success = True
    mock_resp.json.return_value = {"ok": True}
    mock_resp.headers = {}

    with patch.dict(os.environ, {"TEST_MODE": "true"}, clear=False):
        with patch("socket.getaddrinfo") as mock_dns:
            mock_dns.return_value = [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 80))
            ]
            with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
                mock_get.return_value = mock_resp
                res = await live_node_executor.execute_node(node)

                assert res.status == "SUCCESS"
                assert res.status_code == 200
