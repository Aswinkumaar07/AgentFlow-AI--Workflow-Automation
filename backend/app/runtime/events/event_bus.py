import asyncio
import logging
from typing import Any, Callable, Dict, List
from app.runtime.events.event_types import RuntimeEvent, RuntimeEventType

logger = logging.getLogger("agentflow.runtime.events.event_bus")

SubscriberCallback = Callable[[RuntimeEvent], Any]


class EventBus:
    """Async Event Bus for publishing and subscribing to workflow runtime events."""

    def __init__(self) -> None:
        self._subscribers: Dict[RuntimeEventType, List[SubscriberCallback]] = {}
        self._event_history: List[RuntimeEvent] = []

    def subscribe(self, event_type: RuntimeEventType, callback: SubscriberCallback) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    async def publish(self, event: RuntimeEvent) -> None:
        self._event_history.append(event)
        logger.info(f"Published Runtime Event [{event.event_type}] for execution [{event.execution_id}] node [{event.node_id}].")

        callbacks = self._subscribers.get(event.event_type, [])
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in event subscriber callback for [{event.event_type}]: {e}")

    def get_events_for_execution(self, execution_id: str) -> List[RuntimeEvent]:
        return [e for e in self._event_history if e.execution_id == execution_id]


event_bus = EventBus()
