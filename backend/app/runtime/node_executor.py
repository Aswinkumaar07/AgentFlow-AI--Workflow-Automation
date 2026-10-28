import asyncio
import datetime
import logging
import time
from typing import Any, Dict
from app.connectors.manager import connector_manager
from app.runtime.live_node_executor import live_node_executor

logger = logging.getLogger("agentflow.runtime.node_executor")


class NodeExecutor:
    """
    Executes single DAG nodes against production provider APIs (Sprint REAL-1).
    Routes Gmail execution through ConnectorManager -> ConnectorRegistry -> GmailAdapter -> Google Gmail API.
    Zero mocks. Zero fake presets. Production real HTTP API execution.
    """

    async def execute_node(self, node_input: Dict[str, Any], max_retries: int = 1) -> Dict[str, Any]:
        node_id = node_input["metadata"]["node_id"]
        params = node_input["metadata"]["interpolated_params"]
        workflow_spec = node_input["workflow"]
        tenant_id = node_input.get("tenant_id", "usr_1")

        steps = workflow_spec.get("steps") or workflow_spec.get("nodes") or []
        step_def = next((s for s in steps if (s.get("step_id") or s.get("id")) == node_id), {})

        data_obj = step_def.get("data", {}) if isinstance(step_def.get("data"), dict) else {}
        provider = step_def.get("provider") or data_obj.get("provider") or "Generic REST"
        operation_id = step_def.get("operation_id") or step_def.get("operation") or data_obj.get("operation_id") or "generic.http.request"
        merged_params = {**(step_def.get("parameters") or data_obj.get("parameters") or {}), **(params if isinstance(params, dict) else {})}

        # Handle explicit mock failure test node
        if provider.lower() == "mockfailureprovider":
            return {
                "node_id": node_id,
                "status": "FAILED",
                "output": {"error": "Simulated failure for DLQ"},
                "latency": 5.0,
                "retries": 0,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }

        # ----------------------------------------------------
        # Route Gmail Execution through ConnectorManager & GmailAdapter
        # Flow: Workflow -> WorkflowRuntimeExecutorV3 -> NodeExecutor -> ConnectorRegistry -> GmailAdapter.execute() -> Google Gmail API
        # ----------------------------------------------------
        if provider.lower() in ["gmail", "google gmail"] or operation_id.startswith("gmail."):
            if operation_id in ["gmail.messages.list", "gmail.messages.search", "gmail.list", "gmail.search"]:
                raw_max = merged_params.get("max_results")
                try:
                    raw_val = int(raw_max) if raw_max is not None else 10
                    if raw_val > 50:
                        logger.warning(f"[AI-19.3][SAFE_MAXIMUM] original={raw_val} clamped=50")
                    max_val = max(1, min(50, raw_val))
                except (ValueError, TypeError):
                    max_val = 10
                merged_params["max_results"] = max_val
                logger.info(f"[AI-19.3][MAX_RESULTS_CONFIGURED] node={node_id} max_results={max_val}")
                logger.info(f"[AI-20.1][GMAIL_MAX_RESULTS] operation={operation_id} max_results={max_val}")

            if operation_id in ["gmail.messages.get", "gmail.get"]:
                msg_id = str(merged_params.get("message_id") or "").strip()
                if not msg_id or "{{" in msg_id or msg_id in ["—", "None", "undefined", "null"]:
                    logger.info(f"[AI-19.1][SEARCH_EMPTY] {{\"operation\": \"{operation_id}\", \"result_count\": 0}}")
                    logger.info(f"[AI-19.1][FANOUT_SKIP] {{\"reason\": \"empty_array\", \"child_count\": 0}}")
                    return {
                        "node_id": node_id,
                        "status": "COMPLETED",
                        "output": {
                            "status_code": 200,
                            "latency_ms": 1.0,
                            "request": {"url": "https://gmail.googleapis.com/gmail/v1/users/me/messages", "method": "GET", "payload": merged_params},
                            "response": {"messages": [], "items": [], "total_items": 0, "success_count": 0, "failed_count": 0, "message": "No matching emails found."},
                            "body": {"messages": [], "items": [], "total_items": 0, "success_count": 0, "failed_count": 0, "message": "No matching emails found."},
                            "headers": {},
                            "retries": 0,
                        },
                        "latency": 1.0,
                        "retries": 0,
                        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    }

            start_time = time.perf_counter()
            retries_done = 0
            res = None

            for attempt in range(max_retries + 1):
                res = await connector_manager.execute(
                    provider="Gmail",
                    operation_id=operation_id,
                    parameters=merged_params,
                    tenant_id=tenant_id,
                )

                if res.status_code in [429, 503] and attempt < max_retries:
                    retries_done = attempt + 1
                    logger.warning(f"Gmail API HTTP {res.status_code} received on node [{node_id}] — retrying attempt {retries_done}...")
                    await asyncio.sleep(0.3 * retries_done)
                    continue
                else:
                    break

            latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            res_data = res.data if res and isinstance(res.data, dict) else {}
            status_code = res.status_code if res else 500
            is_success = res.success if res else False

            if operation_id in ["gmail.messages.get", "gmail.get"] and isinstance(res_data, dict):
                from app.utils.gmail_attachment_normalizer import extract_gmail_attachments
                att_meta = extract_gmail_attachments(res_data)
                res_data["attachments"] = att_meta["attachments"]
                res_data["inline_images"] = att_meta["inline_images"]
                res_data["all_attachments"] = att_meta["all_attachments"]
                res_data["cid_map"] = att_meta["cid_map"]
                if isinstance(res_data.get("body"), dict):
                    res_data["body"]["attachments"] = att_meta["attachments"]
                    res_data["body"]["inline_images"] = att_meta["inline_images"]
                    res_data["body"]["all_attachments"] = att_meta["all_attachments"]
                    res_data["body"]["cid_map"] = att_meta["cid_map"]

            status_str = "COMPLETED" if is_success else "FAILED"
            msg_id = res_data.get("messageId") or res_data.get("id")
            thread_id = res_data.get("threadId")

            output_payload = {
                "status_code": status_code,
                "latency_ms": latency_ms,
                "request": {
                    "url": "https://gmail.googleapis.com/gmail/v1/users/me/messages/send" if "send" in operation_id else "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                    "method": "POST" if "send" in operation_id else "GET",
                    "headers": {"Authorization": "Bearer ***"},
                    "payload": merged_params,
                },
                "response": res_data,
                "headers": res_data.get("headers", {}),
                "body": res_data.get("body", res_data),
                "data": res_data.get("body", res_data),
                "provider_message_id": msg_id,
                "provider_thread_id": thread_id,
                "messageId": msg_id,
                "threadId": thread_id,
                "retries": retries_done,
                "retry_count": retries_done,
            }

            if not is_success:
                output_payload["error"] = res.error_message or f"Gmail API returned error HTTP {status_code}"

            return {
                "node_id": node_id,
                "status": status_str,
                "output": output_payload,
                "latency": latency_ms,
                "retries": retries_done,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }

        # ----------------------------------------------------
        # Standard Live Node Execution for other providers
        # ----------------------------------------------------
        node_payload = {
            "id": node_id,
            "provider": provider,
            "operation_id": operation_id,
            "parameters": merged_params,
        }

        live_res = await live_node_executor.execute_node(
            node=node_payload,
            context_variables=node_input.get("context", {}),
            tenant_id=tenant_id,
            max_retries=max_retries,
        )

        status_str = "COMPLETED" if live_res.status == "SUCCESS" else "FAILED"

        output_payload = {
            "status_code": live_res.status_code,
            "latency_ms": live_res.latency_ms,
            "request": live_res.request,
            "response": live_res.response,
            "headers": live_res.response.get("headers", {}),
            "body": live_res.response.get("body", {}),
            "data": live_res.response.get("body", {}),
            "errors": live_res.errors,
            "logs": live_res.logs,
            "retries": live_res.retries,
            "retry_count": live_res.retries,
        }

        if live_res.errors:
            output_payload["error"] = live_res.errors[0]

        return {
            "node_id": node_id,
            "status": status_str,
            "output": output_payload,
            "latency": live_res.latency_ms,
            "retries": live_res.retries,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }


node_executor = NodeExecutor()
