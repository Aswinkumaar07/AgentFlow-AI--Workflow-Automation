import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.agents.api_discovery import dynamic_api_discovery_engine, DynamicDiscoveryResult
from app.agents.connector_ai import connector_selector, operation_ranker

logger = logging.getLogger("agentflow.agents.connector_studio")


class GeneratedConnectorSpec(BaseModel):
    provider: str
    category: str = "Custom API"
    icon: str = "Zap"
    description: str = ""
    authentication: str = "APIKey"
    capabilities: List[str] = Field(default_factory=list)
    operations: List[Dict[str, Any]] = Field(default_factory=list)
    generated_test_code: str = ""
    is_registered: bool = True


class ZeroCodeConnectorGenerator:
    """
    AgentFlow AI v2.0 - Zero-Code Dynamic Connector Studio Engine
    Parses OpenAPI 3.x, Swagger 2.0, GraphQL, Postman Collections, and gRPC metadata.
    Generates connector metadata, authentication, operations, parameters, icons, descriptions,
    registers the connector dynamically into live Connector AI, and enables instant use in Planner V3.
    """

    PROVIDER_ICONS = {
        "Stripe": "CreditCard",
        "Twilio": "MessageSquare",
        "Hubspot": "Users",
        "Sendgrid": "Mail",
        "Jira": "CheckSquare",
        "Notion": "BookOpen",
        "Shopify": "ShoppingBag",
        "GraphQL": "Database",
        "Postman": "Send",
        "Generic": "Zap",
    }

    def generate_and_register_connector(
        self, spec_content: Any, format_hint: Optional[str] = None
    ) -> GeneratedConnectorSpec:
        # Run Dynamic API Discovery Engine to parse spec & extract endpoints
        res: DynamicDiscoveryResult = dynamic_api_discovery_engine.discover_and_register_api(
            spec_content, format_hint
        )

        provider_name = res.provider or "Custom API"
        icon = "Zap"
        for k, v in self.PROVIDER_ICONS.items():
            if k.lower() in provider_name.lower():
                icon = v
                break

        desc = f"Production connector for {provider_name} with {res.endpoints_indexed} operation(s)."

        # Build generated test code string
        test_code = f"""
import pytest
from app.agents.connector_ai import connector_selector

def test_generated_{provider_name.lower().replace(' ', '_')}_connector():
    candidates = connector_selector.select_connectors("{provider_name}")
    providers = [c.provider for c in candidates]
    assert "{provider_name}" in providers
"""

        connector_spec = GeneratedConnectorSpec(
            provider=provider_name,
            category="Discovered API",
            icon=icon,
            description=desc,
            authentication=res.connector_spec.authentication,
            capabilities=res.connector_spec.capabilities,
            operations=res.connector_spec.operations,
            generated_test_code=test_code.strip(),
            is_registered=True,
        )

        logger.info(f"Zero-Code Connector Studio generated and registered connector '{provider_name}' with icon '{icon}'.")
        return connector_spec


connector_generator = ZeroCodeConnectorGenerator()
