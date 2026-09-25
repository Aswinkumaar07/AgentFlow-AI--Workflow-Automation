from typing import Any, Dict, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, status
from app.dependencies.auth import get_current_user
from app.models.users import User
from app.core.response import success_response
from app.agents.parameter_autofill import parameter_autofill_service

router = APIRouter(prefix="/parameter-autofill", tags=["Parameter Autofill Engine"])


class AutofillRequest(BaseModel):
    graph: Dict[str, Any]
    prompt: Optional[str] = ""


class ExtractRequest(BaseModel):
    provider: str
    operation_id: str
    prompt: str
    existing_parameters: Optional[Dict[str, Any]] = None


@router.post("/autofill", status_code=status.HTTP_200_OK)
async def autofill_workflow_parameters(
    req: AutofillRequest,
    current_user: User = Depends(get_current_user),
):
    """Autofill and pre-configure all node parameters in a workflow graph with prompt context."""
    configured = parameter_autofill_service.autofill_graph(req.graph, prompt=req.prompt or "")
    return success_response(data=configured, message="Workflow graph parameters autofilled successfully")


@router.post("/extract", status_code=status.HTTP_200_OK)
async def extract_node_parameters(
    req: ExtractRequest,
    current_user: User = Depends(get_current_user),
):
    """Extract parameters, confidence scores, and missing parameters for a prompt and operation."""
    extracted = parameter_autofill_service.extract_prompt_parameters(
        provider=req.provider,
        operation_id=req.operation_id,
        prompt=req.prompt,
        existing_params=req.existing_parameters,
    )
    return success_response(data=extracted, message="Node parameters extracted successfully")
