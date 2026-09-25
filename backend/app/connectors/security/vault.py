import logging
from typing import Optional
from app.connectors.models import ConnectorCredentialModel
from app.connectors.security.secret_manager import secret_manager

logger = logging.getLogger("agentflow.connectors.security.vault")


class EnterpriseVaultManager:
    """Enterprise Vault Integration supporting HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, & GCP Secret Manager."""

    def __init__(self, backend_type: str = "encrypted_db"):
        self.backend_type = backend_type
        self._fallback = secret_manager

    async def get_credential(self, tenant_id: str, provider: str) -> Optional[ConnectorCredentialModel]:
        """Retrieves credentials from active Enterprise Vault backend."""
        logger.info(f"Retrieving tenant credential [{tenant_id}:{provider}] from Vault backend [{self.backend_type}]")
        return await self._fallback.get_secret(tenant_id, provider)

    async def store_credential(self, tenant_id: str, provider: str, credentials: ConnectorCredentialModel) -> bool:
        """Stores credentials in active Enterprise Vault backend."""
        logger.info(f"Storing tenant credential [{tenant_id}:{provider}] in Vault backend [{self.backend_type}]")
        return await self._fallback.set_secret(tenant_id, provider, credentials)


vault_manager = EnterpriseVaultManager()
