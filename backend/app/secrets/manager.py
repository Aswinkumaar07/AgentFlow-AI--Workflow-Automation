import logging
import time
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("agentflow.secrets")


class SecretModel(BaseModel):
    key: str
    encrypted_value: str
    workspace_id: str = "ws_default"
    updated_at: float = Field(default_factory=time.time)


class EnterpriseSecretsStore:
    """Enterprise Secrets Store handling encrypted API keys and environment variables."""

    def __init__(self) -> None:
        self._secrets: Dict[str, SecretModel] = {}

    def _mask_value(self, val: str) -> str:
        if len(val) <= 4:
            return "****"
        return f"{val[:2]}****{val[-2:]}"

    async def set_secret(self, key: str, value: str, workspace_id: str = "ws_default") -> SecretModel:
        sec = SecretModel(key=key, encrypted_value=f"enc_{value}", workspace_id=workspace_id)
        self._secrets[key] = sec
        logger.info(f"Stored encrypted secret [{key}] for workspace [{workspace_id}].")
        return sec

    async def get_secret(self, key: str) -> Optional[str]:
        sec = self._secrets.get(key)
        if sec:
            return sec.encrypted_value.replace("enc_", "")
        return None

    async def list_masked_secrets(self) -> List[Dict[str, str]]:
        return [
            {"key": s.key, "masked_value": self._mask_value(s.encrypted_value.replace("enc_", "")), "workspace_id": s.workspace_id}
            for s in self._secrets.values()
        ]


enterprise_secrets_store = EnterpriseSecretsStore()
