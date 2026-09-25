import asyncio
import logging
from typing import Any, Dict, Optional
import httpx

from app.connectors.config import connector_config
from app.connectors.exceptions import (
    ConnectorAuthenticationError,
    ConnectorExecutionError,
    ConnectorRateLimitError,
    ConnectorTimeoutError,
    ConnectorUnavailableError,
)
from app.connectors.interfaces import BaseConnectionPool

logger = logging.getLogger("agentflow.connectors.cache.connection_pool")


class ConnectionPool(BaseConnectionPool):
    """High-Performance Persistent HTTP Connection Pool featuring HTTP/2, Keep-Alive, & TLS Reuse."""

    def __init__(self) -> None:
        self._client: Optional[httpx.AsyncClient] = None
        self._lock = asyncio.Lock()

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            async with self._lock:
                if self._client is None or self._client.is_closed:
                    limits = httpx.Limits(
                        max_connections=connector_config.MAX_CONNECTIONS,
                        max_keepalive_connections=connector_config.MAX_KEEPALIVE_CONNECTIONS,
                    )
                    timeout = httpx.Timeout(connector_config.DEFAULT_TIMEOUT_SECONDS)
                    try:
                        self._client = httpx.AsyncClient(limits=limits, timeout=timeout, http2=True)
                    except Exception:
                        self._client = httpx.AsyncClient(limits=limits, timeout=timeout, http2=False)
                    logger.info("Initialized persistent HTTP ConnectionPool client.")
        return self._client

    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Any] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        client = await self._get_client()

        try:
            res = await client.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=json_data,
                params=params,
                timeout=timeout,
            )

            status = res.status_code

            if status >= 200 and status < 300:
                try:
                    return res.json()
                except Exception:
                    return {"status": "success", "text": res.text}

            err_text = res.text[:300]
            if status == 401:
                raise ConnectorAuthenticationError(f"HTTP 401 Unauthorized: {err_text}")
            if status == 429:
                raise ConnectorRateLimitError(f"HTTP 429 Rate Limit Exceeded: {err_text}")
            if status in [502, 503, 504]:
                raise ConnectorUnavailableError(f"HTTP {status} Provider Unavailable: {err_text}")

            raise ConnectorExecutionError(f"HTTP {status} Connector Execution Error: {err_text}", status_code=status)

        except httpx.TimeoutException as e:
            raise ConnectorTimeoutError(f"Connector request timed out after {timeout}s: {e}") from e
        except (ConnectorAuthenticationError, ConnectorRateLimitError, ConnectorUnavailableError, ConnectorExecutionError):
            raise
        except Exception as e:
            raise ConnectorExecutionError(f"Connection pool request error: {e}", original_error=e) from e

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            logger.info("Closed ConnectionPool HTTP client.")


connection_pool = ConnectionPool()
