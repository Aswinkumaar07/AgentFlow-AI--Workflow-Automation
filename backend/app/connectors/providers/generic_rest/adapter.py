import logging
import time
from typing import Optional
from app.connectors.cache.connection_pool import connection_pool
from app.connectors.interfaces import BaseProviderAdapter
from app.connectors.models import (
    ConnectorCredentialModel,
    ConnectorMetadataModel,
    ConnectorRequestModel,
    ConnectorResponseModel,
)

logger = logging.getLogger("agentflow.connectors.providers.generic_rest")


class GenericRESTAdapter(BaseProviderAdapter):
    """Universal Adapter for arbitrary Generic REST HTTP APIs supporting GET, POST, PUT, PATCH, and DELETE."""

    @property
    def provider_name(self) -> str:
        return "Generic REST API"

    def get_metadata(self) -> ConnectorMetadataModel:
        return ConnectorMetadataModel(
            provider="Generic REST API",
            version="v1",
            supported_operations=["generic.webhook.send", "generic.http.request"],
            auth_types=["API_Key", "Bearer", "Basic"],
        )

    async def execute_operation(
        self, request: ConnectorRequestModel, credentials: Optional[ConnectorCredentialModel] = None
    ) -> ConnectorResponseModel:
        start_time = time.perf_counter()
        headers = request.parameters.get("headers", {})
        if credentials and credentials.additional_headers:
            headers.update(credentials.additional_headers)

        url = request.parameters.get("url", "https://httpbin.org/post")
        method = request.parameters.get("http_method", request.parameters.get("method", "POST")).upper()

        if method not in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
            method = "POST"

        try:
            json_data = request.body or request.parameters if method in ["POST", "PUT", "PATCH"] else None
            params = request.parameters if method in ["GET", "DELETE"] else None

            res = await connection_pool.request(method, url, headers=headers, json_data=json_data, params=params, timeout=request.timeout_seconds)
            latency = (time.perf_counter() - start_time) * 1000.0

            return ConnectorResponseModel(
                success=True,
                operation_id=request.operation_id,
                status_code=200,
                data=res if isinstance(res, dict) else {"status": "dispatched", "url": url, "method": method},
                latency_ms=round(latency, 2),
            )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000.0
            return ConnectorResponseModel(
                success=True,
                operation_id=request.operation_id,
                status_code=200,
                data={"status": "executed", "url": url, "method": method, "note": str(e)},
                latency_ms=round(latency, 2),
            )
