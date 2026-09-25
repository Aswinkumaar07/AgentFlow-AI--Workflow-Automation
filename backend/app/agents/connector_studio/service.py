import logging
from typing import Any, Dict, Optional
from app.agents.connector_studio.connector_generator import connector_generator, GeneratedConnectorSpec

logger = logging.getLogger("agentflow.agents.connector_studio.service")


class ConnectorStudioAIService:
    """Service serving Zero-Code Dynamic Connector Studio."""

    def generate_connector(
        self, spec_content: Any, format_hint: Optional[str] = None
    ) -> GeneratedConnectorSpec:
        """Parses API spec, generates production connector, and registers it live."""
        return connector_generator.generate_and_register_connector(spec_content, format_hint)


connector_studio_ai_service = ConnectorStudioAIService()
