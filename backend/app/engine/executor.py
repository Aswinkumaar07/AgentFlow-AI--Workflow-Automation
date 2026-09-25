import asyncio
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Set

from app.connectors.manager import connector_manager
from app.engine.compiler import workflow_compiler
from app.engine.exceptions import ApprovalPendingException, WorkflowExecutionError
from app.engine.human.approval import human_approval_handler
from app.engine.interfaces import BaseWorkflowExecutor
from app.engine.models import (
    StepDefinitionModel,
    StepExecutionStateModel,
    StepType,
    WorkflowDefinitionModel,
    WorkflowExecutionStateModel,
    WorkflowStatus,
)
from app.engine.state_machine import state_machine

logger = logging.getLogger("agentflow.engine.executor")


class WorkflowExecutor(BaseWorkflowExecutor):
    """Enterprise Workflow DAG Execution Engine featuring Parallel Step Dispatch, Structured Telemetry, & Persistent Checkpoints."""

    def __init__(self) -> None:
        self.compiler = workflow_compiler
        self.state_store = state_machine
        self.approval_handler = human_approval_handler
        self.connector_manager = connector_manager

    async def execute_workflow(
        self, workflow: WorkflowDefinitionModel, initial_context: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecutionStateModel:
        execution_id = f"exec_{uuid.uuid4().hex[:12]}"
        context = dict(initial_context or {})

        execution_state = WorkflowExecutionStateModel(
            execution_id=execution_id,
            workflow_id=workflow.workflow_id,
            tenant_id=workflow.tenant_id,
            status=WorkflowStatus.RUNNING,
            context_data=context,
        )

        for step in workflow.steps:
            execution_state.step_states[step.step_id] = StepExecutionStateModel(
                step_id=step.step_id, status=WorkflowStatus.PENDING
            )

        await self.state_store.save_state(execution_state)
        logger.info(f"Started Workflow Execution [{execution_id}] for DAG [{workflow.workflow_id}] ({len(workflow.steps)} steps).")

        completed_steps: Set[str] = set()

        while len(completed_steps) < len(workflow.steps):
            ready_steps = [
                s for s in workflow.steps
                if s.step_id not in completed_steps and all(dep in completed_steps for dep in s.dependencies)
            ]

            if not ready_steps:
                if any(execution_state.step_states[s.step_id].status == WorkflowStatus.WAITING_FOR_APPROVAL for s in workflow.steps):
                    execution_state.status = WorkflowStatus.WAITING_FOR_APPROVAL
                    await self.state_store.save_state(execution_state)
                    return execution_state
                break

            tasks = [self._execute_single_step(execution_id, step, context) for step in ready_steps]
            step_results = await asyncio.gather(*tasks, return_exceptions=True)

            for step, res in zip(ready_steps, step_results):
                if isinstance(res, Exception):
                    if isinstance(res, ApprovalPendingException):
                        execution_state.status = WorkflowStatus.WAITING_FOR_APPROVAL
                        await self.state_store.save_state(execution_state)
                        return execution_state

                    logger.error(f"Step [{step.step_id}] failed: {res}")
                    execution_state.status = WorkflowStatus.FAILED
                    execution_state.end_time = time.time()
                    await self.state_store.save_state(execution_state)
                    return execution_state

                completed_steps.add(step.step_id)
                if isinstance(res, dict):
                    context.update(res)

        execution_state.status = WorkflowStatus.COMPLETED
        execution_state.end_time = time.time()
        execution_state.context_data = context
        await self.state_store.save_state(execution_state)

        duration = (execution_state.end_time - execution_state.start_time) * 1000.0
        logger.info(f"Workflow Execution [{execution_id}] COMPLETED successfully in {duration:.2f}ms!")

        return execution_state

    async def _execute_single_step(
        self, execution_id: str, step: StepDefinitionModel, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        step_start_time = time.perf_counter()
        await self.state_store.transition_step(execution_id, step.step_id, WorkflowStatus.RUNNING)

        if step.step_type == StepType.HUMAN_APPROVAL:
            await self.approval_handler.pause_for_approval(execution_id, step.step_id)
            raise ApprovalPendingException(f"Step '{step.step_id}' paused for human approval.", workflow_id=execution_id)

        if step.step_type == StepType.CONNECTOR_ACTION and step.provider and step.provider.lower() != "generic":
            conn_res = await self.connector_manager.execute(
                provider=step.provider,
                operation_id=step.operation_id,
                parameters=step.parameters,
                tenant_id="default",
                timeout_seconds=step.timeout_seconds,
            )

            latency = (time.perf_counter() - step_start_time) * 1000.0
            res_payload = {
                "status_code": conn_res.status_code,
                "latency_ms": round(conn_res.latency_ms or latency, 2),
                "retries_used": conn_res.retries_used,
                "data": conn_res.data,
                "error": conn_res.error_message,
            }
            await self.state_store.transition_step(execution_id, step.step_id, WorkflowStatus.COMPLETED, res_payload)
            return {step.step_id: res_payload}

        latency = (time.perf_counter() - step_start_time) * 1000.0
        res_data = {
            "step_id": step.step_id,
            "status": "executed",
            "latency_ms": round(latency, 2),
            "params": step.parameters,
        }
        await self.state_store.transition_step(execution_id, step.step_id, WorkflowStatus.COMPLETED, res_data)
        return {step.step_id: res_data}


workflow_executor = WorkflowExecutor()
