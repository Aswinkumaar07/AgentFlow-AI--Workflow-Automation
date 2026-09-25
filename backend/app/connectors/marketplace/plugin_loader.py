import logging
from typing import Any, Dict
from app.connectors.generator.connector_builder import connector_builder
from app.connectors.registry import connector_registry

logger = logging.getLogger("agentflow.connectors.marketplace")


class ConnectorPluginLoader:
    """Enterprise Marketplace Plugin Loader supporting dynamic connector installation from manifests."""

    def install_from_manifest(self, manifest_dict: Dict[str, Any]) -> bool:
        """Parses connector manifest and registers new provider adapter dynamically."""
        try:
            spec = manifest_dict.get("spec", {})
            adapter = connector_builder.build_from_openapi(spec)
            connector_registry.register(adapter)
            logger.info(f"Marketplace successfully installed connector plugin: [{adapter.provider_name}]")
            return True
        except Exception as e:
            logger.error(f"Failed to install connector plugin from manifest: {e}")
            return False


plugin_loader = ConnectorPluginLoader()
