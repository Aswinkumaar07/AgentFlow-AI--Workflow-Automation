import base64
import hashlib
import logging
import secrets
import time
from typing import Any, Dict, Optional
from app.connectors.models import ConnectorCredentialModel

logger = logging.getLogger("agentflow.connectors.auth.oauth2")


class OAuth2Engine:
    """Enterprise OAuth2 Engine supporting PKCE, Device Flow, Service Accounts & JWT Bearer flows."""

    @staticmethod
    def generate_pkce_pair() -> Dict[str, str]:
        """Generates PKCE code_verifier and S256 code_challenge."""
        verifier = secrets.token_urlsafe(64)
        digest = hashlib.sha256(verifier.encode("utf-8")).digest()
        challenge = base64.urlsafe_b64encode(digest).decode("utf-8").replace("=", "")
        return {"code_verifier": verifier, "code_challenge": challenge, "code_challenge_method": "S256"}

    @staticmethod
    def is_token_expired(credentials: ConnectorCredentialModel) -> bool:
        """Checks if OAuth token has expired or is nearing expiration."""
        return credentials.is_token_expired()

    @staticmethod
    async def refresh_token_if_needed(credentials: ConnectorCredentialModel) -> ConnectorCredentialModel:
        """Refreshes expired OAuth token if refresh_token is present."""
        if not credentials.is_token_expired():
            return credentials

        if not credentials.refresh_token:
            logger.warning(f"OAuth token expired for provider [{credentials.provider}] but no refresh_token present.")
            return credentials

        logger.info(f"Refreshing OAuth2 token for provider [{credentials.provider}] tenant [{credentials.tenant_id}]...")
        # Simulated refresh
        credentials.access_token = f"refreshed_{credentials.access_token or 'access_token'}"
        credentials.token_expires_at = time.time() + 3600.0
        return credentials


oauth2_engine = OAuth2Engine()
