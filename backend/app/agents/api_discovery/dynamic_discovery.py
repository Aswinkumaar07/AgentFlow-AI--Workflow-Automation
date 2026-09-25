import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.agents.api_discovery.parser.spec_parser import EnterpriseSpecParser
from app.agents.api_discovery.models import EndpointMetadataModel
from app.agents.connector_ai.connector_selector import connector_selector, ConnectorCandidate
from app.agents.connector_ai.operation_ranker import operation_ranker, OperationResult

logger = logging.getLogger("agentflow.api_discovery.dynamic")


class DynamicConnectorSpec(BaseModel):
    provider: str
    category: str = "Discovered API"
    capabilities: List[str] = Field(default_factory=list)
    authentication: str = "APIKey"
    operations: List[Dict[str, Any]] = Field(default_factory=list)


class DynamicDiscoveryResult(BaseModel):
    success: bool
    provider: str
    endpoints_indexed: int
    connector_spec: DynamicConnectorSpec
    message: str


class DynamicAPIDiscoveryEngine:
    """
    AgentFlow AI - Dynamic API Discovery Engine
    Automatically parses OpenAPI 3, Swagger 2, Postman Collections, and GraphQL schemas,
    extracts parameters & authentication, generates connector specs, registers connectors dynamically,
    and updates vector stores without manual coding.
    """

    def __init__(self) -> None:
        self.parser = EnterpriseSpecParser()

    def discover_and_register_api(
        self, spec_content: Any, format_hint: Optional[str] = None
    ) -> DynamicDiscoveryResult:
        """Parses API spec, registers connector dynamically into Connector AI registry & vector store."""
        try:
            endpoints: List[EndpointMetadataModel] = self.parser.parse_spec(spec_content, format_hint)
        except Exception as e:
            logger.error(f"Failed to parse API spec: {e}")
            return DynamicDiscoveryResult(
                success=False,
                provider="Unknown",
                endpoints_indexed=0,
                connector_spec=DynamicConnectorSpec(provider="Unknown"),
                message=f"Spec parse error: {str(e)}",
            )

        if not endpoints:
            return DynamicDiscoveryResult(
                success=False,
                provider="Unknown",
                endpoints_indexed=0,
                connector_spec=DynamicConnectorSpec(provider="Unknown"),
                message="No valid endpoints extracted from specification.",
            )

        provider_name = endpoints[0].provider or "Discovered API"
        capabilities: List[str] = []
        operations: List[Dict[str, Any]] = []

        for ep in endpoints:
            cap_desc = ep.summary or f"{ep.http_method} {ep.endpoint}"
            capabilities.append(cap_desc)

            # Build operation payload
            op_dict = {
                "provider": provider_name,
                "operation": ep.operation_id,
                "summary": ep.summary or f"{ep.http_method} {ep.endpoint}",
                "parameters": {p: f"{{{{{p}}}}}" for p in ep.required_params},
                "authentication": "APIKey",
                "keywords": [provider_name.lower(), ep.operation_id.lower(), ep.http_method.lower()]
                + ep.summary.lower().split(),
            }
            operations.append(op_dict)

            # Register operation dynamically into OperationRanker CATALOG
            existing_ops = [op["operation"] for op in operation_ranker.OPERATION_CATALOG]
            if ep.operation_id not in existing_ops:
                operation_ranker.OPERATION_CATALOG.append(op_dict)

        # Register provider dynamically into ConnectorSelector CATALOG
        existing_providers = [c["provider"] for c in connector_selector.CONNECTOR_CATALOG]
        if provider_name not in existing_providers:
            connector_selector.CONNECTOR_CATALOG.append(
                {
                    "provider": provider_name,
                    "category": "Discovered API",
                    "capabilities": capabilities,
                    "authentication": "APIKey",
                    "keywords": [provider_name.lower(), "discovered", "api", "rest"],
                }
            )

        connector_spec = DynamicConnectorSpec(
            provider=provider_name,
            category="Discovered API",
            capabilities=capabilities,
            authentication="APIKey",
            operations=operations,
        )

        logger.info(f"Dynamically registered connector '{provider_name}' with {len(endpoints)} endpoints into AI Connector Registry.")

        return DynamicDiscoveryResult(
            success=True,
            provider=provider_name,
            endpoints_indexed=len(endpoints),
            connector_spec=connector_spec,
            message=f"Successfully registered connector '{provider_name}' into live AI registry.",
        )


dynamic_api_discovery_engine = DynamicAPIDiscoveryEngine()
