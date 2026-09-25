import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from app.templates.engine import template_engine
from app.core.response import success_response, error_response

router = APIRouter(prefix="/templates", tags=["Template Marketplace"])
logger = logging.getLogger("agentflow.api.templates")


class InstantiateTemplateRequestModel(BaseModel):
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom parameter values")
    user_id: Optional[str] = Field(default="usr_1", description="User or tenant identifier")


@router.get("")
async def get_templates(
    category: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    featured: bool = Query(default=False),
):
    """Returns list of pre-built workflow templates."""
    templates = template_engine.get_templates(category=category, search=search, featured_only=featured)
    data = [t.model_dump() for t in templates]
    return success_response(data=data, message="Workflow templates retrieved successfully")


@router.get("/categories")
async def get_categories():
    """Returns available template categories."""
    categories = template_engine.get_categories()
    return success_response(data=categories, message="Template categories retrieved successfully")


@router.get("/{template_id}")
async def get_template_by_id(template_id: str):
    """Returns details for a specific template."""
    tpl = template_engine.get_template_by_id(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail=f"Template [{template_id}] not found")
    return success_response(data=tpl.model_dump(), message="Template details retrieved successfully")


from app.services.connection_readiness import check_workflow_readiness


@router.post("/{template_id}/instantiate")
async def instantiate_template(template_id: str, payload: Optional[InstantiateTemplateRequestModel] = None):
    """
    Instantiates a workflow template into a validated AgentFlow DAG graph with custom parameters and pinned version snapshot.
    """
    try:
        user_params = payload.parameters if payload else {}
        user_id = payload.user_id if payload else "usr_1"

        tpl = template_engine.get_template_by_id(template_id)
        if not tpl:
            raise HTTPException(status_code=404, detail=f"Template [{template_id}] not found")

        req_providers = tpl.required_providers or tpl.connectors or []
        readiness = await check_workflow_readiness(req_providers, user_id=user_id)
        if not readiness["ready"]:
            missing_str = ", ".join(readiness["missing_connections"])
            raise HTTPException(
                status_code=400,
                detail={
                    "ready": False,
                    "missing_connections": readiness["missing_connections"],
                    "message": f"Connection required for provider(s): {missing_str}",
                },
            )

        res = await template_engine.instantiate_template(template_id, user_parameters=user_params, user_id=user_id)
        return success_response(data=res, message=f"Workflow instantiated successfully from template [{template_id}]")
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error instantiating template [{template_id}]: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to instantiate template: {str(exc)}")


@router.post("/{template_id}/clone")
async def clone_template(template_id: str, user_id: str = "usr_1"):
    """Clones a template into a new executable workflow (backward compatibility)."""
    try:
        cloned_wf = template_engine.clone_template(template_id, user_id=user_id)
        return success_response(data={"message": "Template cloned successfully", "workflow": cloned_wf})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

