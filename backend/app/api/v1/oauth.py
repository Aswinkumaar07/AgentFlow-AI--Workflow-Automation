import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from app.oauth.manager import OAuthManager, oauth_manager
from app.core.response import success_response
from app.core.config import settings

router = APIRouter(prefix="/oauth", tags=["OAuth Connection Center"])
logger = logging.getLogger("agentflow.api.oauth")


@router.get("/providers")
async def get_providers():
    """Returns list of supported OAuth providers."""
    providers = OAuthManager.get_supported_providers()
    logger.info(f"[AUTH-6] OAuth providers loaded: count={len(providers)}")
    return success_response(data=providers, message="Providers retrieved.")


@router.get("/{provider}/login")
async def get_login_url(provider: str, user_id: str = "usr_1"):
    """Generates OAuth login redirect URL for provider."""
    url = oauth_manager.get_login_url(provider, user_id=user_id)
    logger.info(f"[AUTH-6] OAuth login requested for '{provider}'")
    return success_response(data={"provider": provider, "url": url}, message="Login URL generated.")


@router.get("/{provider}/callback")
async def handle_oauth_callback(
    provider: str,
    code: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    user_id: str = "usr_1",
):
    """
    Handles OAuth redirect callback and exchanges code for access token.
    Redirects browser directly to frontend /oauth/result page instead of returning raw JSON.
    """
    frontend_base = settings.FRONTEND_URL.rstrip("/")
    prov_lower = provider.lower()

    if error or not code:
        logger.error(f"[AUTH-9] OAuth callback failed or missing authorization code: provider={provider} error={error}")
        return RedirectResponse(
            url=f"{frontend_base}/oauth/result?provider={prov_lower}&status=error",
            status_code=302,
        )

    try:
        conn = await oauth_manager.handle_callback(user_id=user_id, provider=provider, code=code)
        logger.info(f"[AUTH-9] OAuth callback success: provider={provider} user_id={user_id}")
        logger.info(f"[AUTH-9] Credential stored: provider={conn.provider} connection_id={conn.id}")
        return RedirectResponse(
            url=f"{frontend_base}/oauth/result?provider={prov_lower}&status=success",
            status_code=302,
        )
    except Exception as exc:
        logger.error(f"[AUTH-9] OAuth callback exception: provider={provider} exc={exc}")
        return RedirectResponse(
            url=f"{frontend_base}/oauth/result?provider={prov_lower}&status=error",
            status_code=302,
        )


@router.get("/connections")
async def get_user_connections(user_id: str = "usr_1"):
    """Returns list of active connected OAuth accounts for user."""
    conns = await oauth_manager.get_user_connections(user_id=user_id)
    safe = [c.model_dump(exclude={"access_token", "refresh_token"}) for c in conns]
    logger.info(f"[AUTH-4] OAuth connections loaded: count={len(safe)} user_id={user_id}")
    return success_response(data=safe, message="Connections retrieved.")


@router.get("/connections/health")
async def get_connections_health(user_id: str = "usr_1"):
    """Returns health snapshot for all connections — expiry, status."""
    health = await oauth_manager.get_connection_health(user_id=user_id)
    logger.info(f"[AUTH-10] OAuth connection health loaded: count={len(health)}")
    return success_response(data=health, message="Connection health retrieved.")


@router.post("/refresh")
async def refresh_connection(payload: Dict[str, str]):
    """Forces token refresh for a specific provider connection."""
    provider = payload.get("provider")
    user_id = payload.get("user_id", "usr_1")
    if not provider:
        raise HTTPException(status_code=400, detail="Provider field is required.")
    conn = await oauth_manager.refresh_connection(user_id=user_id, provider=provider)
    if not conn:
        raise HTTPException(status_code=404, detail=f"No connection found for provider '{provider}'.")
    logger.info(f"[AUTH-4] Connection refreshed: provider={provider}")
    return success_response(
        data=conn.model_dump(exclude={"access_token", "refresh_token"}),
        message=f"Token refreshed for '{provider}'.",
    )


@router.post("/disconnect")
async def disconnect_provider(payload: Dict[str, str]):
    """Disconnects and revokes an OAuth provider connection."""
    provider = payload.get("provider")
    user_id = payload.get("user_id", "usr_1")
    if not provider:
        raise HTTPException(status_code=400, detail="Provider field is required.")
    success = await oauth_manager.disconnect(user_id=user_id, provider=provider)
    if not success:
        raise HTTPException(status_code=404, detail=f"No active connection found for provider '{provider}'.")
    logger.info(f"[AUTH-4] Disconnected provider: provider={provider}")
    return success_response(data={"provider": provider}, message=f"Disconnected '{provider}' successfully.")
