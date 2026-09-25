import asyncio
import inspect
import json
import logging
import time
import uuid
from typing import Any, Dict, Optional, Set

from app.runtime.approval import human_approval_engine
from app.runtime.checkpoint import checkpoint_manager
from app.runtime.context import ExecutionContext
from app.runtime.dependency_resolver import dependency_resolver
from app.runtime.dlq import dead_letter_queue
from app.runtime.error_classifier import classify_error
from app.runtime.events.event_bus import event_bus
from app.runtime.events.event_types import RuntimeEvent, RuntimeEventType
from app.runtime.exceptions import WorkflowCancelledException
from app.runtime.execution_analytics import execution_history_store, sanitize_telemetry_secrets
from app.runtime.lifecycle import WorkflowLifecycle, WorkflowLifecycleState
from app.runtime.scheduler import runtime_scheduler
from app.runtime.state import WorkflowExecutionStateV2
from app.runtime.wait_handler import wait_handler

logger = logging.getLogger("agentflow.runtime.workflow_executor")


class WorkflowRuntimeExecutorV3:
    """Production Workflow Orchestration Engine (Runtime Engine v3) with Durable Execution, Event Bus, Checkpoint Restore, & DLQ."""

    def __init__(self) -> None:
        self.resolver = dependency_resolver
        self.scheduler = runtime_scheduler
        self.history_store = execution_history_store
        self.checkpoint_manager = checkpoint_manager
        self.dlq = dead_letter_queue
        self.event_bus = event_bus
        self.lifecycle = WorkflowLifecycle()
        self.wait_handler = wait_handler
        self.approval_engine = human_approval_engine
        self._control_signals: Dict[str, str] = {}

    def _normalize_steps(self, workflow_spec: Dict[str, Any]) -> list:
        steps = workflow_spec.get("steps") or []
        if steps:
            return steps

        # Auto-derive steps from React Flow nodes and edges
        nodes = workflow_spec.get("nodes") or []
        edges = workflow_spec.get("edges") or []

        derived_steps = []
        for n in nodes:
            nid = n.get("id") or n.get("step_id")
            n_data = n.get("data") or {}
            provider = n_data.get("provider") or n.get("provider") or "Generic"
            operation_id = n_data.get("operation_id") or n.get("operation_id") or "generic.http.request"
            params = n_data.get("parameters") or n.get("parameters") or {}
            retry_cfg = n.get("retry") or n_data.get("retry") or (params.get("retry") if isinstance(params, dict) else None)

            deps = [e.get("source") for e in edges if e.get("target") == nid] or n.get("dependencies") or n.get("depends_on") or []

            derived_steps.append({
                "step_id": nid,
                "id": nid,
                "provider": provider,
                "operation_id": operation_id,
                "parameters": params,
                "dependencies": deps,
                "retry": retry_cfg,
            })

        return derived_steps

    def _get_node_retry_config(self, node: Dict[str, Any], workflow_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts retry policy settings (enabled, max_attempts, delay_seconds)."""
        n_retry = node.get("retry")
        if not isinstance(n_retry, dict):
            params = node.get("parameters") or (node.get("data", {}).get("parameters") if isinstance(node.get("data"), dict) else {}) or {}
            n_retry = params.get("retry")

        if not isinstance(n_retry, dict) and isinstance(workflow_spec, dict):
            nodes = workflow_spec.get("nodes") or []
            nid = node.get("step_id") or node.get("id")
            orig_n = next((n for n in nodes if (n.get("id") or n.get("step_id")) == nid), None)
            if orig_n and isinstance(orig_n, dict):
                n_retry = orig_n.get("retry") or (orig_n.get("data", {}).get("retry") if isinstance(orig_n.get("data"), dict) else None)

        if not isinstance(n_retry, dict) and isinstance(workflow_spec, dict):
            n_retry = workflow_spec.get("retry")

        if isinstance(n_retry, dict):
            enabled = bool(n_retry.get("enabled", False))
            max_attempts = int(n_retry.get("max_attempts", 1))
            delay_seconds = float(n_retry.get("delay_seconds", 0.0))
            return {
                "enabled": enabled,
                "max_attempts": max(1, max_attempts),
                "delay_seconds": max(0.0, delay_seconds),
            }
        return {
            "enabled": False,
            "max_attempts": 1,
            "delay_seconds": 0.0,
        }

    async def execute_workflow(
        self, workflow_spec: Dict[str, Any], initial_context: Optional[Dict[str, Any]] = None, resume_execution_id: Optional[str] = None
    ) -> WorkflowExecutionStateV2:
        if resume_execution_id:
            restored = await self.checkpoint_manager.restore(resume_execution_id)
            restored_state = await self.history_store.get_state(resume_execution_id)
            if restored:
                execution_id = restored.execution_id
                tenant_id = (restored_state.tenant_id if restored_state and restored_state.tenant_id else None) or restored.tenant_id or workflow_spec.get("tenant_id", "usr_1")
                completed_node_ids = set(restored.completed_nodes)
                if not workflow_spec and restored.metadata.get("workflow_spec"):
                    workflow_spec = restored.metadata["workflow_spec"]
                ctx_vars = dict(restored.variables or {})
                if initial_context:
                    ctx_vars.update(initial_context)
                context = ExecutionContext(
                    execution_id=execution_id,
                    workflow_id=restored.workflow_id,
                    tenant_id=restored.tenant_id,
                    context_data=ctx_vars,
                    previous_outputs=dict(restored.outputs),
                )
                state = restored_state or WorkflowExecutionStateV2(
                    execution_id=execution_id,
                    workflow_id=restored.workflow_id,
                    tenant_id=restored.tenant_id,
                    status="RUNNING",
                    context_data=restored.variables,
                )
                state.status = "RUNNING"
                if restored_state and restored_state.node_records:
                    for nid, rec in restored_state.node_records.items():
                        if rec.get("status") in ["COMPLETED", "SUCCESS", "SKIPPED"]:
                            completed_node_ids.add(nid)
                        state.node_records[nid] = rec
                logger.info(f"Resuming Durable Workflow Execution [{execution_id}] from node checkpoint ({len(completed_node_ids)} completed).")
            else:
                resume_execution_id = None

        if not resume_execution_id:
            execution_id = f"exec_v3_{uuid.uuid4().hex[:10]}"
            workflow_id = workflow_spec.get("workflow_id", "wf_v3_default")
            tenant_id = workflow_spec.get("tenant_id", "usr_1")

            completed_node_ids = set()
            context = ExecutionContext(
                execution_id=execution_id,
                workflow_id=workflow_id,
                tenant_id=tenant_id,
                context_data=dict(initial_context or {}),
            )

            trig_type = (initial_context or {}).get("_trigger_type") or workflow_spec.get("trigger_type") or "manual"
            state = WorkflowExecutionStateV2(
                execution_id=execution_id,
                workflow_id=workflow_id,
                tenant_id=tenant_id,
                version_id=workflow_spec.get("version_id"),
                version_number=workflow_spec.get("version_number"),
                trigger_type=str(trig_type).lower(),
                status="RUNNING",
                context_data={k: v for k, v in context.context_data.items() if k != "_mock_dispatch_fn"},
            )

        steps = self._normalize_steps(workflow_spec)
        workflow_spec["steps"] = steps
        self.resolver.validate_dag(steps)
        self._control_signals[execution_id] = "RUNNING"

        # ── Preflight Connection Safety Guard ─────────────────────────────────
        from app.services.connection_readiness import check_workflow_readiness, is_internal_provider
        req_providers = set()
        for step in steps:
            prov = str(step.get("provider") or "").strip()
            if prov and not is_internal_provider(prov):
                req_providers.add(prov)

        if req_providers:
            readiness = await check_workflow_readiness(list(req_providers), user_id=tenant_id)
            if not readiness["ready"]:
                missing_str = ", ".join(readiness["missing_connections"])
                logger.warning(f"[PREFLIGHT_BLOCKED] Execution [{execution_id}] blocked due to missing connection(s): {missing_str}")
                state.status = "BLOCKED_MISSING_CONNECTION"
                state.end_time = time.time()
                await self.history_store.save_state(state)
                return state

        logger.info(f"[AI-16][WORKFLOW_EXECUTE_START] {json.dumps({'execution_id': execution_id, 'workflow_id': state.workflow_id, 'node_id': 'ALL', 'operation': 'workflow.execute', 'status': 'STARTED'})}")
        logger.info(f"[AI-16][DAG_RECEIVED] {json.dumps({'execution_id': execution_id, 'workflow_id': state.workflow_id, 'node_id': 'ALL', 'operation': 'dag.validate', 'status': 'VALIDATED', 'node_count': len(steps)})}")

        # Publish WorkflowStarted event
        await self.event_bus.publish(
            RuntimeEvent(
                event_type=RuntimeEventType.WORKFLOW_STARTED,
                execution_id=execution_id,
                workflow_id=state.workflow_id,
                data={"steps_count": len(steps)},
            )
        )

        while len(completed_node_ids) < len(steps):
            signal = self._control_signals.get(execution_id, "RUNNING")
            if signal == "CANCELLED":
                state.status = "CANCELLED"
                state.end_time = time.time()
                await self.event_bus.publish(
                    RuntimeEvent(
                        event_type=RuntimeEventType.WORKFLOW_CANCELLED,
                        execution_id=execution_id,
                        workflow_id=state.workflow_id,
                    )
                )
                await self.history_store.save_state(state)
                raise WorkflowCancelledException(f"Workflow [{execution_id}] cancelled.")

            if signal == "PAUSED":
                state.status = "PAUSED"
                await self.event_bus.publish(
                    RuntimeEvent(
                        event_type=RuntimeEventType.WORKFLOW_PAUSED,
                        execution_id=execution_id,
                        workflow_id=state.workflow_id,
                    )
                )
                await self.history_store.save_state(state)
                return state

            ready_nodes = self.resolver.get_ready_nodes(steps, completed_node_ids)
            if not ready_nodes:
                break

            for node in ready_nodes:
                n_id = node.get("step_id") or node.get("id")
                op_id = node.get("operation_id") or node.get("operation") or "generic.http.request"
                provider = (node.get("provider") or "").lower()

                logger.info(f"[AI-16][NODE_DEPENDENCY] {json.dumps({'execution_id': execution_id, 'workflow_id': state.workflow_id, 'node_id': n_id, 'operation': op_id, 'status': 'DEPENDENCIES_SATISFIED', 'dependencies': node.get('dependencies', [])})}")
                logger.info(f"[AI-16][NODE_SCHEDULED] {json.dumps({'execution_id': execution_id, 'workflow_id': state.workflow_id, 'node_id': n_id, 'operation': op_id, 'status': 'SCHEDULED'})}")

                # Handle Wait / Delay Node
                if provider == "wait" or provider == "delay":
                    logger.info(f"[AI-16][NODE_EXECUTE] {json.dumps({'execution_id': execution_id, 'workflow_id': state.workflow_id, 'node_id': n_id, 'operation': op_id, 'status': 'EXECUTING'})}")
                    await self.event_bus.publish(
                        RuntimeEvent(
                            event_type=RuntimeEventType.NODE_STARTED,
                            execution_id=execution_id,
                            workflow_id=state.workflow_id,
                            node_id=n_id,
                        )
                    )
                    wait_res = await self.wait_handler.process_wait_node(node.get("parameters") or {})
                    completed_node_ids.add(n_id)
                    context.record_step_output(n_id, wait_res)
                    state.node_records[n_id] = {
                        "status": "COMPLETED",
                        "output": wait_res,
                        "latency": 10.0,
                        "retries": 0,
                    }
                    logger.info(f"[AI-16][NODE_SUCCESS] {json.dumps({'execution_id': execution_id, 'workflow_id': state.workflow_id, 'node_id': n_id, 'operation': op_id, 'status': 'SUCCESS'})}")
                    logger.info(f"[AI-16][NODE_OUTPUT] {json.dumps({'execution_id': execution_id, 'workflow_id': state.workflow_id, 'node_id': n_id, 'operation': op_id, 'status': 'OUTPUT_RECORDED'})}")
                    await self.event_bus.publish(
                        RuntimeEvent(
                            event_type=RuntimeEventType.NODE_COMPLETED,
                            execution_id=execution_id,
                            workflow_id=state.workflow_id,
                            node_id=n_id,
                            data=wait_res,
                        )
                    )
                    continue

                # Handle Loop / Iterator Node
                if provider in ("loop", "iterator") or op_id in ("loop.forEach", "loop.iterator", "loop.process"):
                    logger.info(f"[AI-24][NODE_EXECUTE] {json.dumps({'execution_id': execution_id, 'workflow_id': state.workflow_id, 'node_id': n_id, 'operation': op_id, 'status': 'EXECUTING'})}")
                    await self.event_bus.publish(
                        RuntimeEvent(
                            event_type=RuntimeEventType.NODE_STARTED,
                            execution_id=execution_id,
                            workflow_id=state.workflow_id,
                            node_id=n_id,
                        )
                    )

                    params = node.get("parameters") or (node.get("data", {}).get("parameters") if isinstance(node.get("data"), dict) else {}) or {}
                    items_raw = params.get("items") or params.get("input_array") or params.get("array")
                    item_var = params.get("item_variable") or "item"
                    index_var = params.get("index_variable") or "index"

                    resolved_items = None
                    if isinstance(items_raw, list):
                        resolved_items = items_raw
                    elif isinstance(items_raw, str) and "{{" in items_raw:
                        try:
                            resolved_val = context.build_node_input_payload(n_id, {"_val": items_raw}, workflow_spec).get("_val")
                            if isinstance(resolved_val, list):
                                resolved_items = resolved_val
                        except Exception:
                            pass

                    if resolved_items is None:
                        step1_out = {}
                        for k, v in context.previous_outputs.items():
                            if isinstance(v, dict) and v:
                                step1_out = v
                                break
                        if not step1_out:
                            step1_out = state.node_records.get("step_1", {}).get("output") or {}
                        resolved_items = _extract_messages_from_output(step1_out)

                    if not isinstance(resolved_items, list):
                        if resolved_items is not None and resolved_items != "":
                            resolved_items = [resolved_items]
                        else:
                            resolved_items = []

                    total_items = len(resolved_items)
                    logger.info(f"[AI-24][LOOP_START] node_id={n_id} total_items={total_items} item_var={item_var}")

                    n_step_num = None
                    try:
                        n_step_num = int(str(n_id).replace("step_", ""))
                    except Exception:
                        pass

                    body_nodes = []
                    for s in steps:
                        s_id = s.get("step_id") or s.get("id")
                        if s_id == n_id or s_id in completed_node_ids:
                            continue
                        deps = s.get("dependencies") or s.get("depends_on") or []
                        if isinstance(deps, list) and (n_id in deps or (n_step_num is not None and n_step_num in deps)):
                            body_nodes.append(s)

                    iterations = []
                    completed_items = 0
                    failed_items = 0

                    if total_items == 0:
                        logger.info(f"[AI-24][LOOP_EMPTY] node_id={n_id} items=[] status=COMPLETED")
                        loop_output = {
                            "status": "COMPLETED",
                            "total_items": 0,
                            "completed_items": 0,
                            "failed_items": 0,
                            "iterations": [],
                            "outputs": [],
                        }
                        completed_node_ids.add(n_id)
                        for b_step in body_nodes:
                            b_id = b_step.get("step_id") or b_step.get("id")
                            completed_node_ids.add(b_id)
                            state.node_records[b_id] = {
                                "status": "COMPLETED",
                                "output": {"iterations": [], "outputs": [], "total_items": 0},
                                "latency": 0.0,
                                "retries": 0,
                            }
                    else:
                        for idx, curr_item in enumerate(resolved_items):
                            logger.info(f"[AI-24][LOOP_ITERATION] node_id={n_id} index={idx}")
                            context.context_data[item_var] = curr_item
                            context.context_data[index_var] = idx

                            iter_output = None
                            iter_status = "COMPLETED"
                            iter_error = None

                            if body_nodes:
                                for b_step in body_nodes:
                                    b_id = b_step.get("step_id") or b_step.get("id")
                                    b_params = b_step.get("parameters") or {}

                                    node_inp = context.build_node_input_payload(b_id, b_params, workflow_spec)
                                    try:
                                        mock_fn = (context.context_data or {}).get("_mock_dispatch_fn")
                                        if callable(mock_fn):
                                            res_or_coro = mock_fn(b_id, 1, node_inp)
                                            if inspect.isawaitable(res_or_coro):
                                                res_item = await res_or_coro
                                            else:
                                                res_item = res_or_coro
                                            node_res_list = [res_item] if res_item is not None else await self.scheduler.dispatch_ready_nodes([node_inp])
                                        else:
                                            node_res_list = await self.scheduler.dispatch_ready_nodes([node_inp])
                                        res_item = node_res_list[0] if node_res_list else {"status": "FAILED", "output": {"error": "No response"}}
                                        if res_item.get("status") in ["COMPLETED", "SUCCESS"]:
                                            iter_output = res_item.get("output", {})
                                            context.record_step_output(b_id, iter_output)
                                        else:
                                            iter_status = "FAILED"
                                            iter_error = str(res_item.get("output", {}).get("error") or "Body execution failed")
                                    except Exception as exc:
                                        iter_status = "FAILED"
                                        iter_error = str(exc)
                            else:
                                iter_output = {"item": curr_item, "index": idx}

                            if iter_status == "COMPLETED":
                                completed_items += 1
                            else:
                                failed_items += 1

                            iter_rec = {
                                "index": idx,
                                "item": curr_item,
                                "status": iter_status,
                                "output": iter_output,
                            }
                            if iter_error:
                                iter_rec["error"] = iter_error
                            iterations.append(iter_rec)

                        completed_node_ids.add(n_id)
                        for b_step in body_nodes:
                            b_id = b_step.get("step_id") or b_step.get("id")
                            completed_node_ids.add(b_id)
                            b_out = {
                                "total_items": total_items,
                                "completed_items": completed_items,
                                "failed_items": failed_items,
                                "iterations": iterations,
                                "outputs": [it.get("output") for it in iterations if it.get("output") is not None],
                            }
                            first_output = next((it.get("output") for it in iterations if isinstance(it.get("output"), dict)), {})
                            for fk, fv in first_output.items():
                                if fk not in b_out:
                                    b_out[fk] = fv

                            state.node_records[b_id] = {
                                "status": "COMPLETED",
                                "output": b_out,
                                "latency": 10.0,
                                "retries": 0,
                            }
                            context.record_step_output(b_id, b_out)

                        loop_output = {
                            "status": "COMPLETED" if failed_items == 0 or completed_items > 0 else "FAILED",
                            "total_items": total_items,
                            "completed_items": completed_items,
                            "failed_items": failed_items,
                            "iterations": iterations,
                            "outputs": [it.get("output") for it in iterations if it.get("output") is not None],
                        }

                        context.context_data.pop(item_var, None)
                        context.context_data.pop(index_var, None)

                    context.record_step_output(n_id, loop_output)
                    state.node_records[n_id] = {
                        "status": loop_output["status"],
                        "output": loop_output,
                        "latency": 15.0,
                        "retries": 0,
                    }
                    logger.info(f"[AI-24][NODE_SUCCESS] {json.dumps({'execution_id': execution_id, 'workflow_id': state.workflow_id, 'node_id': n_id, 'operation': op_id, 'status': 'SUCCESS'})}")
                    await self.event_bus.publish(
                        RuntimeEvent(
                            event_type=RuntimeEventType.NODE_COMPLETED,
                            execution_id=execution_id,
                            workflow_id=state.workflow_id,
                            node_id=n_id,
                            data=loop_output,
                        )
                    )
                    continue

                # Handle Human Approval Node
                if provider == "approval" or provider == "human_approval":
                    logger.info(f"[AI-16][NODE_EXECUTE] {json.dumps({'execution_id': execution_id, 'workflow_id': state.workflow_id, 'node_id': n_id, 'operation': op_id, 'status': 'WAITING_APPROVAL'})}")
                    app_req = await self.approval_engine.get_approval(execution_id, n_id)
                    if not app_req:
                        await self.approval_engine.create_approval_request(execution_id, n_id)
                        state.status = "WAITING"
                        await self.event_bus.publish(
                            RuntimeEvent(
                                event_type=RuntimeEventType.WORKFLOW_PAUSED,
                                execution_id=execution_id,
                                workflow_id=state.workflow_id,
                                node_id=n_id,
                                data={"reason": "Human approval required"},
                            )
                        )
                        await self.checkpoint_manager.save_checkpoint(
                            execution_id=execution_id,
                            workflow_id=state.workflow_id,
                            state=WorkflowLifecycleState.WAITING,
                            variables=context.context_data,
                            completed_nodes=completed_node_ids,
                            pending_nodes=[s.get("step_id") or s.get("id") for s in steps if (s.get("step_id") or s.get("id")) not in completed_node_ids],
                            outputs=context.previous_outputs,
                            retries={},
                            metadata={"workflow_spec": workflow_spec},
                        )
                        await self.history_store.save_state(state)
                        return state

                    if app_req.status == "PENDING":
                        state.status = "WAITING"
                        await self.history_store.save_state(state)
                        return state

                    if app_req.status == "REJECTED":
                        state.status = "FAILED"
                        await self.event_bus.publish(
                            RuntimeEvent(
                                event_type=RuntimeEventType.NODE_FAILED,
                                execution_id=execution_id,
                                workflow_id=state.workflow_id,
                                node_id=n_id,
                                data={"error": "Human approval rejected"},
                            )
                        )
                        await self.dlq.push_failed_execution(execution_id, workflow_spec, n_id, "Human approval rejected")
                        return state

                    completed_node_ids.add(n_id)
                    context.record_step_output(n_id, {"status": "APPROVED", "approver": app_req.approver})
                    state.node_records[n_id] = {"status": "COMPLETED", "output": {"status": "APPROVED"}, "latency": 5.0, "retries": 0}
                    continue

                # Dispatch Standard DAG Node
                if op_id in ["gmail.messages.search", "gmail.messages.list"]:
                    params = node.get("parameters") or {}
                    q_val = params.get("q")
                    logger.info(f"[AI-17][SEARCH_QUERY] {json.dumps({'execution_id': execution_id, 'workflow_id': state.workflow_id, 'node_id': n_id, 'operation': op_id, 'q': q_val})}")
                    logger.info(f"[AI-17.1][EXECUTION_QUERY] step={n_id} op={op_id} q='{q_val}'")

                logger.info(f"[AI-16][NODE_EXECUTE] {json.dumps({'execution_id': execution_id, 'workflow_id': state.workflow_id, 'node_id': n_id, 'operation': op_id, 'status': 'EXECUTING'})}")
                await self.event_bus.publish(
                    RuntimeEvent(
                        event_type=RuntimeEventType.NODE_STARTED,
                        execution_id=execution_id,
                        workflow_id=state.workflow_id,
                        node_id=n_id,
                    )
                )

                # -------------------------------------------------------------
                # Sprint AI-19: Generic Array Fan-Out / Iteration Mechanism
                # -------------------------------------------------------------
                params = node.get("parameters") or (node.get("data", {}).get("parameters") if isinstance(node.get("data"), dict) else {}) or {}
                msg_id_param = str(params.get("message_id") or params.get("id") or "")
                
                # Retrieve previous step output dynamically
                step1_out = {}
                for k, v in context.previous_outputs.items():
                    if isinstance(v, dict) and v:
                        step1_out = v
                        break
                if not step1_out:
                    step1_out = state.node_records.get("step_1", {}).get("output") or {}
                
                def _extract_messages_from_output(out_obj):
                    if not isinstance(out_obj, dict):
                        return []
                    msgs = out_obj.get("messages")
                    if isinstance(msgs, list):
                        return msgs
                    items = out_obj.get("items")
                    if isinstance(items, list):
                        return items
                    for sub_key in ["body", "output", "response", "data"]:
                        sub_val = out_obj.get(sub_key)
                        if isinstance(sub_val, dict):
                            found = _extract_messages_from_output(sub_val)
                            if found:
                                return found
                    return []

                step1_msgs = _extract_messages_from_output(step1_out)

                is_fanout = "[*]" in msg_id_param or (
                    op_id in ["gmail.messages.get", "gmail.get"] and 
                    isinstance(step1_msgs, list) and 
                    len(step1_msgs) > 0 and
                    "[0]" not in msg_id_param
                )

                if is_fanout:
                    item_ids = []
                    if isinstance(step1_msgs, list):
                        for item in step1_msgs:
                            val = None
                            if isinstance(item, dict):
                                val = item.get("id") or item.get("message_id")
                            elif isinstance(item, str):
                                val = item
                            if val:
                                s_val = str(val).strip()
                                if s_val and not s_val.startswith("{{") and s_val not in ["null", "undefined", "None", "—"]:
                                    item_ids.append(s_val)

                    search_node = next(
                        (n for n in workflow_spec.get("nodes", []) 
                         if n.get("operation_id") in ["gmail.messages.list", "gmail.messages.search", "gmail.list", "gmail.search"]
                         or n.get("operation") in ["gmail.messages.list", "gmail.messages.search", "gmail.list", "gmail.search"]
                         or (isinstance(n.get("data"), dict) and n.get("data", {}).get("operation_id") in ["gmail.messages.list", "gmail.messages.search"])),
                        {}
                    )
                    configured_max = None
                    if isinstance(step1_out, dict):
                        configured_max = step1_out.get("max_results") or step1_out.get("request", {}).get("payload", {}).get("max_results")
                    
                    if configured_max is None:
                        search_params = search_node.get("parameters") or (search_node.get("data", {}) if isinstance(search_node.get("data"), dict) else {}).get("parameters", {})
                        configured_max = search_params.get("max_results")

                    try:
                        raw_max = int(configured_max) if configured_max is not None else 10
                        if raw_max > 50:
                            logger.warning(f"[AI-19.3][SAFE_MAXIMUM] original={raw_max} clamped=50")
                        effective_max = max(1, min(50, raw_max))
                    except (ValueError, TypeError):
                        effective_max = 10

                    logger.info(f"[AI-19.3][MAX_RESULTS_CONFIGURED] node={search_node.get('id', 'step_1')} max_results={effective_max}")
                    logger.info(f"[AI-20.1][GMAIL_MAX_RESULTS] operation={op_id} max_results={effective_max}")
                    item_ids = item_ids[:effective_max]
                    total_count = len(item_ids)

                    logger.info(f"[AI-20.1][RESULT_LIMIT] requested={effective_max} returned={total_count}")

                    if total_count == 0:
                        logger.info(f"[AI-19.1][SEARCH_EMPTY] {{\"operation\": \"{op_id}\", \"result_count\": 0}}")
                        logger.info(f"[AI-19.1][FANOUT_SKIP] {{\"reason\": \"empty_array\", \"child_count\": 0}}")
                    else:
                        logger.info(f"[AI-19][FANOUT_START] source=step_1.messages count={total_count} max_results={effective_max}")

                    item_results = []
                    item_bodies = []
                    success_count = 0
                    failed_count = 0

                    for idx, item_id in enumerate(item_ids):
                        logger.info(f"[AI-19][FANOUT_ITEM] index={idx} message_id={item_id}")
                        logger.info(f"[AI-19][FANOUT_GET] index={idx} message_id={item_id}")

                        single_params = dict(params)
                        single_params["message_id"] = item_id

                        node_inp = context.build_node_input_payload(n_id, single_params, workflow_spec)
                        try:
                            node_res_list = await self.scheduler.dispatch_ready_nodes([node_inp])
                            res_item = node_res_list[0] if node_res_list else {"status": "FAILED", "output": {"error": "No response"}}
                            
                            if res_item.get("status") in ["COMPLETED", "SUCCESS"]:
                                success_count += 1
                                logger.info(f"[AI-19][FANOUT_SUCCESS] index={idx} message_id={item_id}")
                                out_data = res_item.get("output", {})
                                item_results.append(out_data)
                                body_data = out_data.get("body") if isinstance(out_data.get("body"), dict) else out_data
                                item_bodies.append(body_data)
                            else:
                                failed_count += 1
                                err_msg = str(res_item.get("output", {}).get("error") or "Retrieval failed")
                                logger.warning(f"[AI-19][FANOUT_FAILURE] index={idx} message_id={item_id} error={err_msg}")
                        except Exception as exc:
                            failed_count += 1
                            logger.error(f"[AI-19][FANOUT_FAILURE] index={idx} message_id={item_id} error={exc}")

                    if total_count > 0:
                        logger.info(f"[AI-19][FANOUT_COMPLETE] total={total_count} success={success_count} failed={failed_count}")

                    combined_output = {
                        "status": "COMPLETED",
                        "total_items": total_count,
                        "success_count": success_count,
                        "failed_count": failed_count,
                        "messages": item_bodies,
                        "items": item_results,
                        "message": "No matching emails found." if total_count == 0 else f"Loaded {success_count} emails.",
                        "body": {
                            "messages": item_bodies,
                            "items": item_results,
                            "total_items": total_count,
                            "success_count": success_count,
                            "failed_count": failed_count,
                            "message": "No matching emails found." if total_count == 0 else f"Loaded {success_count} emails.",
                        }
                    }

                    res = {
                        "node_id": n_id,
                        "status": "COMPLETED",
                        "output": combined_output,
                        "latency": 50.0,
                        "retries": 0,
                    }
                    state.node_records[n_id] = res
                    completed_node_ids.add(n_id)
                    context.record_step_output(n_id, combined_output)
                    state.context_data = context.context_data
                    continue

                retry_cfg = self._get_node_retry_config(node, workflow_spec)
                max_attempts = retry_cfg["max_attempts"] if retry_cfg["enabled"] else 1
                delay_sec = retry_cfg["delay_seconds"] if retry_cfg["enabled"] else 0.0

                attempts_history = []
                res = None

                for attempt in range(1, max_attempts + 1):
                    start_ts = time.time()
                    node_inp = context.build_node_input_payload(n_id, node.get("parameters") or {}, workflow_spec)

                    mock_fn = (context.context_data or {}).get("_mock_dispatch_fn")
                    if callable(mock_fn):
                        res_or_coro = mock_fn(n_id, attempt, node_inp)
                        if inspect.isawaitable(res_or_coro):
                            res_item = await res_or_coro
                        else:
                            res_item = res_or_coro
                        if res_item is not None:
                            node_res_list = [res_item]
                        else:
                            node_res_list = await self.scheduler.dispatch_ready_nodes([node_inp])
                    else:
                        node_res_list = await self.scheduler.dispatch_ready_nodes([node_inp])

                    raw_res = node_res_list[0] if node_res_list else {"status": "FAILED", "output": {"error": "No result"}}
                    latency_ms = round((time.time() - start_ts) * 1000, 2)
                    status_str = raw_res.get("status")
                    is_success = status_str in ["COMPLETED", "SUCCESS"]

                    err_out = raw_res.get("output", {}) if isinstance(raw_res.get("output"), dict) else {"error": str(raw_res.get("output"))}
                    classification = classify_error(err_out if not is_success else {})

                    attempt_record = sanitize_telemetry_secrets({
                        "attempt": attempt,
                        "max_attempts": max_attempts,
                        "status": "SUCCESS" if is_success else "FAILED",
                        "error_type": classification["error_type"] if not is_success else None,
                        "retryable": classification["retryable"] if not is_success else False,
                        "timestamp": time.time(),
                        "latency_ms": latency_ms,
                    })
                    attempts_history.append(attempt_record)

                    if is_success:
                        res = dict(raw_res)
                        res["status"] = "COMPLETED"
                        res["attempts"] = attempt
                        res["max_attempts"] = max_attempts
                        res["attempts_history"] = attempts_history
                        res["recovered_after_retry"] = (attempt > 1)
                        res["retries"] = attempt - 1
                        break
                    else:
                        if retry_cfg["enabled"] and classification["retryable"] and attempt < max_attempts:
                            logger.info(f"[AI-29][RETRY_ATTEMPT] node_id={n_id} attempt={attempt}/{max_attempts} error_type={classification['error_type']} delay={delay_sec}s")
                            if delay_sec > 0:
                                await asyncio.sleep(delay_sec)
                            continue
                        else:
                            res = dict(raw_res)
                            res["status"] = "FAILED"
                            res["attempts"] = attempt
                            res["max_attempts"] = max_attempts
                            res["attempts_history"] = attempts_history
                            res["retryable"] = classification["retryable"]
                            res["exhausted_retries"] = (attempt >= max_attempts and classification["retryable"])
                            res["retries"] = attempt - 1
                            break

                state.node_records[n_id] = res

                if res.get("status") in ["COMPLETED", "SUCCESS"]:
                    res["status"] = "COMPLETED"
                    completed_node_ids.add(n_id)
                    context.record_step_output(n_id, res["output"])
                    state.context_data = {k: v for k, v in context.context_data.items() if k != "_mock_dispatch_fn"}

                    # AI-23: Handle Conditional Branching (IF/ELSE)
                    if provider == "condition" or op_id == "condition.if" or op_id.startswith("condition."):
                        out_body = res.get("output", {}).get("body") if isinstance(res.get("output"), dict) and "body" in res.get("output") else res.get("output", {})
                        if isinstance(out_body, dict):
                            cond_result = out_body.get("result")
                            true_target = out_body.get("true_branch") or node.get("parameters", {}).get("true_branch") or node.get("parameters", {}).get("true_step_id")
                            false_target = out_body.get("false_branch") or node.get("parameters", {}).get("false_branch") or node.get("parameters", {}).get("false_step_id")

                            skipped_start_id = false_target if cond_result else true_target
                            if not skipped_start_id and not cond_result:
                                skipped_start_id = true_target

                            if skipped_start_id:
                                self._mark_skipped_branch(steps, skipped_start_id, completed_node_ids, state)
                    logger.info(f"[AI-16][NODE_SUCCESS] {json.dumps({'execution_id': execution_id, 'workflow_id': state.workflow_id, 'node_id': n_id, 'operation': op_id, 'status': 'SUCCESS'})}")
                    logger.info(f"[AI-16][NODE_OUTPUT] {json.dumps({'execution_id': execution_id, 'workflow_id': state.workflow_id, 'node_id': n_id, 'operation': op_id, 'status': 'OUTPUT_RECORDED'})}")
                    await self.event_bus.publish(
                        RuntimeEvent(
                            event_type=RuntimeEventType.NODE_COMPLETED,
                            execution_id=execution_id,
                            workflow_id=state.workflow_id,
                            node_id=n_id,
                            data=res["output"],
                        )
                    )
                else:
                    state.status = "FAILED"
                    state.end_time = time.time()
                    logger.error(f"[AI-16][NODE_FAILED] {json.dumps({'execution_id': execution_id, 'workflow_id': state.workflow_id, 'node_id': n_id, 'operation': op_id, 'status': 'FAILED'})}")
                    
                    # Mark remaining downstream nodes as SKIPPED
                    for remaining in steps:
                        rem_id = remaining.get("step_id") or remaining.get("id")
                        if rem_id not in completed_node_ids and rem_id != n_id:
                            state.node_records[rem_id] = {
                                "node_id": rem_id,
                                "status": "SKIPPED",
                                "output": {"error": "Dependency failed"},
                                "latency": 0.0,
                                "retries": 0,
                            }

                    await self.event_bus.publish(
                        RuntimeEvent(
                            event_type=RuntimeEventType.NODE_FAILED,
                            execution_id=execution_id,
                            workflow_id=state.workflow_id,
                            node_id=n_id,
                            data=res.get("output", {}),
                        )
                    )
                    await self.event_bus.publish(
                        RuntimeEvent(
                            event_type=RuntimeEventType.WORKFLOW_FAILED,
                            execution_id=execution_id,
                            workflow_id=state.workflow_id,
                        )
                    )
                    state.status = "FAILED"
                    state.end_time = time.time()
                    # Push failed run to Dead Letter Queue
                    await self.dlq.push_failed_execution(
                        execution_id, workflow_spec, n_id, str(res.get("output", {}).get("error", "Execution failed"))
                    )
                    await self.checkpoint_manager.save_checkpoint(
                        execution_id=execution_id,
                        workflow_id=state.workflow_id,
                        state=WorkflowLifecycleState.FAILED,
                        variables=context.context_data,
                        completed_nodes=completed_node_ids,
                        pending_nodes=[s.get("step_id") or s.get("id") for s in steps if (s.get("step_id") or s.get("id")) not in completed_node_ids],
                        outputs=context.previous_outputs,
                        retries={},
                        metadata={
                            "workflow_spec": workflow_spec,
                            "version_id": getattr(state, "version_id", None) or workflow_spec.get("version_id"),
                            "version_number": getattr(state, "version_number", None) or workflow_spec.get("version_number"),
                        },
                    )
                    await self.history_store.save_state(state)
                    logger.info(f"[AI-16][WORKFLOW_EXECUTE_COMPLETE] {json.dumps({'execution_id': execution_id, 'workflow_id': state.workflow_id, 'node_id': 'ALL', 'operation': 'workflow.complete', 'status': 'FAILED', 'nodes_executed': len(completed_node_ids)})}")
                    return state

            # Persist Durable Checkpoint after EVERY node batch
            await self.checkpoint_manager.save_checkpoint(
                execution_id=execution_id,
                workflow_id=state.workflow_id,
                state=WorkflowLifecycleState.RUNNING,
                variables=context.context_data,
                completed_nodes=completed_node_ids,
                pending_nodes=[s.get("step_id") or s.get("id") for s in steps if (s.get("step_id") or s.get("id")) not in completed_node_ids],
                outputs=context.previous_outputs,
                retries={},
                metadata={
                    "workflow_spec": workflow_spec,
                    "version_id": getattr(state, "version_id", None) or workflow_spec.get("version_id"),
                    "version_number": getattr(state, "version_number", None) or workflow_spec.get("version_number"),
                },
            )

        state.status = "COMPLETED"
        state.end_time = time.time()
        logger.info(f"[AI-16][WORKFLOW_EXECUTE_COMPLETE] {json.dumps({'execution_id': execution_id, 'workflow_id': state.workflow_id, 'node_id': 'ALL', 'operation': 'workflow.complete', 'status': 'COMPLETED', 'nodes_executed': len(completed_node_ids)})}")
        await self.event_bus.publish(
            RuntimeEvent(
                event_type=RuntimeEventType.WORKFLOW_COMPLETED,
                execution_id=execution_id,
                workflow_id=state.workflow_id,
            )
        )
        await self.history_store.save_state(state)
        return state

    def _mark_skipped_branch(self, steps: list, skipped_start_id: str, completed_node_ids: set, state: Any) -> None:
        if not skipped_start_id or skipped_start_id in completed_node_ids:
            return

        to_skip = {skipped_start_id}
        changed = True
        while changed:
            changed = False
            for s in steps:
                s_id = s.get("step_id") or s.get("id")
                if s_id in completed_node_ids or s_id in to_skip:
                    continue
                deps = s.get("dependencies") or []
                if any(d in to_skip for d in deps):
                    to_skip.add(s_id)
                    changed = True

        for s_id in to_skip:
            if s_id not in completed_node_ids:
                completed_node_ids.add(s_id)
                op_name = next((s.get("operation") or s.get("operation_id") for s in steps if (s.get("step_id") or s.get("id")) == s_id), "generic.http.request")
                state.node_records[s_id] = {
                    "node_id": s_id,
                    "operation": op_name,
                    "status": "SKIPPED",
                    "output": {"status": "SKIPPED", "reason": "Skipped due to condition evaluation"},
                    "latency": 0.0,
                    "latency_ms": 0.0,
                    "retries": 0,
                }
                logger.info(f"[AI-23][NODE_SKIPPED] node_id={s_id} status=SKIPPED")

    async def approve_node(self, execution_id: str, node_id: str, approver: str = "admin", initial_context: Optional[dict] = None) -> Optional[WorkflowExecutionStateV2]:
        success = await self.approval_engine.approve(execution_id, node_id, approver)
        if success:
            checkpoint = await self.checkpoint_manager.restore(execution_id)
            if checkpoint and checkpoint.metadata.get("workflow_spec"):
                return await self.execute_workflow(checkpoint.metadata.get("workflow_spec"), resume_execution_id=execution_id, initial_context=initial_context)
        return None

    async def replay_dlq(self, execution_id: str) -> Optional[WorkflowExecutionStateV2]:
        record = await self.dlq.replay(execution_id)
        if record:
            return await self.execute_workflow(record.workflow, resume_execution_id=execution_id)
        return None


workflow_runtime_executor_v3 = WorkflowRuntimeExecutorV3()
workflow_runtime_executor = workflow_runtime_executor_v3
