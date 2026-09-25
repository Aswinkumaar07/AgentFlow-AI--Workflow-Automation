import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.response import success_response
from app.dependencies.auth import get_current_user
from app.models.users import User
from app.connectors.registry import connector_registry

logger = logging.getLogger("agentflow.api.v1.connectors")
router = APIRouter(prefix="/connectors", tags=["Dynamic Connector Registry"])


@router.get("", status_code=status.HTTP_200_OK)
async def list_connectors(
    current_user: User = Depends(get_current_user),
):
    """Retrieve metadata for all 16 supported SaaS & Logic connectors."""
    connectors = connector_registry.get_all_metadata()
    return success_response(data=connectors, message="Dynamic connector metadata retrieved successfully.")


@router.get("/{provider}", status_code=status.HTTP_200_OK)
async def get_connector_definition(
    provider: str,
    current_user: User = Depends(get_current_user),
):
    """Retrieve full metadata and operation schemas for a specific connector provider."""
    meta = connector_registry.get_connector_metadata(provider)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector provider '{provider}' not found in registry."
        )
    return success_response(data=meta.model_dump(), message=f"Metadata for provider '{provider}' retrieved.")


@router.get("/{provider}/{operation}", status_code=status.HTTP_200_OK)
async def get_operation_schema(
    provider: str,
    operation: str,
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve specific operation schema detailing required & optional parameters,
    field types, validation rules, and default values.
    """
    schema = connector_registry.get_operation_schema(provider, operation)
    if not schema:
        # Fallback search if provider prefix mismatch
        meta = connector_registry.get_connector_metadata(provider)
        if meta and meta.operation_schemas:
            schema = next(iter(meta.operation_schemas.values()), None)

    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operation schema '{operation}' for provider '{provider}' not found."
        )
    return success_response(data=schema.model_dump(), message=f"Operation schema for '{operation}' retrieved.")
