import asyncio
import ipaddress
import json
import logging
import socket
import time
from typing import Any, Dict, Optional, Set, Tuple
from urllib.parse import urlparse

import httpcore
import httpx
import yaml
from pydantic import BaseModel

from app.agents.api_discovery.exceptions import APIDiscoveryError

logger = logging.getLogger("agentflow.api_discovery.fetcher")


class PinnedNetworkBackend(httpcore.AnyIOBackend):
    """
    httpcore network backend that performs DNS resolution immediately before connection,
    validates every resolved IP against SSRF boundaries, and pins the TCP socket connection
    to the validated IP while preserving the original hostname for TLS SNI / certificate validation.
    """

    def __init__(self, allow_http_for_tests: bool = False) -> None:
        super().__init__()
        self.allow_http_for_tests = allow_http_for_tests

    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: Optional[float] = None,
        local_address: Optional[str] = None,
        socket_options: Optional[list] = None,
    ) -> httpcore.AsyncNetworkStream:
        try:
            addr_info = await asyncio.get_running_loop().getaddrinfo(
                host, port, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM
            )
        except Exception as e:
            raise httpcore.ConnectError(f"DNS resolution failure for host '{host}': {e}")

        if not addr_info:
            raise httpcore.ConnectError(f"DNS resolution returned no addresses for host '{host}'.")

        for res in addr_info:
            ip_str = res[4][0]
            try:
                ip_obj = ipaddress.ip_address(ip_str)
            except ValueError:
                raise httpcore.ConnectError(f"Invalid IP address format: {ip_str}")

            if (
                ip_obj.is_private
                or ip_obj.is_loopback
                or ip_obj.is_link_local
                or ip_obj.is_multicast
                or ip_obj.is_reserved
                or ip_obj.is_unspecified
            ):
                raise SSRFBlockedError(
                    f"Access to private/reserved target IP '{ip_obj}' is blocked for SSRF security."
                )

        target_ip = addr_info[0][4][0]
        return await super().connect_tcp(
            host=target_ip,
            port=port,
            timeout=timeout,
            local_address=local_address,
            socket_options=socket_options,
        )


class SecurePinnedTransport(httpx.AsyncHTTPTransport):
    """
    httpx AsyncHTTPTransport that uses PinnedNetworkBackend to enforce DNS-pinning SSRF protection
    and ignore environment proxies that could bypass destination policy.
    """

    def __init__(self, allow_http_for_tests: bool = False, **kwargs) -> None:
        super().__init__(trust_env=False, **kwargs)
        self._pool = httpcore.AsyncConnectionPool(
            ssl_context=self._pool._ssl_context,
            max_connections=self._pool._max_connections,
            max_keepalive_connections=self._pool._max_keepalive_connections,
            keepalive_expiry=self._pool._keepalive_expiry,
            http1=self._pool._http1,
            http2=self._pool._http2,
            retries=self._pool._retries,
            local_address=self._pool._local_address,
            uds=self._pool._uds,
            network_backend=PinnedNetworkBackend(allow_http_for_tests=allow_http_for_tests),
            socket_options=self._pool._socket_options,
        )


# Maximum response size limit for OpenAPI specs (5 MB)
DEFAULT_MAX_SPEC_SIZE_BYTES = 5 * 1024 * 1024


class SpecFetcherError(APIDiscoveryError):
    """Base exception for OpenAPI Spec Fetcher errors."""

    pass


def validate_runtime_target_url(url: str, allow_http_for_tests: bool = False) -> bool:
    """
    Validates dynamic target URL against SSRF, forbidden hostnames, non-HTTPS schemes,
    and private IP addresses before dynamic REST execution.
    """
    fetcher = SpecFetcher(allow_http_for_tests=allow_http_for_tests)
    try:
        fetcher.validate_url(url)
        return True
    except Exception as e:
        logger.warning(f"[AI-37][SSRF_BLOCKED] Runtime target URL '{url}' rejected: {e}")
        return False


class InvalidURLError(SpecFetcherError):
    """Raised when the requested URL is malformed or uses an unsupported scheme."""

    pass


class SSRFBlockedError(SpecFetcherError):
    """Raised when a URL or resolved target IP violates SSRF security boundaries."""

    pass


class TimeoutFetchError(SpecFetcherError):
    """Raised when network fetch exceeds connection or read timeouts."""

    pass


class ResponseTooLargeError(SpecFetcherError):
    """Raised when remote specification payload exceeds maximum allowed byte size."""

    pass


class UnsupportedContentTypeError(SpecFetcherError):
    """Raised when the HTTP response header or payload is not JSON/YAML specification content."""

    pass


class InvalidSpecContentError(SpecFetcherError):
    """Raised when the fetched payload cannot be parsed as valid JSON/YAML or lacks spec keys."""

    pass


class HTTPFetchError(SpecFetcherError):
    """Raised when HTTP response status code indicates failure (4xx / 5xx)."""

    pass


class SpecFetchResult(BaseModel):
    requested_url: str
    final_url: str
    content: str
    content_type: str
    content_length: int
    status_code: int
    duration_ms: float
    format_hint: str = "json"  # "json" or "yaml"


class SpecFetcher:
    """
    AgentFlow AI - Secure Remote OpenAPI Specification Fetcher (AI-37 Phase 1)
    Retrieves remote OpenAPI/Swagger JSON/YAML documents over HTTPS with strict SSRF protection,
    hostname IP resolution verification, response size caps, timeout enforcement, and content validation.
    """

    FORBIDDEN_HOSTNAMES: Set[str] = {
        "localhost",
        "0.0.0.0",
        "127.0.0.1",
        "::1",
        "169.254.169.254",
        "metadata.google.internal",
        "metadata",
        "kubernetes.default",
        "kubernetes.default.svc",
    }

    ALLOWED_SCHEMES: Set[str] = {"https"}

    ALLOWED_CONTENT_TYPES: Set[str] = {
        "application/json",
        "application/yaml",
        "text/yaml",
        "text/x-yaml",
        "application/x-yaml",
        "text/plain",
        "text/json",
        "application/openapi+json",
        "application/openapi+yaml",
    }

    def __init__(
        self,
        max_size_bytes: int = DEFAULT_MAX_SPEC_SIZE_BYTES,
        connect_timeout: float = 5.0,
        read_timeout: float = 10.0,
        allow_http_for_tests: bool = False,
    ) -> None:
        self.max_size_bytes = max_size_bytes
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.allow_http_for_tests = allow_http_for_tests

    def sanitize_url_for_logging(self, url: str) -> str:
        """Removes query params or userinfo credentials from URL string for safe logging."""
        try:
            parsed = urlparse(url)
            sanitized_netloc = parsed.hostname or ""
            if parsed.port:
                sanitized_netloc += f":{parsed.port}"
            return f"{parsed.scheme}://{sanitized_netloc}{parsed.path}"
        except Exception:
            return "[SANITIZED_URL]"

    def validate_url(self, url: str) -> str:
        """
        Validates scheme, hostname, and resolves IP addresses to prevent SSRF vulnerabilities.
        Returns the validated hostname string.
        """
        if not url or not isinstance(url, str):
            raise InvalidURLError("URL must be a non-empty string.")

        try:
            parsed = urlparse(url)
        except Exception as e:
            raise InvalidURLError(f"Malformed URL structure: {e}")

        scheme = (parsed.scheme or "").lower()
        allowed_schemes = (
            self.ALLOWED_SCHEMES
            if not self.allow_http_for_tests
            else {"https", "http"}
        )
        if scheme not in allowed_schemes:
            raise InvalidURLError(
                f"Invalid URL scheme '{scheme}'. Remote API discovery requires HTTPS."
            )

        hostname = (parsed.hostname or "").lower().strip()
        if not hostname:
            raise InvalidURLError("URL must specify a valid hostname.")

        # String check against forbidden hostnames
        if (
            hostname in self.FORBIDDEN_HOSTNAMES
            or hostname.endswith(".local")
            or hostname.endswith(".internal")
        ):
            raise SSRFBlockedError(
                f"Access to forbidden hostname '{hostname}' is blocked for SSRF security."
            )

        # IP Address string validation & DNS Resolution
        try:
            # Check if host is direct IP address string
            ip_obj = ipaddress.ip_address(hostname)
            self._assert_ip_allowed(ip_obj)
        except ValueError:
            # Hostname string -> Resolve via DNS to check target IP
            try:
                addr_info = socket.getaddrinfo(
                    hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM
                )
                if not addr_info:
                    raise SSRFBlockedError(
                        f"DNS resolution returned no addresses for host '{hostname}'."
                    )
                for res in addr_info:
                    ip_str = res[4][0]
                    ip_obj = ipaddress.ip_address(ip_str)
                    self._assert_ip_allowed(ip_obj)
            except socket.gaierror as e:
                raise SSRFBlockedError(
                    f"DNS resolution failure for host '{hostname}': {e}"
                )

        return hostname

    def _assert_ip_allowed(
        self, ip: ipaddress.IPv4Address | ipaddress.IPv6Address
    ) -> None:
        """Verifies that IP address is not private, loopback, link-local, reserved, or multicast."""
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise SSRFBlockedError(
                f"Access to private/reserved target IP '{ip}' is blocked for SSRF security."
            )

    def validate_content_structure(self, content: str) -> Tuple[str, Dict[str, Any]]:
        """
        Performs lightweight validation of spec content.
        Verifies content is valid JSON or YAML and contains basic OpenAPI/Swagger keys.
        """
        if not content or not content.strip():
            raise InvalidSpecContentError("Empty response body received.")

        # Reject HTML responses
        stripped = content.strip().lower()
        if stripped.startswith("<html") or stripped.startswith("<!doctype html"):
            raise UnsupportedContentTypeError(
                "Server returned an HTML document instead of an OpenAPI specification."
            )

        spec_dict: Optional[Dict[str, Any]] = None
        format_hint = "json"

        # Try parsing as JSON first
        try:
            spec_dict = json.loads(content)
            format_hint = "json"
        except Exception:
            # Fallback to YAML parse
            try:
                spec_dict = yaml.safe_load(content)
                format_hint = "yaml"
            except Exception as e:
                raise InvalidSpecContentError(
                    f"Content is not valid JSON or YAML: {e}"
                )

        if not isinstance(spec_dict, dict):
            raise InvalidSpecContentError(
                "Specification payload must be a JSON/YAML object dictionary."
            )

        # Lightweight check for spec structure
        has_openapi = "openapi" in spec_dict or "swagger" in spec_dict
        has_paths = "paths" in spec_dict
        has_info = "info" in spec_dict
        has_endpoints = "endpoints" in spec_dict

        if not (
            has_openapi
            or has_paths
            or (has_info and "item" in spec_dict)
            or has_endpoints
        ):
            raise InvalidSpecContentError(
                "Payload is valid JSON/YAML but lacks OpenAPI/Swagger/Postman keys ('openapi', 'swagger', 'paths', 'info')."
            )

        return format_hint, spec_dict

    async def fetch(self, url: str) -> SpecFetchResult:
        """
        Retrieves remote OpenAPI spec over HTTPS with SSRF checks, timeout handling, and size limiting.
        """
        sanitized_url = self.sanitize_url_for_logging(url)
        logger.info(f"SpecFetcher initiating secure fetch for: {sanitized_url}")

        # 1. SSRF & Scheme Validation
        self.validate_url(url)

        start_time = time.perf_counter()
        timeout_config = httpx.Timeout(
            connect=self.connect_timeout,
            read=self.read_timeout,
            write=self.connect_timeout,
            pool=self.connect_timeout,
        )

        transport = SecurePinnedTransport(allow_http_for_tests=self.allow_http_for_tests)
        try:
            async with httpx.AsyncClient(
                transport=transport,
                timeout=timeout_config,
                follow_redirects=False,
                trust_env=False,
            ) as client:
                req_url = url
                current_redirects = 0
                max_redirects = 3

                while True:
                    try:
                        req = client.build_request(
                            "GET",
                            req_url,
                            headers={
                                "Accept": "application/json, application/yaml, text/yaml, */*"
                            },
                        )
                        resp = await client.send(req, stream=True)
                    except httpx.TimeoutException as te:
                        raise TimeoutFetchError(
                            f"Request timeout while fetching spec from {sanitized_url}: {te}"
                        )
                    except httpx.RequestError as re_err:
                        raise HTTPFetchError(
                            f"Network error while fetching spec from {sanitized_url}: {re_err}"
                        )

                    # Handle Redirects safely
                    if resp.status_code in (301, 302, 303, 307, 308):
                        location = resp.headers.get("Location")
                        await resp.aclose()
                        if not location:
                            raise HTTPFetchError(
                                f"Redirect status {resp.status_code} received without Location header."
                            )

                        current_redirects += 1
                        if current_redirects > max_redirects:
                            raise HTTPFetchError(
                                f"Exceeded maximum allowed redirects ({max_redirects})."
                            )

                        # Validate redirect destination for SSRF!
                        redirect_url = str(httpx.URL(req_url).join(location))
                        self.validate_url(redirect_url)
                        req_url = redirect_url
                        continue

                    break

                duration_ms = (time.perf_counter() - start_time) * 1000.0

                if resp.status_code >= 400:
                    await resp.aclose()
                    raise HTTPFetchError(
                        f"HTTP error {resp.status_code} received from remote server."
                    )

                # Content-Type check (soft validation)
                content_type = (
                    resp.headers.get("Content-Type", "")
                    .lower()
                    .split(";")[0]
                    .strip()
                )

                # Content-Length header check
                content_length_hdr = resp.headers.get("Content-Length")
                if content_length_hdr and content_length_hdr.isdigit():
                    if int(content_length_hdr) > self.max_size_bytes:
                        await resp.aclose()
                        raise ResponseTooLargeError(
                            f"Remote specification Content-Length ({content_length_hdr} bytes) exceeds maximum limit ({self.max_size_bytes} bytes)."
                        )

                # Stream response bytes with size guard
                chunks = []
                total_bytes = 0
                try:
                    async for chunk in resp.aiter_bytes():
                        total_bytes += len(chunk)
                        if total_bytes > self.max_size_bytes:
                            await resp.aclose()
                            raise ResponseTooLargeError(
                                f"Remote specification body exceeded maximum limit ({self.max_size_bytes} bytes) during streaming."
                            )
                        chunks.append(chunk)
                finally:
                    await resp.aclose()

                raw_bytes = b"".join(chunks)
                try:
                    content_str = raw_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    try:
                        content_str = raw_bytes.decode("latin-1")
                    except Exception as e:
                        raise InvalidSpecContentError(
                            f"Failed to decode spec content as text: {e}"
                        )

                # Validate structure
                format_hint, _ = self.validate_content_structure(content_str)

                logger.info(
                    f"SpecFetcher successfully retrieved {total_bytes} bytes from {sanitized_url} in {duration_ms:.2f}ms"
                )

                return SpecFetchResult(
                    requested_url=url,
                    final_url=req_url,
                    content=content_str,
                    content_type=content_type or "application/json",
                    content_length=total_bytes,
                    status_code=resp.status_code,
                    duration_ms=round(duration_ms, 2),
                    format_hint=format_hint,
                )

        except (SpecFetcherError, APIDiscoveryError):
            raise
        except Exception as e:
            raise SpecFetcherError(
                f"Unexpected error fetching remote specification: {e}"
            )


spec_fetcher = SpecFetcher()
