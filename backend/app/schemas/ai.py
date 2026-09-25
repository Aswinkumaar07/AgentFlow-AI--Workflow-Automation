from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict

class AIGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=3, description="Natural language prompt describing workflow requirements")
    services: Optional[List[str]] = Field(default=None, description="Optional target services filter")

class AIValidateRequest(BaseModel):
    workflow_json: Dict[str, Any] = Field(..., description="DAG Workflow JSON to validate")

class AIRepairRequest(BaseModel):
    workflow_json: Dict[str, Any] = Field(..., description="Broken DAG Workflow JSON")
    errors: List[str] = Field(default_factory=list, description="Validation or execution error logs")

class AIDiscoverRequest(BaseModel):
    query: str = Field(..., min_length=2, description="API capability query")

class AIGenerateResponse(BaseModel):
    user_prompt: str
    goal: str
    services: List[str]
    workflow_json: Dict[str, Any]
    validation_report: Dict[str, Any]
    is_valid: bool
    is_repaired: bool
    repair_report: Optional[Dict[str, Any]] = None
    execution_metadata: Dict[str, Any]
    logs: List[str]
    schedule: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

