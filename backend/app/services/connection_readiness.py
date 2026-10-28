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


def is_dynamic_openapi_operation(step_or_data: Any) -> bool:
    """Checks if a step, node parameter dict, or provider string represents a dynamic OpenAPI operation."""
    if not step_or_data:
        return False

    if isinstance(step_or_data, str):
        norm = step_or_data.lower().strip()
        return norm == "generic_rest" or "openapi" in norm

    if isinstance(step_or_data, dict):
        params = step_or_data.get("parameters") if isinstance(step_or_data.get("parameters"), dict) else {}
        data = step_or_data.get("data") if isinstance(step_or_data.get("data"), dict) else step_or_data

        prov = str(step_or_data.get("provider") or data.get("provider") or params.get("provider") or "").lower().strip()

        is_dynamic = bool(
            step_or_data.get("is_dynamic_api")
            or data.get("is_dynamic_api")
            or params.get("is_dynamic_api")
            or prov == "generic_rest"
            or "openapi" in prov
        )
        return is_dynamic

    return False


def is_dynamic_public_openapi_operation(step_or_data: Any) -> bool:
    """Checks if a step or node parameter dict represents a public dynamic OpenAPI operation."""
    if not is_dynamic_openapi_operation(step_or_data):
        return False

    if not isinstance(step_or_data, dict):
        return False

    params = step_or_data.get("parameters") if isinstance(step_or_data.get("parameters"), dict) else {}
    data = step_or_data.get("data") if isinstance(step_or_data.get("data"), dict) else step_or_data

    sec_schemes = step_or_data.get("security_schemes") or data.get("security_schemes") or params.get("security_schemes") or {}
    sec_reqs = step_or_data.get("security_requirements") or data.get("security_requirements") or params.get("security_requirements") or []

    has_schemes = isinstance(sec_schemes, dict) and len(sec_schemes) > 0
    has_reqs = isinstance(sec_reqs, list) and len(sec_reqs) > 0

    return not has_schemes and not has_reqs


async def check_step_readiness(steps: List[Dict[str, Any]], user_id: str = "usr_1") -> Dict[str, Any]:
    """
    Step-level connection readiness checker.
    Distinguishes native OAuth connectors (Gmail, Slack, Drive, etc.) from dynamic OpenAPI operations.
    Dynamic OpenAPI operations (both public and authenticated) are allowed through the native OAuth preflight gate;
    runtime security evaluation for authenticated OpenAPI endpoints is handled by GenericRESTAdapter.
    """
    req_providers: List[str] = []
    for step in steps:
        if isinstance(step, dict):
            if is_dynamic_openapi_operation(step):
                continue
            prov = str(step.get("provider") or "").strip()
            if prov and not is_internal_provider(prov):
                req_providers.append(prov)
        elif isinstance(step, str) and step.strip():
            if not is_internal_provider(step) and not is_dynamic_openapi_operation(step):
                req_providers.append(step)

    return await check_workflow_readiness(req_providers, user_id=user_id)


async def check_workflow_readiness(required_providers: List[Any], user_id: str = "usr_1") -> Dict[str, Any]:
    """
    Central connection readiness checker.
    Queries active user connections in OAuthManager and SecretManager.
    Distinguishes INTERNAL_PROVIDER, READY, and MISSING_CONNECTION states.
    """
    if required_providers and isinstance(required_providers[0], dict):
        return await check_step_readiness(required_providers, user_id=user_id)

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
            if raw_p and isinstance(raw_p, str):
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

        if isinstance(raw_prov, dict):
            if is_dynamic_openapi_operation(raw_prov):
                provider_results.append({
                    "provider": raw_prov.get("provider") or "generic_rest",
                    "status": "READY",
                    "requires_oauth": False,
                })
                continue
            raw_prov = str(raw_prov.get("provider") or "").strip()

        norm = str(raw_prov).lower().strip()

        if is_internal_provider(norm):
            provider_results.append({
                "provider": raw_prov,
                "status": "INTERNAL_PROVIDER",
                "requires_oauth": False,
            })
            continue

        if is_dynamic_openapi_operation(norm):
            provider_results.append({
                "provider": raw_prov,
                "status": "READY",
                "requires_oauth": False,
            })
            continue

        norm_mapped = normalize_provider(str(raw_prov)).lower()
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
