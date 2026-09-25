import logging
import time
from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from app.triggers.engine import TriggerType, WorkflowActivationStatus, trigger_engine

router = APIRouter(prefix="/triggers", tags=["Trigger Engine & Activation"])
logger = logging.getLogger("agentflow.api.triggers")


@router.get("")
async def get_triggers():
    """Returns list of registered triggers and workflow activation statuses."""
    return [t.model_dump() for t in trigger_engine._triggers.values()]


@router.post("/register")
async def register_trigger(payload: Dict[str, Any]):
    """Registers a new workflow trigger subscription."""
    workflow_id = payload.get("workflow_id", "wf_custom")
    trigger_type_str = payload.get("trigger_type", "WEBHOOK")
    config = payload.get("config", {})
    workflow_spec = payload.get("workflow_spec", {"workflow_id": workflow_id, "steps": []})

    try:
        t_type = TriggerType(trigger_type_str.upper())
    except ValueError:
        t_type = TriggerType.WEBHOOK

    sub = await trigger_engine.register_trigger(
        workflow_id=workflow_id,
        trigger_type=t_type,
        config=config,
        workflow_spec=workflow_spec,
    )
    return {"message": "Trigger registered successfully", "subscription": sub.model_dump()}


@router.post("/webhooks/{trigger_type}")
async def receive_webhook_event(trigger_type: str, payload: Dict[str, Any]):
    """Receives incoming external webhook/event payloads and dispatches active workflows."""
    try:
        t_type = TriggerType(trigger_type.upper())
    except ValueError:
        # Fallback to single trigger_id dispatch if trigger_type is not an enum value
        return await receive_single_webhook(trigger_id=trigger_type, payload=payload)

    executions = await trigger_engine.process_incoming_event(trigger_type=t_type, payload=payload)
    return {
        "message": f"Processed incoming {t_type.value} event",
        "dispatched_count": len(executions),
        "executions": executions,
    }


@router.post("/webhook/{trigger_id}")
async def receive_single_webhook(trigger_id: str, payload: Dict[str, Any]):
    """Receives an incoming HTTP webhook for a specific trigger_id or workflow_id."""
    from app.runtime.execution_analytics import sanitize_telemetry_secrets
    from app.runtime.workflow_executor import workflow_runtime_executor_v3
    from app.versions.manager import workflow_version_manager

    # Attempt loading target workflow spec
    workflow_id = trigger_id if not trigger_id.startswith("trig_") else "wf_studio_1"
    
    # Get latest pinned snapshot or active definition
    history = await workflow_version_manager.get_version_history(workflow_id)
    if history and history[0].workflow_spec:
        wf_spec = dict(history[0].workflow_spec)
        wf_spec["workflow_id"] = workflow_id
        wf_spec["version_id"] = history[0].version_id
        wf_spec["version_number"] = history[0].version_number
    else:
        wf_spec = {"workflow_id": workflow_id, "nodes": [], "edges": []}

    initial_context = {
        "_trigger_type": "webhook",
        "trigger": {
            "trigger_id": trigger_id,
            "body": payload,
            "payload": payload,
            "headers": {},
            "timestamp": time.time(),
        },
    }

    exec_state = await workflow_runtime_executor_v3.execute_workflow(
        workflow_spec=wf_spec, initial_context=initial_context
    )

    res = {
        "success": True,
        "message": f"Webhook [{trigger_id}] processed successfully",
        "trigger_id": trigger_id,
        "execution_id": exec_state.execution_id,
        "status": exec_state.status,
    }
    return sanitize_telemetry_secrets(res)

