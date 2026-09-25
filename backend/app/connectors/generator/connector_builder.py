import logging
from typing import Any, Dict, List, Optional
from app.connectors.base_connector import BaseConnector
from app.connectors.cache.connection_pool import connection_pool
from app.connectors.models import (
    ConnectorCredentialModel,
    ConnectorMetadataModel,
    ConnectorRequestModel,
    ConnectorResponseModel,
)

logger = logging.getLogger("agentflow.connectors.generator")


class GeneratedConnectorAdapter(BaseConnector):
    """Dynamically generated Provider Adapter created from OpenAPI/Swagger spec."""

    def __init__(self, provider_name: str, version: str = "v1", operations: Optional[List[str]] = None):
        self._provider_name = provider_name
        self.version = version
        self.operations = operations or []

    @property
    def provider_name(self) -> str:
        return self._provider_name

    def get_metadata(self) -> ConnectorMetadataModel:
        return ConnectorMetadataModel(
            provider=self.provider_name,
            version=self.version,
            supported_operations=self.operations,
            auth_types=["OAuth2", "Bearer", "API_Key"],
        )

    async def execute_operation(
        self, request: ConnectorRequestModel, credentials: Optional[ConnectorCredentialModel] = None
    ) -> ConnectorResponseModel:
        headers = self.authentication({}, credentials)
        url = request.parameters.get("url", f"https://api.{self.provider_name.lower().replace(' ', '')}.com/v1/{request.operation_id}")

        res = await connection_pool.request("POST", url, headers=headers, json_data=request.body or request.parameters)
        return ConnectorResponseModel(
            success=True,
            operation_id=request.operation_id,
            status_code=200,
            data=self.deserialize(res),
        )


class ConnectorBuilder:
    """Automated Connector Generator building production adapters from OpenAPI specs."""

    @staticmethod
    def build_from_openapi(spec_dict: Dict[str, Any]) -> GeneratedConnectorAdapter:
        info = spec_dict.get("info", {})
        provider_name = info.get("title", "Generated Provider")
        version = info.get("version", "v1")
        paths = spec_dict.get("paths", {})

        operations = []
        for path, item in paths.items():
            if isinstance(item, dict):
                for method, op in item.items():
                    if isinstance(op, dict):
                        op_id = op.get("operationId", f"{method}_{path.replace('/', '_')}")
                        operations.append(op_id)

        adapter = GeneratedConnectorAdapter(provider_name=provider_name, version=version, operations=operations)
        logger.info(f"ConnectorBuilder automatically built adapter for [{provider_name}] with {len(operations)} operations.")
        return adapter


connector_builder = ConnectorBuilder()
