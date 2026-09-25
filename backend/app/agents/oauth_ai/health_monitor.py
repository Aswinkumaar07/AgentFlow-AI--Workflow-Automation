import time
import logging
from typing import Any, Dict, List, Optional
from app.agents.oauth_ai.account_picker import account_picker, ConnectedAccount

logger = logging.getLogger("agentflow.agents.oauth_ai.health_monitor")

HEALTH_STATUS_OK = "healthy"
HEALTH_STATUS_EXPIRING = "expiring_soon"   # < 10 minutes remaining
HEALTH_STATUS_EXPIRED = "expired"
HEALTH_STATUS_MISSING = "missing"


class ConnectionHealthMonitor:
    """Proactively checks OAuth token expiration, executing auto-refreshes and recovery."""

    EXPIRY_WARNING_SECONDS = 600  # Warn when < 10 minutes remain

    def check_connection_health(self, provider: str) -> Dict[str, Any]:
        """Returns full health snapshot for a single provider's default account."""
        acc = account_picker.get_default_account(provider)
        if not acc:
            return {
                "provider": provider,
                "is_connected": False,
                "status": HEALTH_STATUS_MISSING,
                "is_expired": False,
                "expires_in_seconds": 0,
                "account_id": None,
                "email_or_name": None,
                "message": f"No OAuth account connected for '{provider}'.",
            }

        expires_in = acc.expires_in_seconds()
        is_expired = acc.is_expired()

        # Auto-refresh if expired
        if is_expired:
            logger.warning(f"Token for '{acc.email_or_name}' ({provider}) is expired. Auto-refreshing...")
            acc = self.auto_refresh_token(acc)
            expires_in = acc.expires_in_seconds()
            is_expired = acc.is_expired()

        # Determine health status
        if is_expired:
            health_status = HEALTH_STATUS_EXPIRED
        elif expires_in < self.EXPIRY_WARNING_SECONDS:
            health_status = HEALTH_STATUS_EXPIRING
        else:
            health_status = HEALTH_STATUS_OK

        return {
            "provider": provider,
            "is_connected": True,
            "status": health_status,
            "is_expired": is_expired,
            "expires_in_seconds": expires_in,
            "expires_at": acc.expires_at,
            "account_id": acc.account_id,
            "email_or_name": acc.email_or_name,
            "scopes": acc.scopes,
            "is_default": acc.is_default,
            "message": (
                f"Account '{acc.email_or_name}' is healthy."
                if health_status == HEALTH_STATUS_OK
                else f"Account '{acc.email_or_name}' token expiring in {expires_in}s."
                if health_status == HEALTH_STATUS_EXPIRING
                else f"Account '{acc.email_or_name}' token has expired."
            ),
        }

    def check_all_health(self) -> List[Dict[str, Any]]:
        """Returns connection health for every known provider."""
        all_providers = account_picker.list_all_providers()
        return [self.check_connection_health(p) for p in all_providers]

    def force_refresh(self, provider: str) -> Dict[str, Any]:
        """Forces token refresh for the default account of a provider, regardless of expiry."""
        acc = account_picker.get_default_account(provider)
        if not acc:
            return {
                "provider": provider,
                "success": False,
                "message": f"No account found for provider '{provider}'.",
            }

        refreshed = account_picker.refresh_account_token(provider, acc.account_id)
        if not refreshed:
            return {
                "provider": provider,
                "success": False,
                "message": "Token refresh failed.",
            }

        logger.info(f"Force-refreshed token for '{refreshed.email_or_name}' ({provider}).")
        return {
            "provider": provider,
            "success": True,
            "account_id": refreshed.account_id,
            "email_or_name": refreshed.email_or_name,
            "expires_at": refreshed.expires_at,
            "expires_in_seconds": refreshed.expires_in_seconds(),
            "message": f"Token refreshed successfully for '{refreshed.email_or_name}'.",
        }

    def auto_refresh_token(self, account: ConnectedAccount) -> ConnectedAccount:
        """Background auto-refresh invoked when an expired token is detected on health check."""
        refreshed = account_picker.refresh_account_token(account.provider, account.account_id)
        if refreshed:
            logger.info(f"Auto-refreshed OAuth token for '{refreshed.email_or_name}' ({refreshed.provider}).")
            return refreshed
        return account


connection_health_monitor = ConnectionHealthMonitor()
