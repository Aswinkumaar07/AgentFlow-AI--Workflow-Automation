import logging
from typing import Any, Dict, Optional
from app.agents.oauth_ai.account_picker import account_picker, ConnectedAccount, OAUTH_PROVIDERS
from app.agents.oauth_ai.health_monitor import connection_health_monitor
from app.oauth.provider_utils import normalize_provider

logger = logging.getLogger("agentflow.agents.oauth_ai.oauth_manager")


class ZeroTouchOAuthManager:
    """
    AgentFlow AI - Zero-Touch Invisible OAuth Engine.
    Automatically checks connection health, populates nodes with active account credentials,
    handles single/default account auto-binding, multi-account awareness, and signals when re-authentication is required.
    All Google sub-services (Gmail, Drive, Sheets, etc.) auto-bind to the single 'Google' credential.
    """

    def ensure_node_authenticated(self, node: Dict[str, Any]) -> Dict[str, Any]:
        raw_provider = node.get("provider", "Generic")
        norm_provider = normalize_provider(raw_provider)

        if norm_provider not in OAUTH_PROVIDERS and raw_provider not in OAUTH_PROVIDERS:
            return {
                "node": node,
                "is_authenticated": True,
                "auto_bound": False,
                "multiple_accounts": False,
                "requires_oauth_popup": False,
                "message": f"Provider '{raw_provider}' does not require OAuth authentication.",
            }

        health = connection_health_monitor.check_connection_health(norm_provider)
        accs = account_picker.list_accounts(norm_provider)

        # 0 Accounts connected or disconnected -> Requires OAuth popup
        if not health["is_connected"] or not accs:
            logger.warning(f"OAuth missing for node '{node.get('id') or node.get('step_id')}' ({raw_provider}).")
            return {
                "node": node,
                "is_authenticated": False,
                "auto_bound": False,
                "multiple_accounts": False,
                "requires_oauth_popup": True,
                "oauth_connect_url": f"/api/v1/oauth/{norm_provider.lower().replace(' ', '_')}/login",
                "message": f"No connected account found for '{norm_provider}'. OAuth login required.",
            }

        # Token expired and auto-refresh failed
        if health["is_expired"]:
            logger.error(f"OAuth token expired for '{norm_provider}' after refresh attempt.")
            return {
                "node": node,
                "is_authenticated": False,
                "auto_bound": False,
                "multiple_accounts": False,
                "requires_oauth_popup": True,
                "oauth_connect_url": f"/api/v1/oauth/{norm_provider.lower().replace(' ', '_')}/login",
                "message": f"OAuth token expired for '{norm_provider}'. Re-authentication required.",
            }

        # Single account or default account available -> Auto-populate node parameters
        params = node.get("parameters", {})
        default_acc = account_picker.get_default_account(norm_provider)

        account_id = params.get("auth_account_id") or (default_acc.account_id if default_acc else health["account_id"])
        account_label = params.get("auth_account_label") or (default_acc.email_or_name if default_acc else health["email_or_name"])

        params["auth_account_id"] = account_id
        params["auth_account_label"] = account_label
        params["auth_provider"] = norm_provider
        params["auth_status"] = "active"
        params["auth_expires_in"] = health["expires_in_seconds"]
        params["auth_scopes"] = health.get("scopes", [])
        node["parameters"] = params

        logger.info(
            f"Zero-Touch OAuth bound '{account_label}' ({norm_provider}) → node "
            f"'{node.get('id') or node.get('step_id')}' ({raw_provider})."
        )

        return {
            "node": node,
            "is_authenticated": True,
            "auto_bound": True,
            "multiple_accounts": len(accs) > 1,
            "accounts": [a.model_dump(exclude={"access_token", "refresh_token"}) for a in accs] if len(accs) > 1 else [],
            "requires_oauth_popup": False,
            "account_label": account_label,
            "account_id": account_id,
            "expires_in_seconds": health["expires_in_seconds"],
            "message": f"Successfully auto-bound account '{account_label}'.",
        }


zero_touch_oauth_manager = ZeroTouchOAuthManager()
