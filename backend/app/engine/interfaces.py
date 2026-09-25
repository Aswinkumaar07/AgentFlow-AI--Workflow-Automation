from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from app.engine.models import (
    StepDefinitionModel,
    WorkflowDefinitionModel,
    WorkflowExecutionStateModel,
)


class BaseWorkflowCompiler(ABC):
    """Interface for compiling workflow specs into executable DAG structures."""

    @abstractmethod
    def compile(self, raw_workflow: Dict[str, Any]) -> WorkflowDefinitionModel:
        """Parses and validates raw JSON/YAML workflow dict into WorkflowDefinitionModel."""
        raise NotImplementedError


class BaseWorkflowStateStore(ABC):
    """Interface for Persistent Checkpointing & Execution State Persistence."""

    @abstractmethod
    async def save_state(self, state: WorkflowExecutionStateModel) -> None:
        """Persists current workflow state checkpoint."""
        raise NotImplementedError

    @abstractmethod
    async def get_state(self, execution_id: str) -> Optional[WorkflowExecutionStateModel]:
        """Retrieves checkpointed workflow execution state."""
        raise NotImplementedError


class BaseWorkflowQueue(ABC):
    """Interface for Distributed Workflow Worker Queue."""

    @abstractmethod
    async def enqueue_step(self, execution_id: str, step: StepDefinitionModel) -> None:
        """Enqueues step task for worker dispatch."""
        raise NotImplementedError


class BaseWorkflowScheduler(ABC):
    """Interface for Cron and Event-Driven Workflow Scheduling."""

    @abstractmethod
    def schedule_cron(self, workflow_id: str, cron_expression: str) -> None:
        """Schedules recurring cron workflow trigger."""
        raise NotImplementedError


class BaseWorkflowExecutor(ABC):
    """Interface for Workflow Execution Engine."""

    @abstractmethod
    async def execute_workflow(
        self, workflow: WorkflowDefinitionModel, initial_context: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecutionStateModel:
        """Executes a workflow definition DAG end-to-end."""
        raise NotImplementedError
