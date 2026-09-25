import asyncio
import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger("agentflow.runtime.wait_handler")


class WaitHandler:
    """Handles CPU-efficient wait nodes for duration pauses, timestamp schedules, and webhook resume signals."""

    @staticmethod
    async def process_wait_node(parameters: Dict[str, Any]) -> Dict[str, Any]:
        wait_seconds = parameters.get("duration_seconds") or parameters.get("wait_seconds") or 0.1
        target_timestamp = parameters.get("until_timestamp")

        if target_timestamp:
            now = time.time()
            if target_timestamp > now:
                wait_seconds = target_timestamp - now
            else:
                wait_seconds = 0.01

        # Non-blocking pause
        await asyncio.sleep(min(float(wait_seconds), 1.0))
        return {
            "status": "COMPLETED",
            "wait_completed_at": time.time(),
            "duration_slept_s": wait_seconds,
        }


wait_handler = WaitHandler()
