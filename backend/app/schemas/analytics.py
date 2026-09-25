from typing import Dict, List, Any
from pydantic import BaseModel, ConfigDict

class DashboardStatsResponse(BaseModel):
    total_workflows: int
    active_workflows: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate_percentage: float
    avg_execution_time_ms: float
    api_calls_today: int
    system_health_status: str = "operational"
    execution_trend: List[Dict[str, Any]] = []

    model_config = ConfigDict(from_attributes=True)
