import logging
from typing import Any, Dict, List, Set
from app.oauth.manager import oauth_manager
from app.connectors.security.secret_manager import secret_manager
from app.oauth.provider_utils import normalize_provider

logger = logging.getLogger("agentflow.services.connection_readiness")

INTERNAL_PROVIDERS: Set[str] = {
    "ai",
    "schedule",
    "condition",
    "loop",
    "merge",
    "approval",
    "human_approval",
    "human approval",
    "webhook",
    "code",
    "trigger",
    "internal",
    "agentflow",
    "generic",
}

GOOGLE_VARIANTS: Set[str] = {
    "google",
    "gmail",
    "google_gmail",
    "google_drive",
    "drive",
    "google_sheets",
    "sheets",
}


def is_internal_provider(provider: str) -> bool:
    if not provider:
        return True
    norm = provider.lower().strip()
    return norm in INTERNAL_PROVIDERS or norm.startswith("internal") or norm.startswith("ai_")


def is_google_service(provider: str) -> bool:
    if not provider:
        return False
    norm = provider.lower().strip()
    return norm in GOOGLE_VARIANTS or "google" in norm or "gmail" in norm or "drive" in norm or "sheets" in norm


async def check_workflow_readiness(required_providers: List[str], user_id: str = "usr_1") -> Dict[str, Any]:
    """
    Central connection readiness checker.
    Queries active user connections in OAuthManager and SecretManager.
    Distinguishes INTERNAL_PROVIDER, READY, and MISSING_CONNECTION states.
    """
    connected_providers: Set[str] = set()

    try:
        active_conns = await oauth_manager.get_user_connections(user_id)
        for c in active_conns:
            if c.status == "CONNECTED":
                connected_providers.add(c.provider.lower())
    except Exception as exc:
        logger.warning(f"Error querying oauth_manager connections: {exc}")

    try:
        stored_secrets = await secret_manager.list_all_secrets(user_id)
        for s in stored_secrets:
            if getattr(s, "access_token", None):
                prov = getattr(s, "provider", str(s)).lower()
                connected_providers.add(prov)
    except Exception as exc:
        logger.warning(f"Error querying secret_manager secrets: {exc}")

    try:
        from app.runtime.credential_resolver import credential_resolver
        for raw_p in required_providers:
            if raw_p:
                cres = await credential_resolver.resolve(raw_p, user_id)
                if cres.get("auth_status") == "active":
                    connected_providers.add(raw_p.lower())
                    if cres.get("auth_provider"):
                        connected_providers.add(cres["auth_provider"].lower())
    except Exception as exc:
        logger.warning(f"Error querying credential_resolver: {exc}")

    missing_connections: List[str] = []
    provider_results: List[Dict[str, Any]] = []

    for raw_prov in required_providers:
        if not raw_prov:
            continue
        norm = raw_prov.lower().strip()

        if is_internal_provider(norm):
            provider_results.append({
                "provider": raw_prov,
                "status": "INTERNAL_PROVIDER",
                "requires_oauth": False,
            })
            continue

        norm_mapped = normalize_provider(raw_prov).lower()
        is_conn = (
            norm in connected_providers
            or norm_mapped in connected_providers
            or (is_google_service(norm) and any(is_google_service(c) for c in connected_providers))
            or any(norm in c or c in norm for c in connected_providers)
        )

        if is_conn:
            provider_results.append({
                "provider": raw_prov,
                "status": "READY",
                "requires_oauth": True,
            })
        else:
            missing_connections.append(raw_prov)
            provider_results.append({
                "provider": raw_prov,
                "status": "MISSING_CONNECTION",
                "requires_oauth": True,
            })

    return {
        "ready": len(missing_connections) == 0,
        "missing_connections": missing_connections,
        "provider_results": provider_results,
    }
