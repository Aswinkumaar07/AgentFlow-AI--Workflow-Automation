import json
import socket
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.agents.api_discovery.fetcher import (
    HTTPFetchError,
    InvalidSpecContentError,
    InvalidURLError,
    ResponseTooLargeError,
    SpecFetcher,
    SpecFetchResult,
    SSRFBlockedError,
    TimeoutFetchError,
    UnsupportedContentTypeError,
)


@pytest.fixture
def fetcher():
    return SpecFetcher(allow_http_for_tests=False)


@pytest.mark.asyncio
async def test_valid_https_url_accepted(fetcher):
    # Public domain that resolves to public IP
    with patch("socket.getaddrinfo") as mock_dns:
        mock_dns.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))
        ]
        hostname = fetcher.validate_url("https://example.com/openapi.json")
        assert hostname == "example.com"


@pytest.mark.asyncio
async def test_http_scheme_rejected(fetcher):
    with pytest.raises(InvalidURLError) as exc_info:
        fetcher.validate_url("http://example.com/openapi.json")
    assert "HTTPS" in str(exc_info.value)


@pytest.mark.asyncio
async def test_localhost_rejected(fetcher):
    with pytest.raises(SSRFBlockedError) as exc_info:
        fetcher.validate_url("https://localhost/openapi.json")
    assert "localhost" in str(exc_info.value)


@pytest.mark.asyncio
async def test_127_0_0_1_rejected(fetcher):
    with pytest.raises(SSRFBlockedError) as exc_info:
        fetcher.validate_url("https://127.0.0.1:8000/openapi.json")
    assert "blocked for SSRF" in str(exc_info.value)


@pytest.mark.asyncio
async def test_private_ipv4_ranges_rejected(fetcher):
    private_ips = [
        "https://10.0.0.1/openapi.json",
        "https://192.168.1.50/openapi.json",
        "https://172.16.0.1/openapi.json",
    ]
    for url in private_ips:
        with pytest.raises(SSRFBlockedError):
            fetcher.validate_url(url)


@pytest.mark.asyncio
async def test_aws_metadata_ip_rejected(fetcher):
    with pytest.raises(SSRFBlockedError) as exc_info:
        fetcher.validate_url("https://169.254.169.254/latest/meta-data/")
    assert "169.254.169.254" in str(exc_info.value)


@pytest.mark.asyncio
async def test_private_ipv6_rejected(fetcher):
    with pytest.raises(SSRFBlockedError):
        fetcher._assert_ip_allowed(
            __import__("ipaddress").ip_address("::1")
        )
    with pytest.raises(SSRFBlockedError):
        fetcher._assert_ip_allowed(
            __import__("ipaddress").ip_address("fe80::1")
        )


@pytest.mark.asyncio
async def test_dns_resolving_to_private_ip_rejected(fetcher):
    with patch("socket.getaddrinfo") as mock_dns:
        # DNS returns internal private IP for external-looking domain
        mock_dns.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.10", 0))
        ]
        with pytest.raises(SSRFBlockedError) as exc_info:
            fetcher.validate_url("https://internal-spoofed-domain.com/spec.json")
        assert "private/reserved target IP" in str(exc_info.value)


@pytest.mark.asyncio
async def test_timeout_handled(fetcher):
    with patch.object(fetcher, "validate_url", return_value="api.example.com"):
        with patch(
            "httpx.AsyncClient.send",
            side_effect=httpx.ReadTimeout("Read timeout occurred"),
        ):
            with pytest.raises(TimeoutFetchError) as exc_info:
                await fetcher.fetch("https://api.example.com/spec.json")
            assert "timeout" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_oversized_response_rejected():
    strict_fetcher = SpecFetcher(
        max_size_bytes=100, allow_http_for_tests=False
    )

    valid_openapi = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0"},
        "paths": {"/test": {"get": {"summary": "A" * 200}}},
    }
    large_payload = json.dumps(valid_openapi).encode("utf-8")

    async def mock_iter_bytes():
        yield large_payload

    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "application/json"}
    mock_resp.aiter_bytes = mock_iter_bytes
    mock_resp.aclose = AsyncMock()

    with patch.object(
        strict_fetcher, "validate_url", return_value="api.example.com"
    ):
        with patch("httpx.AsyncClient.send", return_value=mock_resp):
            with pytest.raises(ResponseTooLargeError) as exc_info:
                await strict_fetcher.fetch("https://api.example.com/spec.json")
            assert "exceeded maximum limit" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_valid_json_accepted(fetcher):
    valid_openapi = {
        "openapi": "3.0.0",
        "info": {"title": "Payment API", "version": "v1"},
        "paths": {
            "/v1/charge": {
                "post": {
                    "summary": "Create charge",
                    "parameters": [{"name": "amount", "required": True}],
                }
            }
        },
    }
    payload_bytes = json.dumps(valid_openapi).encode("utf-8")

    async def mock_iter_bytes():
        yield payload_bytes

    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.headers = {
        "Content-Type": "application/json",
        "Content-Length": str(len(payload_bytes)),
    }
    mock_resp.aiter_bytes = mock_iter_bytes
    mock_resp.aclose = AsyncMock()

    with patch.object(
        fetcher, "validate_url", return_value="api.example.com"
    ):
        with patch("httpx.AsyncClient.send", return_value=mock_resp):
            res: SpecFetchResult = await fetcher.fetch(
                "https://api.example.com/openapi.json"
            )
            assert res.status_code == 200
            assert res.format_hint == "json"
            assert "Payment API" in res.content


@pytest.mark.asyncio
async def test_valid_yaml_accepted(fetcher):
    yaml_spec = """
openapi: 3.0.0
info:
  title: Weather API
  version: 1.0.0
paths:
  /v1/forecast:
    get:
      summary: Get weather forecast
"""
    payload_bytes = yaml_spec.encode("utf-8")

    async def mock_iter_bytes():
        yield payload_bytes

    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "application/yaml"}
    mock_resp.aiter_bytes = mock_iter_bytes
    mock_resp.aclose = AsyncMock()

    with patch.object(
        fetcher, "validate_url", return_value="api.example.com"
    ):
        with patch("httpx.AsyncClient.send", return_value=mock_resp):
            res: SpecFetchResult = await fetcher.fetch(
                "https://api.example.com/openapi.yaml"
            )
            assert res.status_code == 200
            assert res.format_hint == "yaml"
            assert "Weather API" in res.content


@pytest.mark.asyncio
async def test_html_content_rejected(fetcher):
    html_payload = b"<!DOCTYPE html><html><body>404 Not Found</body></html>"

    async def mock_iter_bytes():
        yield html_payload

    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "text/html"}
    mock_resp.aiter_bytes = mock_iter_bytes
    mock_resp.aclose = AsyncMock()

    with patch.object(
        fetcher, "validate_url", return_value="api.example.com"
    ):
        with patch("httpx.AsyncClient.send", return_value=mock_resp):
            with pytest.raises(UnsupportedContentTypeError) as exc_info:
                await fetcher.fetch("https://api.example.com/spec.html")
            assert "HTML document" in str(exc_info.value)


@pytest.mark.asyncio
async def test_http_404_handled(fetcher):
    mock_resp = AsyncMock()
    mock_resp.status_code = 404
    mock_resp.headers = {}
    mock_resp.aclose = AsyncMock()

    with patch.object(
        fetcher, "validate_url", return_value="api.example.com"
    ):
        with patch("httpx.AsyncClient.send", return_value=mock_resp):
            with pytest.raises(HTTPFetchError) as exc_info:
                await fetcher.fetch("https://api.example.com/missing.json")
            assert "404" in str(exc_info.value)


@pytest.mark.asyncio
async def test_http_500_handled(fetcher):
    mock_resp = AsyncMock()
    mock_resp.status_code = 500
    mock_resp.headers = {}
    mock_resp.aclose = AsyncMock()

    with patch.object(
        fetcher, "validate_url", return_value="api.example.com"
    ):
        with patch("httpx.AsyncClient.send", return_value=mock_resp):
            with pytest.raises(HTTPFetchError) as exc_info:
                await fetcher.fetch("https://api.example.com/error.json")
            assert "500" in str(exc_info.value)


@pytest.mark.asyncio
async def test_redirect_to_ssrf_target_rejected(fetcher):
    mock_redirect_resp = AsyncMock()
    mock_redirect_resp.status_code = 302
    mock_redirect_resp.headers = {"Location": "https://127.0.0.1/secret.json"}
    mock_redirect_resp.aclose = AsyncMock()

    with patch.object(
        fetcher, "validate_url", side_effect=[True, SSRFBlockedError("Blocked 127.0.0.1")]
    ):
        with patch("httpx.AsyncClient.send", return_value=mock_redirect_resp):
            with pytest.raises(SSRFBlockedError):
                await fetcher.fetch("https://api.example.com/redirect")
