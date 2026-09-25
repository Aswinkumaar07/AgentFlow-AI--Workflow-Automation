from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies.auth import get_current_user
from app.models.users import User
from app.core.response import success_response
from app.agents.oauth_ai.service import OAuthAIService

router = APIRouter(prefix="/oauth-ai", tags=["Invisible OAuth Engine"])

oauth_ai_service = OAuthAIService()


# ── Request Models ──────────────────────────────────────────────────

class PopulateNodeRequest(BaseModel):
    node: Dict[str, Any]


class PopulateWorkflowRequest(BaseModel):
    steps: List[Dict[str, Any]]


class ConnectAccountRequest(BaseModel):
    provider: str
    email_or_name: str


class SetDefaultRequest(BaseModel):
    provider: str
    account_id: str


class RefreshRequest(BaseModel):
    provider: str


class DisconnectAccountRequest(BaseModel):
    provider: str
    account_id: str


# ── Health & Status ─────────────────────────────────────────────────

@router.get("/status", status_code=status.HTTP_200_OK)
async def get_all_oauth_status(
    current_user: User = Depends(get_current_user),
):
    """Retrieve connection health status across all OAuth providers."""
    health_list = oauth_ai_service.get_all_connections_health()
    return success_response(data=health_list, message="OAuth health retrieved successfully.")


@router.get("/status/{provider}", status_code=status.HTTP_200_OK)
async def get_provider_status(
    provider: str,
    current_user: User = Depends(get_current_user),
):
    """Retrieve health status for a single provider."""
    health = oauth_ai_service.get_provider_health(provider)
    return success_response(data=health, message=f"Health for '{provider}' retrieved.")


# ── Node Population ─────────────────────────────────────────────────

@router.post("/populate-node", status_code=status.HTTP_200_OK)
async def auto_populate_node_oauth(
    req: PopulateNodeRequest,
    current_user: User = Depends(get_current_user),
):
    """Automatically populate a single node with active OAuth credentials."""
    populated = oauth_ai_service.populate_node_auth(req.node)
    return success_response(data=populated, message="Node OAuth populated successfully.")


@router.post("/populate-workflow", status_code=status.HTTP_200_OK)
async def auto_populate_workflow_oauth(
    req: PopulateWorkflowRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Bulk-populate OAuth credentials for all steps in a workflow DAG.
    Returns enriched steps, bound count, and list of providers needing re-auth.
    """
    result = oauth_ai_service.populate_workflow(req.steps)
    return success_response(data=result, message=f"Workflow populated: {result['bound_count']} accounts bound.")


# ── Account Management ──────────────────────────────────────────────

@router.get("/accounts/{provider}", status_code=status.HTTP_200_OK)
async def list_provider_accounts(
    provider: str,
    current_user: User = Depends(get_current_user),
):
    """List all connected accounts for a provider."""
    accounts = oauth_ai_service.list_accounts(provider)
    return success_response(data=accounts, message=f"Accounts for '{provider}' retrieved.")


@router.post("/connect", status_code=status.HTTP_200_OK)
async def connect_oauth_account(
    req: ConnectAccountRequest,
    current_user: User = Depends(get_current_user),
):
    """Connect or reconnect an OAuth provider account."""
    acc = oauth_ai_service.connect_account(req.provider, req.email_or_name)
    return success_response(data=acc.model_dump(exclude={"access_token", "refresh_token"}), message=f"Account connected for '{req.provider}'.")


@router.post("/set-default", status_code=status.HTTP_200_OK)
async def set_default_account(
    req: SetDefaultRequest,
    current_user: User = Depends(get_current_user),
):
    """Set a specific account as the default for its provider."""
    success = oauth_ai_service.set_default_account(req.provider, req.account_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Account '{req.account_id}' not found for '{req.provider}'.")
    return success_response(data={"provider": req.provider, "account_id": req.account_id}, message="Default account updated.")


@router.post("/disconnect-account", status_code=status.HTTP_200_OK)
async def disconnect_specific_account(
    req: DisconnectAccountRequest,
    current_user: User = Depends(get_current_user),
):
    """Disconnect a specific account (not the entire provider)."""
    success = oauth_ai_service.disconnect_account(req.provider, req.account_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Account '{req.account_id}' not found.")
    return success_response(data={"provider": req.provider, "account_id": req.account_id}, message="Account disconnected.")


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def force_refresh_token(
    req: RefreshRequest,
    current_user: User = Depends(get_current_user),
):
    """Force-refresh the OAuth token for the default account of a provider."""
    result = oauth_ai_service.force_refresh(req.provider)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message", "Refresh failed."))
    return success_response(data=result, message=result.get("message", "Token refreshed."))
