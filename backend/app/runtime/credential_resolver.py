import logging
from typing import Any, Dict
from app.connectors.security.secret_manager import secret_manager
from app.oauth.manager import oauth_manager
from app.oauth.provider_utils import normalize_provider
from app.agents.oauth_ai.account_picker import account_picker

logger = logging.getLogger("agentflow.runtime.credential_resolver")


class CredentialResolver:
    """
    Sprint AUTH-3 — Backend-Driven Credential Resolver.
    Resolves authenticated OAuth credential details for a provider and user_id.
    Executes BEFORE workflow JSON is sent to frontend so every OAuth node is pre-bound.
    Strictly queries SecretManager and OAuthManager single source of truth.
    """

    async def resolve(self, provider: str, user_id: str = "usr_1") -> Dict[str, Any]:
        norm_prov = normalize_provider(provider)

        # 1. Query SecretManager Store First
        secret = await secret_manager.get_secret(user_id, norm_prov)
        if secret and secret.access_token:
            lbl = getattr(secret, "account_label", None)
            if not lbl or lbl.startswith("usr_1@") or lbl == f"{user_id}@{norm_prov.lower()}.com":
                conn_meta = await oauth_manager.get_connected_account(user_id, norm_prov)
                if conn_meta:
                    lbl = conn_meta.get("email")
            lbl = lbl or f"{user_id}@{norm_prov.lower()}.com"
            return {
                "credential_id": f"conn_{norm_prov.lower()}_{user_id}",
                "auth_provider": norm_prov,
                "auth_account_label": lbl,
                "auth_status": "active",
                "scopes": secret.scopes or ["gmail.readonly", "drive.file"],
                "is_authenticated": True,
            }

        # 2. Query OAuthManager Memory Store / Metadata
        conn_meta = await oauth_manager.get_connected_account(user_id, norm_prov)
        if conn_meta and conn_meta.get("email"):
            return {
                "credential_id": conn_meta.get("connection_id") or f"conn_{norm_prov.lower()}_{user_id}",
                "auth_provider": norm_prov,
                "auth_account_label": conn_meta.get("email"),
                "auth_status": "active",
                "scopes": conn_meta.get("scopes") or ["gmail.readonly", "drive.file"],
                "is_authenticated": True,
            }

        # If SecretManager and OAuthManager have no credential, node remains unbound
        return {
            "credential_id": None,
            "auth_provider": norm_prov,
            "auth_account_label": None,
            "auth_status": "unbound",
            "scopes": [],
            "is_authenticated": False,
        }

    def resolve_sync(self, provider: str, user_id: str = "usr_1") -> Dict[str, Any]:
        norm_prov = normalize_provider(provider)

        # 1. Query SecretManager Sync
        secret = secret_manager.get_secret_sync(user_id, norm_prov)
        if secret and secret.access_token:
            lbl = getattr(secret, "account_label", None)
            if not lbl:
                key = oauth_manager._make_key(user_id, norm_prov)
                meta = oauth_manager._user_metadata.get(key, {})
                lbl = meta.get("email")
            lbl = lbl or f"{user_id}@{norm_prov.lower()}.com"
            return {
                "credential_id": f"conn_{norm_prov.lower()}_{user_id}",
                "auth_provider": norm_prov,
                "auth_account_label": lbl,
                "auth_status": "active",
                "scopes": secret.scopes or ["gmail.readonly", "drive.file"],
                "is_authenticated": True,
            }

        # 2. Query OAuthManager Memory Store Sync
        active_conns = [
            c for c in oauth_manager._connections.values()
            if c.user_id == user_id and normalize_provider(c.provider) == norm_prov and c.status == "CONNECTED"
        ]
        if active_conns:
            conn = active_conns[0]
            key = oauth_manager._make_key(user_id, norm_prov)
            meta = oauth_manager._user_metadata.get(key, {})
            email = meta.get("email") or getattr(conn, "account_label", None) or getattr(conn, "email", None) or f"{user_id}@{norm_prov.lower()}.com"
            return {
                "credential_id": conn.id or f"conn_{norm_prov.lower()}_{user_id}",
                "auth_provider": norm_prov,
                "auth_account_label": email,
                "auth_status": "active",
                "scopes": conn.scopes or ["gmail.readonly", "drive.file"],
                "is_authenticated": True,
            }

        # If SecretManager and OAuthManager have no credential, node remains unbound
        return {
            "credential_id": None,
            "auth_provider": norm_prov,
            "auth_account_label": None,
            "auth_status": "unbound",
            "scopes": [],
            "is_authenticated": False,
        }


credential_resolver = CredentialResolver()
