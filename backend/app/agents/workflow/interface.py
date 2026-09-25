from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseWorkflowGeneratorService(ABC):
    """
    Abstract Interface for Workflow Generation Module.
    
    TODO: Plug in LangGraph / LLM workflow builder module.
    Translates execution plans into executable JSON DAG schemas and Python SDK code.
    """

    @abstractmethod
    async def generate_workflow_dag(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate DAG definition containing nodes, edges, trigger rules, and parameters.
        """
        pass

    @abstractmethod
    async def generate_python_sdk(self, dag: Dict[str, Any]) -> str:
        """
        Generate standalone Python SDK code snippet for execution.
        """
        pass
