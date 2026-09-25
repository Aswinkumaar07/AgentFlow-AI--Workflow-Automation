import asyncio
import logging
from typing import Any, Dict, List
from app.runtime.node_executor import node_executor

logger = logging.getLogger("agentflow.runtime.scheduler")


class RuntimeScheduler:
    """Dispatches ready DAG nodes for execution (designed for future parallel worker scaling)."""

    def __init__(self) -> None:
        self.node_executor = node_executor

    async def dispatch_ready_nodes(self, node_inputs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Dispatches a list of ready node input payloads concurrently via asyncio.gather."""
        if not node_inputs:
            return []

        tasks = [self.node_executor.execute_node(inp) for inp in node_inputs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        final_results = []
        for inp, res in zip(node_inputs, results):
            node_id = inp["metadata"]["node_id"]
            if isinstance(res, Exception):
                logger.error(f"Node [{node_id}] execution failed with exception: {res}")
                final_results.append({
                    "node_id": node_id,
                    "status": "FAILED",
                    "output": {"error": str(res)},
                    "latency": 0.0,
                    "retries": 0,
                    "timestamp": "",
                })
            else:
                res["node_id"] = node_id
                final_results.append(res)

        return final_results


runtime_scheduler = RuntimeScheduler()
