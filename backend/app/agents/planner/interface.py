from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BasePlannerService(ABC):
    """
    Abstract Interface for AI Task Planning Module.
    
    TODO: Implement multi-step reasoning planner using LangGraph or AutoGen.
    This interface abstracts user prompt interpretation into structured execution plans.
    """

    @abstractmethod
    async def create_execution_plan(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Decompose a natural language user prompt into an ordered sequence of agent actions.
        
        Args:
            prompt: User request in natural language.
            context: Additional user context or schema specifications.

        Returns:
            Dict containing step-by-step DAG execution plan.
        """
        pass
