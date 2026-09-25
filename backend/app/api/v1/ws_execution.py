"""
WebSocket endpoint for real-time execution event streaming.
Endpoint: GET /ws/execution/{execution_id}

Message format (server → client):
  { "type": "node_event",    "node_id": str, "status": str,
    "latency_ms": float,     "log_message": str, "variables": dict }
  { "type": "execution_status", "status": str, "execution_id": str }
  { "type": "heartbeat",     "ts": float }
  { "type": "completed",     "execution_id": str, "duration_ms": float }
"""
import asyncio
import json
import logging
import time
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/ws", tags=["WebSocket Execution Stream"])
logger = logging.getLogger("agentflow.api.ws_execution")

# Active connections: execution_id -> set of WebSocket connections
_connections: Dict[str, Set[WebSocket]] = {}


async def _broadcast(execution_id: str, message: dict) -> None:
    """Broadcast a JSON message to all clients watching an execution."""
    dead = set()
    for ws in list(_connections.get(execution_id, set())):
        try:
            await ws.send_text(json.dumps(message))
        except Exception:
            dead.add(ws)
    # Cleanup dead connections
    if dead:
        _connections.setdefault(execution_id, set()).difference_update(dead)


async def _simulate_execution(execution_id: str, node_ids: list) -> None:
    """
    Drives a simulated step-by-step execution for demo / backend-not-connected mode.
    Each node transitions: PENDING → RUNNING (1–2s) → COMPLETED/FAILED.
    """
    total = len(node_ids)
    started_at = time.time()

    await _broadcast(execution_id, {
        "type": "execution_status",
        "execution_id": execution_id,
        "status": "RUNNING",
        "total_steps": total,
    })

    for idx, node_id in enumerate(node_ids):
        # Check if execution was cancelled
        from app.api.v1.runtime import _execution_signals
        signal = _execution_signals.get(execution_id, "RUNNING")

        if signal == "CANCELLED":
            await _broadcast(execution_id, {
                "type": "node_event", "node_id": node_id, "status": "CANCELLED",
                "latency_ms": 0, "log_message": f"Step [{node_id}] cancelled by operator.",
                "variables": {},
            })
            continue

        # Wait while paused
        pause_wait = 0
        while _execution_signals.get(execution_id) == "PAUSED" and pause_wait < 60:
            await asyncio.sleep(1)
            pause_wait += 1

        # RUNNING
        await _broadcast(execution_id, {
            "type": "node_event", "node_id": node_id, "status": "RUNNING",
            "latency_ms": 0, "log_message": f"[{node_id}] Executing step {idx + 1}/{total}…",
            "variables": {},
        })

        run_time = 0.8 + (idx % 3) * 0.4   # 0.8–1.6s per step
        await asyncio.sleep(run_time)
        latency_ms = round(run_time * 1000, 1)

        # Simulate occasional failure on 2nd-to-last step if > 3 nodes
        is_fail = (total > 3 and idx == total - 2 and idx > 0)
        status = "FAILED" if is_fail else "COMPLETED"
        variables = {f"output_{node_id}": f"result_{idx}", "step_index": idx}

        await _broadcast(execution_id, {
            "type": "node_event", "node_id": node_id, "status": status,
            "latency_ms": latency_ms,
            "log_message": (
                f"[{node_id}] {'✓ Completed' if status == 'COMPLETED' else '✗ Failed'} in {latency_ms}ms."
            ),
            "variables": variables,
            "request_payload": {"step_id": node_id, "index": idx},
            "response_data": {"status": status.lower(), "data": f"output_{idx}"},
            "error_message": f"Simulated error at step {idx + 1}" if is_fail else None,
        })

    # Final status
    duration_ms = round((time.time() - started_at) * 1000, 1)
    final_status = "FAILED" if any(
        True for node_id in node_ids
        if _execution_signals.get(execution_id) == "CANCELLED"
    ) else "COMPLETED"

    # Record telemetry into analytics engine
    from app.analytics.engine import analytics_engine
    step_telemetry = [
        {"id": nid, "step_id": nid, "provider": "Generic REST API", "status": "COMPLETED", "latency_ms": 25.0}
        for nid in node_ids
    ]
    analytics_engine.record_execution(
        execution_id=execution_id,
        workflow_name="Interactive DAG Run",
        status=final_status,
        duration_ms=duration_ms,
        steps=step_telemetry,
    )

    await _broadcast(execution_id, {
        "type": "completed",
        "execution_id": execution_id,
        "status": final_status,
        "duration_ms": duration_ms,
    })


@router.websocket("/execution/{execution_id}")
async def execution_websocket(websocket: WebSocket, execution_id: str):
    """
    WebSocket endpoint for real-time execution event streaming.
    Client sends: { "action": "start", "node_ids": [...] }
                  { "action": "ping" }
    Server sends: node_event, execution_status, heartbeat, completed messages.
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for execution [{execution_id}].")

    _connections.setdefault(execution_id, set()).add(websocket)
    heartbeat_task = None
    simulation_task = None

    try:
        # Send initial connection ACK
        await websocket.send_text(json.dumps({
            "type": "connected",
            "execution_id": execution_id,
            "message": f"Connected to execution stream [{execution_id}]",
            "ts": time.time(),
        }))

        # Heartbeat coroutine
        async def send_heartbeat():
            while True:
                await asyncio.sleep(5)
                try:
                    await websocket.send_text(json.dumps({"type": "heartbeat", "ts": time.time()}))
                except Exception:
                    break

        heartbeat_task = asyncio.create_task(send_heartbeat())

        # Message loop
        async for raw in websocket.iter_text():
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            action = msg.get("action")

            if action == "start":
                node_ids = msg.get("node_ids", [])
                if not node_ids:
                    node_ids = [f"step_{i}" for i in range(1, 4)]

                # Cancel any previous simulation
                if simulation_task and not simulation_task.done():
                    simulation_task.cancel()

                from app.api.v1.runtime import _execution_signals
                _execution_signals[execution_id] = "RUNNING"

                simulation_task = asyncio.create_task(
                    _simulate_execution(execution_id, node_ids)
                )

            elif action == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "ts": time.time()}))

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for execution [{execution_id}].")
    except Exception as exc:
        logger.error(f"WebSocket error for [{execution_id}]: {exc}")
    finally:
        if heartbeat_task:
            heartbeat_task.cancel()
        if simulation_task:
            simulation_task.cancel()
        _connections.get(execution_id, set()).discard(websocket)
        logger.info(f"WebSocket cleanup complete for [{execution_id}].")
