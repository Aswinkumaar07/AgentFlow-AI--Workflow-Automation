import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from app.connectors.interfaces import BaseProviderAdapter
from app.connectors.models import (
    ConnectorCredentialModel,
    ConnectorMetadataModel,
    ConnectorRequestModel,
    ConnectorResponseModel,
)

logger = logging.getLogger("agentflow.connectors.base")


class BaseConnector(BaseProviderAdapter, ABC):
    """Enterprise SDK Base Class for all SaaS Provider Connectors.

    Provides standardized lifecycle hooks:
    - authentication(): Configures and validates request headers/credentials.
    - validate(): Enforces request parameter schema validation.
    - serialize(): Transforms python objects into wire format (JSON/XML).
    - deserialize(): Transforms wire format into structured python response.
    - execute(): Executes the operation over the persistent connection pool.
    - retry(): Defines custom retry strategy.
    - rollback(): Executes compensation workflow on transaction failure.
    """

    def authentication(self, headers: Dict[str, str], credentials: Optional[ConnectorCredentialModel]) -> Dict[str, str]:
        """Injects authentication tokens into HTTP headers."""
        req_headers = dict(headers)
        if credentials:
            if credentials.access_token:
                req_headers["Authorization"] = f"Bearer {credentials.access_token}"
            elif credentials.api_key:
                req_headers["X-API-Key"] = credentials.api_key
            if credentials.additional_headers:
                req_headers.update(credentials.additional_headers)
        return req_headers

    def validate(self, request: ConnectorRequestModel) -> None:
        """Validates request parameter schema prior to execution."""
        if not request.operation_id:
            raise ValueError("Connector request operation_id cannot be empty.")

    def serialize(self, body: Any) -> Any:
        """Serializes request payload into JSON-compatible format."""
        return body

    def deserialize(self, raw_data: Any) -> Dict[str, Any]:
        """Deserializes raw provider payload into structured dictionary."""
        if isinstance(raw_data, dict):
            return raw_data
        return {"result": raw_data}

    async def retry(self, request: ConnectorRequestModel, attempt: int) -> bool:
        """Determines whether execution should be retried for attempt count."""
        return attempt <= request.retry_attempts

    async def rollback(self, request: ConnectorRequestModel, failure_reason: str) -> bool:
        """Executes compensation workflow on transaction failure."""
        logger.warning(f"[{self.provider_name}] Executing rollback for operation '{request.operation_id}': {failure_reason}")
        return True
