import json
import logging
import os
import threading
from typing import Any, Dict, Optional
from app.connectors.interfaces import BaseSecretManager
from app.connectors.models import ConnectorCredentialModel
from app.connectors.security.encryption import credential_encryption

logger = logging.getLogger("agentflow.connectors.security.secret_manager")

# Default vault path fallback resolving root or backend storage
DEFAULT_VAULT_PATH = (
    os.path.join("storage", "credentials", "vault.json")
    if os.path.exists("storage") or not os.path.exists("backend")
    else os.path.join("backend", "storage", "credentials", "vault.json")
)


class EnterpriseSecretManager(BaseSecretManager):
    """Enterprise Multi-Tenant Secret Manager providing AES-256 encrypted credential storage with vault file persistence."""

    def __init__(self, vault_path: Optional[str] = None) -> None:
        self._store: Dict[str, str] = {}  # tenant_id:provider -> encrypted_blob
        self._lock = threading.Lock()
        self.vault_path = vault_path or DEFAULT_VAULT_PATH
        self._load_vault()

    def _make_key(self, tenant_id: Any, provider: str) -> str:
        return f"{str(tenant_id).lower()}:{provider.lower()}"

    def _load_vault(self) -> None:
        """Loads persisted encrypted blobs from vault.json if present."""
        if not self.vault_path:
            return
        try:
            if os.path.exists(self.vault_path):
                with open(self.vault_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        with self._lock:
                            self._store = {str(k): str(v) for k, v in data.items()}
                        logger.info(f"Loaded {len(self._store)} encrypted secrets from vault [{self.vault_path}]")
        except Exception as e:
            logger.error(f"Failed to load credential vault from [{self.vault_path}]: {e}")
            # Do not crash application startup on corrupt or missing vault

    def _save_vault(self) -> None:
        """Persists current encrypted store to vault.json using atomic temp file replacement."""
        if not self.vault_path:
            return
        try:
            vault_dir = os.path.dirname(self.vault_path)
            if vault_dir:
                os.makedirs(vault_dir, exist_ok=True)

            tmp_path = f"{self.vault_path}.tmp"
            with self._lock:
                store_snapshot = dict(self._store)

            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(store_snapshot, f, indent=2)

            os.replace(tmp_path, self.vault_path)
            logger.debug(f"Persisted encrypted store ({len(store_snapshot)} secrets) to vault [{self.vault_path}]")
        except Exception as e:
            logger.error(f"Failed to persist credential vault to [{self.vault_path}]: {e}")

    async def get_secret(self, tenant_id: Any, provider: str) -> Optional[ConnectorCredentialModel]:
        return self.get_secret_sync(tenant_id, provider)

    def get_secret_sync(self, tenant_id: Any, provider: str) -> Optional[ConnectorCredentialModel]:
        key = self._make_key(tenant_id, provider)
        with self._lock:
            encrypted_blob = self._store.get(key)

        if not encrypted_blob:
            return None

        try:
            data = credential_encryption.decrypt(encrypted_blob)
            return ConnectorCredentialModel(**data)
        except Exception as e:
            logger.error(f"Failed to decrypt credentials for tenant [{tenant_id}] provider [{provider}]: {e}")
            return None

    async def set_secret(self, tenant_id: Any, provider: str, credentials: ConnectorCredentialModel) -> bool:
        key = self._make_key(tenant_id, provider)
        try:
            encrypted_blob = credential_encryption.encrypt(credentials.model_dump())
            with self._lock:
                self._store[key] = encrypted_blob
            self._save_vault()
            logger.info(f"Encrypted and stored credentials for tenant [{tenant_id}] provider [{provider}]")
            return True
        except Exception as e:
            logger.error(f"Failed to encrypt credentials for tenant [{tenant_id}] provider [{provider}]: {e}")
            return False

    async def delete_secret(self, tenant_id: Any, provider: str) -> bool:
        key = self._make_key(tenant_id, provider)
        deleted = False
        with self._lock:
            if key in self._store:
                del self._store[key]
                deleted = True
        if deleted:
            self._save_vault()
            logger.info(f"Deleted encrypted credentials for tenant [{tenant_id}] provider [{provider}]")
            return True
        return False

    async def list_all_secrets(self, tenant_id: Any) -> Dict[str, ConnectorCredentialModel]:
        """Returns map of provider -> decrypted ConnectorCredentialModel for tenant."""
        tid = str(tenant_id).lower()
        result: Dict[str, ConnectorCredentialModel] = {}
        with self._lock:
            keys = [k for k in self._store if k.startswith(f"{tid}:")]
        for k in keys:
            prov = k.split(":", 1)[1]
            secret = await self.get_secret(tenant_id, prov)
            if secret:
                result[prov] = secret
        return result


secret_manager = EnterpriseSecretManager()

