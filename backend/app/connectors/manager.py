import logging
from typing import Any, Dict, Optional

from app.connectors.auth.refresh_manager import token_refresh_manager
from app.connectors.execution.executor import connector_executor
from app.connectors.factory import ConnectorFactory
from app.connectors.models import (
    ConnectorCredentialModel,
    ConnectorRequestModel,
    ConnectorResponseModel,
)
from app.connectors.registry import connector_registry
from app.connectors.security.secret_manager import secret_manager

logger = logging.getLogger("agentflow.connectors.manager")


class ConnectorManager:
    """Enterprise Facade orchestrating Connector Factory, Execution Engine, Secret Manager, & Registry."""

    def __init__(self) -> None:
        self.factory = ConnectorFactory()
        self.executor = connector_executor
        self.secret_manager = secret_manager
        self.registry = connector_registry

    async def execute(
        self,
        provider: str,
        operation_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        body: Optional[Any] = None,
        tenant_id: str = "default",
        timeout_seconds: float = 30.0,
    ) -> ConnectorResponseModel:
        """Executes a connector operation for a given tenant with automatic OAuth refresh and telemetry."""
        adapter = self.factory.get_adapter(provider)
        credentials = await self.secret_manager.get_secret(tenant_id, provider)

        if credentials:
            credentials = await token_refresh_manager.get_valid_credentials(credentials)

        request = ConnectorRequestModel(
            operation_id=operation_id,
            parameters=parameters or {},
            body=body,
            tenant_id=tenant_id,
            timeout_seconds=timeout_seconds,
        )

        return await self.executor.execute(adapter, request, credentials)

    async def store_credentials(self, tenant_id: str, provider: str, credentials: ConnectorCredentialModel) -> bool:
        """Stores encrypted credentials for a tenant."""
        return await self.secret_manager.set_secret(tenant_id, provider, credentials)


connector_manager = ConnectorManager()
