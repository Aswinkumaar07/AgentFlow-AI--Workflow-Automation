from typing import TypedDict, List, Dict, Any, Optional

class WorkflowState(TypedDict, total=False):
    """
    Strongly typed shared LangGraph state passed across all agent nodes.
    """
    user_prompt: str
    goal: str
    services: List[str]
    tasks: List[Dict[str, Any]]
    api_candidates: List[Dict[str, Any]]
    retrieved_documents: List[Dict[str, Any]]
    workflow_json: Dict[str, Any]
    validation_report: Dict[str, Any]
    repair_report: Dict[str, Any]
    execution_metadata: Dict[str, Any]
    memory_matches: List[Dict[str, Any]]
    logs: List[str]
    timestamps: Dict[str, str]
    retry_count: int
    current_step: str
    is_valid: bool
    is_repaired: bool
    error_message: Optional[str]
