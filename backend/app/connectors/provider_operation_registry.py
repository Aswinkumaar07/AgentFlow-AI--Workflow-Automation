import logging
from typing import Dict, List, Optional
from app.connectors.models import OperationSchemaModel, ConnectorMetadataModel
from app.connectors.registry import connector_registry

logger = logging.getLogger("agentflow.connectors.provider_operation_registry")


class ProviderOperationRegistry:
    """
    Sprint AI-2: Provider-Agnostic Operation Registry for AgentFlow AI.
    Exposes operations dynamically through a provider-agnostic common registry.
    Allows dynamic discovery of operations by the Planner without hardcoded provider if/else rules.
    """

    def get_provider_operations(self, provider_name: str) -> List[OperationSchemaModel]:
        """
        Returns all registered operations for a specific provider.
        Example: "What operations does Gmail support?"
        -> [gmail.messages.send, gmail.messages.read, gmail.messages.reply, ...]
        """
        meta = connector_registry.get_connector_metadata(provider_name)
        if meta and meta.operation_schemas:
            return list(meta.operation_schemas.values())
        return []

    def get_operation_metadata(self, operation_id: str) -> Optional[OperationSchemaModel]:
        """
        Returns full schema metadata for a specific operation_id across all registered providers.
        """
        for meta in connector_registry._metadata_map.values():
            if operation_id in meta.operation_schemas:
                return meta.operation_schemas[operation_id]
        return None

    def search_operations_by_intent(self, intent: str) -> List[OperationSchemaModel]:
        """
        Dynamically searches available operations across all providers for a given intent keyword or prompt query.
        """
        intent_lower = intent.lower()
        matched: List[OperationSchemaModel] = []
        for meta in connector_registry._metadata_map.values():
            for op in meta.operation_schemas.values():
                if (
                    intent_lower in op.id.lower()
                    or intent_lower in (op.display_name or "").lower()
                    or intent_lower in op.description.lower()
                ):
                    matched.append(op)
        return matched

    def list_all_providers(self) -> List[str]:
        """
        Lists all registered connector providers dynamically from the registry.
        """
        return connector_registry.list_supported_providers()

    def get_operations_map(self) -> Dict[str, List[str]]:
        """
        Returns a mapping of provider -> list of supported operation IDs.
        """
        providers = self.list_all_providers()
        ops_map: Dict[str, List[str]] = {}
        for p in providers:
            ops = self.get_provider_operations(p)
            ops_map[p] = [op.id for op in ops]
        return ops_map

    def select_best_operation(self, provider_name: str, intent_or_prompt: str) -> str:
        """
        Dynamically resolves the best operation for a provider and prompt using registry metadata,
        eliminating hardcoded if/else statements in the planner.
        """
        return connector_registry.match_operation_dynamically(provider_name, intent_or_prompt)


provider_operation_registry = ProviderOperationRegistry()
