import logging
import threading
from typing import Dict, List, Optional
from app.connectors.interfaces import BaseProviderAdapter
from app.connectors.models import ConnectorMetadataModel, OperationSchemaModel
from app.connectors.schemas_registry import ALL_CONNECTOR_METADATA, GENERIC_REST_METADATA
from app.connectors.providers.drive.adapter import DriveAdapter
from app.connectors.providers.generic_rest.adapter import GenericRESTAdapter
from app.connectors.providers.github.adapter import GitHubAdapter
from app.connectors.providers.gmail.adapter import GmailAdapter
from app.connectors.providers.notion.adapter import NotionAdapter
from app.connectors.providers.sheets.adapter import GoogleSheetsAdapter
from app.connectors.providers.slack.adapter import SlackAdapter
from app.connectors.providers.stripe.adapter import StripeAdapter

logger = logging.getLogger("agentflow.connectors.registry")


class ConnectorRegistry:
    """Thread-safe Enterprise Connector Registry providing dynamic schemas for all 16 supported providers."""

    ALIAS_MAP = {
        "gmail": "gmail",
        "google gmail": "gmail",
        "email": "gmail",
        "send email": "gmail",
        "drive": "drive",
        "google drive": "drive",
        "sheets": "sheets",
        "google sheets": "sheets",
        "slack": "slack",
        "slack web api": "slack",
        "github": "github",
        "github api v3": "github",
        "notion": "notion",
        "notion api": "notion",
        "discord": "discord",
        "stripe": "stripe",
        "stripe connect": "stripe",
        "openai": "openai",
        "ai": "ai",
        "generic": "generic_rest",
        "generic rest": "generic_rest",
        "generic rest api": "generic_rest",
        "generic_rest": "generic_rest",
        "webhook": "webhook",
        "webhook trigger": "webhook",
        "schedule": "schedule",
        "condition": "condition",
        "if": "condition",
        "loop": "loop",
        "merge": "merge",
        "approval": "approval",
    }

    def __init__(self) -> None:
        self._adapters: Dict[str, BaseProviderAdapter] = {}
        self._metadata_map: Dict[str, ConnectorMetadataModel] = ALL_CONNECTOR_METADATA
        self._lock = threading.Lock()
        self._register_default_adapters()

    def _register_default_adapters(self) -> None:
        self.register(GmailAdapter())
        self.register(DriveAdapter())
        self.register(SlackAdapter())
        self.register(GitHubAdapter())
        self.register(NotionAdapter())
        self.register(StripeAdapter())
        self.register(GoogleSheetsAdapter())
        self.register(GenericRESTAdapter())

    def register(self, adapter: BaseProviderAdapter) -> None:
        key = adapter.provider_name.lower().replace(" ", "_")
        with self._lock:
            self._adapters[key] = adapter
            logger.info(f"Registered Connector ProviderAdapter: [{adapter.provider_name}]")

    def _resolve_key(self, provider_name: str) -> str:
        raw_key = provider_name.lower().strip()
        return self.ALIAS_MAP.get(raw_key, raw_key.replace(" ", "_"))

    def has(self, provider_name: str) -> bool:
        resolved_key = self._resolve_key(provider_name)
        with self._lock:
            if resolved_key in self._adapters or resolved_key in self._metadata_map:
                return True
            for k in self._metadata_map:
                if k in resolved_key or resolved_key in k:
                    return True
            return False

    def get(self, provider_name: str) -> BaseProviderAdapter:
        resolved_key = self._resolve_key(provider_name)
        with self._lock:
            if resolved_key in self._adapters:
                return self._adapters[resolved_key]
            for adapter_key, adapter in self._adapters.items():
                if adapter_key in resolved_key or resolved_key in adapter_key:
                    return adapter
            return self._adapters.get("generic_rest", GenericRESTAdapter())

    def get_connector_metadata(self, provider_name: str) -> ConnectorMetadataModel:
        resolved_key = self._resolve_key(provider_name)
        with self._lock:
            if resolved_key in self._metadata_map:
                return self._metadata_map[resolved_key]
            for k, meta in self._metadata_map.items():
                if k in resolved_key or resolved_key in k:
                    return meta
            return GENERIC_REST_METADATA

    def get_operation_schema(self, provider_name: str, operation_id: str) -> Optional[OperationSchemaModel]:
        meta = self.get_connector_metadata(provider_name)
        if meta and operation_id in meta.operation_schemas:
            return meta.operation_schemas[operation_id]
        for m in self._metadata_map.values():
            if operation_id in m.operation_schemas:
                return m.operation_schemas[operation_id]
        return None

    def list_supported_providers(self) -> List[str]:
        """Dynamically lists all registered connector providers."""
        with self._lock:
            return list(self._metadata_map.keys())

    def discover_operations(self, provider_name: str) -> List[OperationSchemaModel]:
        """Discovers all supported operation schemas for a given provider dynamically from registry metadata."""
        meta = self.get_connector_metadata(provider_name)
        if meta and meta.operation_schemas:
            return list(meta.operation_schemas.values())
        return []

    def match_operation_dynamically(self, provider_name: str, prompt: str) -> str:
        """
        Provider-Agnostic Operation Matcher.
        Discovers operation schemas from registry metadata and matches user prompt intent
        without any hardcoded provider conditional branches.
        """
        p_lower = prompt.lower()
        operations = self.discover_operations(provider_name)

        if not operations:
            meta = self.get_connector_metadata(provider_name)
            return meta.supported_operations[0] if meta.supported_operations else "generic.http.request"

        best_op_id = operations[0].id
        best_score = -1

        for op in operations:
            score = 0
            op_id_lower = op.id.lower()
            display_lower = (op.display_name or "").lower()

            # Absolute explicit intent matches (100 points)
            if "mark_unread" in op_id_lower and ("mark as unread" in p_lower or "mark unread" in p_lower):
                score += 100
            elif "mark_read" in op_id_lower and ("mark as read" in p_lower or "mark read" in p_lower):
                score += 100
            elif "delete" in op_id_lower and any(kw in p_lower for kw in ["delete email", "trash email", "delete message", "trash message", "delete msg"]):
                score += 100
            elif "forward" in op_id_lower and any(kw in p_lower for kw in ["forward email", "forward message", "fwd email"]):
                score += 100
            elif "reply" in op_id_lower and any(kw in p_lower for kw in ["reply to email", "reply to message", "reply message", "send reply", "respond to email", "reply"]):
                score += 100
            elif "download" in op_id_lower and any(kw in p_lower for kw in ["download attachment", "save attachment"]):
                score += 100

            # High priority action verb matches (50-100 points)
            if any(verb in p_lower for verb in ["read latest", "read unread", "read email", "read emails", "fetch email", "fetch unread", "list email", "check unread", "unread emails", "unread email", "read today", "read last", "last email", "latest email"]) and ("list" in op_id_lower or "get" in op_id_lower):
                score += 100
            elif any(verb in p_lower for verb in ["search", "find", "query", "lookup"]) and "search" in op_id_lower:
                score += 80
            elif any(verb in p_lower for verb in ["send", "write email", "dispatch"]) and "send" in op_id_lower:
                score += 50
            elif any(verb in p_lower for verb in ["create", "add", "new", "make"]) and ("create" in op_id_lower or "add" in op_id_lower):
                score += 50

            # Display name token matching (1 point per token)
            for token in display_lower.split():
                if len(token) > 3 and token in p_lower:
                    score += 1

            if score > best_score:
                best_score = score
                best_op_id = op.id

        return best_op_id

    def get_all_metadata(self) -> List[Dict]:
        with self._lock:
            return [meta.model_dump() for meta in self._metadata_map.values()]


connector_registry = ConnectorRegistry()

