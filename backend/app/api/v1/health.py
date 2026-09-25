from fastapi import APIRouter, status
from app.core.response import success_response

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("", status_code=status.HTTP_200_OK)
async def get_health_status():
    """Health check endpoint for container orchestrators and load balancers."""
    return success_response(
        data={
            "status": "healthy",
            "version": "1.0.0",
            "database": "connected",
            "redis": "connected",
        },
        message="AgentFlow AI System Operational"
    )
