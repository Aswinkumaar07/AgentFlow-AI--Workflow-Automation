from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, status
from app.dependencies.auth import get_current_user
from app.models.users import User
from app.core.response import success_response
from app.agents.marketplace import marketplace_ai_service

router = APIRouter(prefix="/marketplace", tags=["AI-Powered Workflow Marketplace"])


class PublishWorkflowRequest(BaseModel):
    title: str
    description: str
    workflow_graph: Dict[str, Any]


class RecommendRequest(BaseModel):
    query: str


class PersonalizeRequest(BaseModel):
    template_id: str
    user_context: Dict[str, Any] = Field(default_factory=dict)


class ForkRequest(BaseModel):
    template_id: str


class RateRequest(BaseModel):
    template_id: str
    stars: float = Field(..., ge=1.0, le=5.0)


class CommentRequest(BaseModel):
    template_id: str
    content: str


@router.get("/templates", status_code=status.HTTP_200_OK)
async def list_marketplace_templates(current_user: User = Depends(get_current_user)):
    """List all AI-analyzed templates in marketplace catalog."""
    templates = marketplace_ai_service.list_templates()
    return success_response(data=[t.model_dump() for t in templates], message="Marketplace templates retrieved successfully")


@router.post("/publish", status_code=status.HTTP_201_CREATED)
async def publish_workflow_to_marketplace(
    req: PublishWorkflowRequest,
    current_user: User = Depends(get_current_user),
):
    """Publish workflow DAG into the AI Marketplace with automated metadata extraction."""
    user_identity = current_user.full_name or current_user.email or str(current_user.id)
    tpl = marketplace_ai_service.publish(req.title, req.description, req.workflow_graph, author=user_identity)
    return success_response(data=tpl.model_dump(), message="Workflow published to marketplace successfully")


@router.post("/recommend", status_code=status.HTTP_200_OK)
async def recommend_marketplace_templates(
    req: RecommendRequest,
    current_user: User = Depends(get_current_user),
):
    """Semantic search & AI template recommendation based on prompt."""
    results = marketplace_ai_service.search_recommend(req.query)
    return success_response(data=[r.model_dump() for r in results], message="Recommended templates retrieved successfully")


@router.post("/personalize", status_code=status.HTTP_200_OK)
async def personalize_marketplace_template(
    req: PersonalizeRequest,
    current_user: User = Depends(get_current_user),
):
    """One-click AI personalization of template node parameters for user context."""
    ctx = req.user_context or {"email": current_user.email, "company": "User Org"}
    graph = marketplace_ai_service.personalize(req.template_id, ctx)
    return success_response(data=graph, message="Template personalized successfully")


@router.post("/fork", status_code=status.HTTP_201_CREATED)
async def fork_marketplace_template(
    req: ForkRequest,
    current_user: User = Depends(get_current_user),
):
    """Fork workflow template into user workspace lineage."""
    user_identity = current_user.full_name or current_user.email or str(current_user.id)
    forked = marketplace_ai_service.fork(req.template_id, user_id=user_identity)
    return success_response(data=forked.model_dump(), message="Workflow forked successfully")


@router.post("/rate", status_code=status.HTTP_200_OK)
async def rate_marketplace_template(
    req: RateRequest,
    current_user: User = Depends(get_current_user),
):
    """Add community rating to template."""
    tpl = marketplace_ai_service.rate(req.template_id, req.stars)
    return success_response(data=tpl.model_dump(), message="Rating submitted successfully")


@router.post("/comment", status_code=status.HTTP_200_OK)
async def comment_marketplace_template(
    req: CommentRequest,
    current_user: User = Depends(get_current_user),
):
    """Add community discussion comment to template."""
    user_identity = current_user.full_name or current_user.email or str(current_user.id)
    tpl = marketplace_ai_service.comment(req.template_id, user_name=user_identity, content=req.content)
    return success_response(data=tpl.model_dump(), message="Comment added successfully")
