import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.workflow_scheduler import workflow_scheduler_service
from app.agents.planner.planner_v4 import intelligent_planner_v4

logger = logging.getLogger("agentflow.api.v1.scheduler")

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


class CreateJobRequestModel(BaseModel):
    prompt: str = Field(..., description="Schedule prompt (e.g. 'Tomorrow 9 AM send sales report', 'Every Monday read unread emails')")
    name: Optional[str] = Field(None, description="Optional custom job name")
    timezone: Optional[str] = Field("Asia/Kolkata", description="User timezone")


class UpdateJobRequestModel(BaseModel):
    name: Optional[str] = None
    prompt: Optional[str] = None
    timezone: Optional[str] = None
    status: Optional[str] = None


@router.post("/jobs", response_model=Dict[str, Any])
async def schedule_job(payload: CreateJobRequestModel):
    """Schedules a new workflow job."""
    plan = intelligent_planner_v4.plan(payload.prompt)
    workflow_json = plan.workflow_graph

    job = workflow_scheduler_service.schedule_job(
        prompt=payload.prompt,
        workflow_json=workflow_json,
        name=payload.name,
        user_timezone=payload.timezone or "Asia/Kolkata",
    )
    return {
        "success": True,
        "message": "Workflow job scheduled successfully.",
        "data": job.to_dict(),
    }


@router.get("/jobs", response_model=Dict[str, Any])
async def list_jobs():
    """Lists all scheduled jobs."""
    jobs = workflow_scheduler_service.list_jobs()
    return {
        "success": True,
        "message": "Scheduled jobs retrieved.",
        "data": jobs,
    }


@router.get("/jobs/{job_id}", response_model=Dict[str, Any])
async def get_job(job_id: str):
    """Retrieves a scheduled job by ID."""
    job = workflow_scheduler_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Scheduled job '{job_id}' not found.")
    return {
        "success": True,
        "message": "Job details retrieved.",
        "data": job.to_dict(),
    }


@router.put("/jobs/{job_id}", response_model=Dict[str, Any])
async def update_job(job_id: str, payload: UpdateJobRequestModel):
    """Edits an existing scheduled job."""
    updates = payload.model_dump(exclude_unset=True)
    updated_job = workflow_scheduler_service.update_job(job_id, updates)
    if not updated_job:
        raise HTTPException(status_code=404, detail=f"Scheduled job '{job_id}' not found.")
    return {
        "success": True,
        "message": "Scheduled job updated.",
        "data": updated_job.to_dict(),
    }


@router.delete("/jobs/{job_id}", response_model=Dict[str, Any])
async def cancel_job(job_id: str):
    """Cancels a scheduled job."""
    success = workflow_scheduler_service.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Scheduled job '{job_id}' not found.")
    return {
        "success": True,
        "message": f"Scheduled job '{job_id}' cancelled.",
        "data": {"job_id": job_id, "status": "cancelled"},
    }
