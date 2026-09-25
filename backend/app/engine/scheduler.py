import logging
import threading
from typing import Dict
from app.engine.interfaces import BaseWorkflowScheduler

logger = logging.getLogger("agentflow.engine.scheduler")


class WorkflowScheduler(BaseWorkflowScheduler):
    """Cron and Event-Driven Workflow Scheduler."""

    def __init__(self) -> None:
        self._cron_schedules: Dict[str, str] = {}
        self._lock = threading.Lock()

    def schedule_cron(self, workflow_id: str, cron_expression: str) -> None:
        with self._lock:
            self._cron_schedules[workflow_id] = cron_expression
            logger.info(f"Scheduled cron trigger for workflow [{workflow_id}]: '{cron_expression}'")

    def get_schedules(self) -> Dict[str, str]:
        with self._lock:
            return dict(self._cron_schedules)


workflow_scheduler = WorkflowScheduler()
