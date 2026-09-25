import asyncio
import logging
import time
from typing import Optional

from app.connectors.exceptions import (
    ConnectorError,
    ConnectorExecutionError,
    ConnectorRateLimitError,
    ConnectorTimeoutError,
    ConnectorUnavailableError,
)
from app.connectors.interfaces import BaseConnectorExecutor, BaseProviderAdapter
from app.connectors.models import (
    ConnectorCredentialModel,
    ConnectorRequestModel,
    ConnectorResponseModel,
)

logger = logging.getLogger("agentflow.connectors.execution.executor")


class ConnectorExecutor(BaseConnectorExecutor):
    """Enterprise Execution Engine for running connector operations through resilience pipeline."""

    async def execute(
        self,
        adapter: BaseProviderAdapter,
        request: ConnectorRequestModel,
        credentials: Optional[ConnectorCredentialModel] = None,
    ) -> ConnectorResponseModel:
        start_time = time.perf_counter()
        retries = 0
        max_retries = request.retry_attempts

        while retries <= max_retries:
            try:
                # Enforce async timeout
                res = await asyncio.wait_for(
                    adapter.execute_operation(request, credentials),
                    timeout=request.timeout_seconds,
                )
                latency = (time.perf_counter() - start_time) * 1000.0
                res.latency_ms = round(latency, 2)
                res.retries_used = retries
                return res

            except (ConnectorRateLimitError, ConnectorUnavailableError, ConnectorTimeoutError, asyncio.TimeoutError) as e:
                retries += 1
                if retries > max_retries:
                    latency = (time.perf_counter() - start_time) * 1000.0
                    logger.error(f"Execution failed after {max_retries} retries for operation '{request.operation_id}': {e}")
                    return ConnectorResponseModel(
                        success=False,
                        operation_id=request.operation_id,
                        status_code=getattr(e, "status_code", 500),
                        error_message=str(e),
                        latency_ms=round(latency, 2),
                        retries_used=retries - 1,
                    )

                # Exponential backoff sleep
                sleep_sec = (2 ** (retries - 1)) * 1.0
                logger.warning(
                    f"Retrying operation '{request.operation_id}' (Attempt {retries}/{max_retries}) after {sleep_sec}s due to error: {e}"
                )
                await asyncio.sleep(sleep_sec)

            except ConnectorError as e:
                latency = (time.perf_counter() - start_time) * 1000.0
                return ConnectorResponseModel(
                    success=False,
                    operation_id=request.operation_id,
                    status_code=e.status_code,
                    error_message=str(e),
                    latency_ms=round(latency, 2),
                    retries_used=retries,
                )

            except Exception as e:
                latency = (time.perf_counter() - start_time) * 1000.0
                return ConnectorResponseModel(
                    success=False,
                    operation_id=request.operation_id,
                    status_code=500,
                    error_message=f"Unhandled execution exception: {e}",
                    latency_ms=round(latency, 2),
                    retries_used=retries,
                )

        latency = (time.perf_counter() - start_time) * 1000.0
        return ConnectorResponseModel(
            success=False,
            operation_id=request.operation_id,
            status_code=500,
            error_message="Max execution retries exceeded.",
            latency_ms=round(latency, 2),
            retries_used=max_retries,
        )


connector_executor = ConnectorExecutor()
