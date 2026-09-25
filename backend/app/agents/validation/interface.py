from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseValidationService(ABC):
    """
    Abstract Interface for Workflow & Schema Validation Module.
    
    TODO: Plug in static DAG cycle detection, type checking, and parameter validation.
    """

    @abstractmethod
    async def validate_dag_structure(self, dag: Dict[str, Any]) -> List[str]:
        """
        Check for cycles, orphan nodes, or missing required parameters.
        
        Returns:
            List of validation errors (empty if valid).
        """
        pass
