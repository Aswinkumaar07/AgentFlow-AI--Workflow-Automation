from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, status
from app.dependencies.auth import get_current_user
from app.models.users import User
from app.core.response import success_response
from app.agents.connector_studio import connector_studio_ai_service

router = APIRouter(prefix="/connector-studio", tags=["Zero-Code Connector Studio Engine"])


class UploadSpecRequest(BaseModel):
    spec: Any = Field(..., description="Raw JSON/YAML OpenAPI, Swagger, GraphQL, or Postman spec")
    format_hint: Optional[str] = Field(None, description="Format hint: openapi, swagger, postman, graphql")


@router.post("/upload-spec", status_code=status.HTTP_201_CREATED)
async def generate_and_register_connector_endpoint(
    req: UploadSpecRequest,
    current_user: User = Depends(get_current_user),
):
    """Parse uploaded API specification, generate production connector, and register live for Planner V3."""
    spec = connector_studio_ai_service.generate_connector(req.spec, req.format_hint)
    return success_response(data=spec.model_dump(), message=f"Connector '{spec.provider}' generated and registered live successfully")
