import logging
import time
from typing import Any, Dict
from app.runtime.checkpoint import checkpoint_manager
from app.runtime.execution_history import execution_history_store
from app.runtime.workflow_executor import workflow_runtime_executor_v3

logger = logging.getLogger("agentflow.services.runtime_service")


async def perform_canonical_resume(execution_id: str) -> Dict[str, Any]:
    """
    Shared canonical execution resume service.
    Restores durable checkpoint/state, delegates execution to WorkflowRuntimeExecutorV3
    with resume_execution_id, and returns standard telemetry payload.
    """
    from app.api.v1.runtime import _build_execution_response_payload

    checkpoint = await checkpoint_manager.restore(execution_id)
    state = await execution_history_store.get_state(execution_id)

    if not checkpoint and not state:
        logger.warning(f"No checkpoint or history state found for execution [{execution_id}].")
        return {
            "success": False,
            "replayed": False,
            "execution_id": execution_id,
            "status": "NOT_FOUND",
            "message": f"Execution checkpoint/state [{execution_id}] not found.",
            "can_resume": False,
        }

    # Recover workflow specification
    spec: Dict[str, Any] = {}
    if checkpoint and checkpoint.metadata.get("workflow_spec"):
        spec = dict(checkpoint.metadata["workflow_spec"])
    elif state:
        spec = {
            "workflow_id": state.workflow_id,
            "version_id": getattr(state, "version_id", None),
            "version_number": getattr(state, "version_number", None),
            "tenant_id": getattr(state, "tenant_id", "usr_1"),
        }

    # Empty-Replay Safety Guard: Verify spec contains executable workflow steps or nodes
    executable_steps = spec.get("steps") or spec.get("nodes") or []
    if not executable_steps:
        logger.warning(
            f"Execution [{execution_id}] cannot be replayed: missing executable steps or nodes in workflow_spec."
        )
        return {
            "success": False,
            "replayed": False,
            "execution_id": execution_id,
            "status": "NOT_FOUND",
            "message": f"Cannot replay execution [{execution_id}]: missing checkpoint snapshot or executable workflow definition.",
            "can_resume": False,
        }

    # Execute durable workflow resume via WorkflowRuntimeExecutorV3
    res_state = await workflow_runtime_executor_v3.execute_workflow(
        spec, resume_execution_id=execution_id
    )

    if checkpoint and checkpoint.metadata.get("version_id"):
        res_state.version_id = checkpoint.metadata.get("version_id")
        res_state.version_number = checkpoint.metadata.get("version_number")
        await execution_history_store.save_state(res_state)

    logger.info(f"Execution [{execution_id}] canonically resumed cleanly with status [{res_state.status}].")
    payload = await _build_execution_response_payload(res_state, spec)
    payload["replayed"] = res_state.status in ("COMPLETED", "SUCCESS", "RUNNING", "WAITING")
    payload["message"] = f"Execution [{execution_id}] replayed/resumed with status [{res_state.status}]."
    return payload
