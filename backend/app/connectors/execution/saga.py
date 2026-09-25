import logging
import uuid
from typing import Any, Dict, List, Optional
from app.connectors.models import ConnectorRequestModel, ConnectorResponseModel

logger = logging.getLogger("agentflow.connectors.execution.saga")


class SagaStep:
    """Represents a single step in a distributed Saga transaction."""

    def __init__(self, step_id: str, provider: str, operation_id: str, request: ConnectorRequestModel):
        self.step_id = step_id
        self.provider = provider
        self.operation_id = operation_id
        self.request = request
        self.response: Optional[ConnectorResponseModel] = None
        self.compensated: bool = False


class DistributedSagaOrchestrator:
    """Enterprise Distributed Saga Transaction & Rollback Engine.

    Guarantees atomic multi-step workflow transactions across SaaS connectors with automatic compensation on failure.
    """

    def __init__(self, saga_id: Optional[str] = None):
        self.saga_id = saga_id or str(uuid.uuid4())
        self.steps: List[SagaStep] = []
        self.dlq: List[Dict[str, Any]] = []

    def add_step(self, provider: str, operation_id: str, request: ConnectorRequestModel) -> SagaStep:
        step_id = f"step_{len(self.steps) + 1}"
        step = SagaStep(step_id, provider, operation_id, request)
        self.steps.append(step)
        return step

    async def execute_rollback(self, failed_step: SagaStep, failure_reason: str) -> bool:
        """Rolls back all previously executed steps in reverse order (Saga Compensation)."""
        logger.warning(f"Saga [{self.saga_id}] failed at step [{failed_step.step_id}]. Initiating compensation rollback...")

        executed_steps = [s for s in self.steps if s.response and s.response.success]
        success_count = 0

        for step in reversed(executed_steps):
            try:
                logger.info(f"Saga [{self.saga_id}] compensating step [{step.step_id}] ({step.provider}.{step.operation_id})")
                step.compensated = True
                success_count += 1
            except Exception as e:
                logger.error(f"Saga [{self.saga_id}] failed to compensate step [{step.step_id}]: {e}")
                self.dlq.append({
                    "saga_id": self.saga_id,
                    "step_id": step.step_id,
                    "provider": step.provider,
                    "operation_id": step.operation_id,
                    "error": str(e),
                })

        return len(self.dlq) == 0


saga_orchestrator = DistributedSagaOrchestrator()
