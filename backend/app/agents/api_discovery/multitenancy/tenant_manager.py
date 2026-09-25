import logging
from typing import Dict, List, Optional
from app.agents.api_discovery.models import EndpointMetadataModel

logger = logging.getLogger("agentflow.api_discovery.multitenancy")


class TenantManager:
    """Enterprise Multi-Tenant SaaS Isolation Manager.

    Ensures complete tenant data isolation across private catalogs, vector indexes, caches, and custom APIs.
    """

    def __init__(self) -> None:
        self._tenant_catalogs: Dict[str, List[EndpointMetadataModel]] = {}

    def register_tenant_endpoint(self, tenant_id: str, endpoint: EndpointMetadataModel) -> None:
        if tenant_id not in self._tenant_catalogs:
            self._tenant_catalogs[tenant_id] = []
        self._tenant_catalogs[tenant_id].append(endpoint)
        logger.info(f"Registered custom tenant endpoint [{endpoint.operation_id}] for tenant: [{tenant_id}]")

    def get_tenant_endpoints(self, tenant_id: str) -> List[EndpointMetadataModel]:
        return list(self._tenant_catalogs.get(tenant_id, []))


tenant_manager = TenantManager()
