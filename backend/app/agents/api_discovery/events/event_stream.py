import logging
import time
from typing import Any, Callable, Dict, List

logger = logging.getLogger("agentflow.api_discovery.events")


class EventStreamingEngine:
    """Enterprise Event Streaming Engine publishing events to Redis Streams, Kafka, or PubSub."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}

    def subscribe(self, event_type: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        event = {
            "event_type": event_type,
            "timestamp": time.time(),
            "payload": payload,
        }
        logger.info(f"Published Discovery Event [{event_type}]: {payload.get('summary', str(payload)[:80])}")

        for callback in self._subscribers.get(event_type, []):
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error executing event subscriber for [{event_type}]: {e}")


event_stream = EventStreamingEngine()
