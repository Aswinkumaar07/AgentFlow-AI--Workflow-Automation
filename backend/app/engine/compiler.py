import logging
from typing import Any, Dict, List, Set
from app.engine.exceptions import WorkflowCompilationError
from app.engine.interfaces import BaseWorkflowCompiler
from app.engine.models import StepDefinitionModel, StepType, WorkflowDefinitionModel

logger = logging.getLogger("agentflow.engine.compiler")


class WorkflowCompiler(BaseWorkflowCompiler):
    """Enterprise Workflow Compiler parsing JSON/YAML graph specifications into validated DAG state machines."""

    def compile(self, raw_workflow: Dict[str, Any]) -> WorkflowDefinitionModel:
        if not isinstance(raw_workflow, dict):
            raise WorkflowCompilationError("Raw workflow payload must be a dictionary.")

        workflow_id = raw_workflow.get("workflow_id", raw_workflow.get("id", "wf_compiled"))
        name = raw_workflow.get("name", "Compiled Workflow")
        version = raw_workflow.get("version", "v1")
        tenant_id = raw_workflow.get("tenant_id", "default")
        cron = raw_workflow.get("cron_schedule", raw_workflow.get("cron"))

        steps_raw = raw_workflow.get("steps", raw_workflow.get("tasks", []))
        compiled_steps: List[StepDefinitionModel] = []

        for step_dict in steps_raw:
            if isinstance(step_dict, dict):
                s_type = step_dict.get("step_type", step_dict.get("type", "CONNECTOR_ACTION"))
                if "APPROVAL" in str(s_type).upper():
                    st_enum = StepType.HUMAN_APPROVAL
                elif "PARALLEL" in str(s_type).upper():
                    st_enum = StepType.PARALLEL
                elif "CONDITION" in str(s_type).upper():
                    st_enum = StepType.CONDITION
                else:
                    st_enum = StepType.CONNECTOR_ACTION

                step_model = StepDefinitionModel(
                    step_id=step_dict.get("step_id", step_dict.get("task_id", f"step_{len(compiled_steps)+1}")),
                    step_type=st_enum,
                    provider=step_dict.get("provider", step_dict.get("service", "Generic")),
                    operation_id=step_dict.get("operation_id", step_dict.get("action", "")),
                    parameters=step_dict.get("parameters", step_dict.get("params", {})),
                    dependencies=step_dict.get("dependencies", []),
                    retry_attempts=step_dict.get("retry_attempts", 3),
                    timeout_seconds=step_dict.get("timeout_seconds", 30.0),
                )
                compiled_steps.append(step_model)

        self._validate_dag(compiled_steps)

        model = WorkflowDefinitionModel(
            workflow_id=workflow_id,
            name=name,
            version=version,
            tenant_id=tenant_id,
            steps=compiled_steps,
            cron_schedule=cron,
        )
        logger.info(f"Compiled Workflow DAG [{workflow_id}] with {len(compiled_steps)} steps.")
        return model

    def _validate_dag(self, steps: List[StepDefinitionModel]) -> None:
        """Validates DAG graph for cycles and invalid dependencies."""
        step_ids = {s.step_id for s in steps}

        # 1. Check for invalid dependency references
        for s in steps:
            for dep in s.dependencies:
                if dep not in step_ids:
                    raise WorkflowCompilationError(f"Step '{s.step_id}' references unknown dependency '{dep}'.")

        # 2. Cycle detection via Topological Sort (Kahn's Algorithm)
        in_degree = {s.step_id: 0 for s in steps}
        adj = {s.step_id: [] for s in steps}

        for s in steps:
            for dep in s.dependencies:
                adj[dep].append(s.step_id)
                in_degree[s.step_id] += 1

        queue = [sid for sid, deg in in_degree.items() if deg == 0]
        visited_count = 0

        while queue:
            node = queue.pop(0)
            visited_count += 1
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count != len(steps):
            raise WorkflowCompilationError("Cyclic dependency detected in Workflow DAG specification.")


workflow_compiler = WorkflowCompiler()
