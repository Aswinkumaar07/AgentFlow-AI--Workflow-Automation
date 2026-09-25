import logging
import time
from typing import Any, Dict, List, Optional
from app.agents.oauth_ai.oauth_manager import zero_touch_oauth_manager
from app.agents.oauth_ai.account_picker import account_picker, ConnectedAccount
from app.agents.oauth_ai.health_monitor import connection_health_monitor

logger = logging.getLogger("agentflow.agents.oauth_ai.service")


class OAuthAIService:
    """Service for Zero-Touch OAuth node population, multi-account management, and health monitoring."""

    # ── Node Population ────────────────────────────────────────

    def populate_node_auth(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Automatically checks and populates a single node with OAuth credentials."""
        return zero_touch_oauth_manager.ensure_node_authenticated(node)

    def populate_workflow(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Bulk-populates OAuth credentials for all steps in a workflow DAG.
        Returns enriched steps plus a summary of bindings made and any missing accounts.
        """
        bound = []
        needs_auth = []
        enriched_steps = []

        for step in steps:
            result = zero_touch_oauth_manager.ensure_node_authenticated(step)
            enriched_steps.append(result["node"])

            if result["is_authenticated"]:
                bound.append({
                    "step_id": step.get("step_id") or step.get("id"),
                    "provider": step.get("provider"),
                    "account": result.get("account_label"),
                })
            else:
                needs_auth.append({
                    "step_id": step.get("step_id") or step.get("id"),
                    "provider": step.get("provider"),
                    "oauth_connect_url": result.get("oauth_connect_url"),
                })

        return {
            "steps": enriched_steps,
            "bound_count": len(bound),
            "needs_auth_count": len(needs_auth),
            "bound": bound,
            "needs_auth": needs_auth,
            "fully_authenticated": len(needs_auth) == 0,
        }

    # ── Health Monitoring ──────────────────────────────────────

    def get_all_connections_health(self) -> List[Dict[str, Any]]:
        """Returns connection health across all OAuth providers."""
        return connection_health_monitor.check_all_health()

    def get_provider_health(self, provider: str) -> Dict[str, Any]:
        """Returns health for a single provider."""
        return connection_health_monitor.check_connection_health(provider)

    def force_refresh(self, provider: str) -> Dict[str, Any]:
        """Forces token refresh for the default account of a provider."""
        return connection_health_monitor.force_refresh(provider)

    # ── Account Management ─────────────────────────────────────

    def list_accounts(self, provider: str) -> List[Dict[str, Any]]:
        """Lists all connected accounts for a provider."""
        accounts = account_picker.list_accounts(provider)
        return [
            {
                **a.model_dump(exclude={"access_token", "refresh_token"}),
                "is_expired": a.is_expired(),
                "expires_in_seconds": a.expires_in_seconds(),
            }
            for a in accounts
        ]

    def connect_account(self, provider: str, email_or_name: str) -> ConnectedAccount:
        """Connects or updates an OAuth account as the default."""
        import hashlib
        account_id = f"acc_{provider.lower().replace(' ', '_')}_{hashlib.md5(email_or_name.encode()).hexdigest()[:8]}"
        acc = ConnectedAccount(
            account_id=account_id,
            provider=provider,
            email_or_name=email_or_name,
            status="active",
            is_default=True,
            expires_at=int(time.time()) + 3600,
        )
        # Mark all existing as non-default first
        for existing in account_picker.list_accounts(provider):
            existing.is_default = False
        return account_picker.add_or_update_account(acc)

    def set_default_account(self, provider: str, account_id: str) -> bool:
        """Sets a specific account as the default for the provider."""
        success = account_picker.set_default(provider, account_id)
        if success:
            logger.info(f"Default account for '{provider}' set to '{account_id}'.")
        return success

    def disconnect_account(self, provider: str, account_id: str) -> bool:
        """Removes a specific account. If it was default, the next account is promoted."""
        return account_picker.disconnect_account(provider, account_id)


oauth_ai_service = OAuthAIService()
