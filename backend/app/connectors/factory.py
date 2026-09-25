import logging
from app.connectors.interfaces import BaseProviderAdapter
from app.connectors.registry import connector_registry

logger = logging.getLogger("agentflow.connectors.factory")


class ConnectorFactory:
    """Factory Pattern class for resolving and instantiating Provider Adapters."""

    @staticmethod
    def get_adapter(provider_name: str) -> BaseProviderAdapter:
        """Resolves adapter instance for target provider name."""
        return connector_registry.get(provider_name)
