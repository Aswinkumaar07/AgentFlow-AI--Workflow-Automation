import logging
import asyncio
from typing import Dict
from app.connectors.auth.oauth2 import oauth2_engine
from app.connectors.models import ConnectorCredentialModel

logger = logging.getLogger("agentflow.connectors.auth.refresh_manager")


class TokenRefreshManager:
    """Background Token Refresh & Reconnect Manager preventing authentication downtime."""

    def __init__(self) -> None:
        self._locks: Dict[str, asyncio.Lock] = {}

    async def get_valid_credentials(self, credentials: ConnectorCredentialModel) -> ConnectorCredentialModel:
        """Guarantees valid non-expired credentials, refreshing in a thread-safe / async-safe manner."""
        if not credentials.is_token_expired():
            return credentials

        lock_key = f"{credentials.tenant_id}:{credentials.provider}"
        if lock_key not in self._locks:
            self._locks[lock_key] = asyncio.Lock()

        async with self._locks[lock_key]:
            return await oauth2_engine.refresh_token_if_needed(credentials)


token_refresh_manager = TokenRefreshManager()
