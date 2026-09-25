import logging
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.runtime.workflow_executor import workflow_runtime_executor_v3

logger = logging.getLogger("agentflow.triggers.engine")


class TriggerType(str, Enum):
    WEBHOOK = "WEBHOOK"
    CRON = "CRON"
    SCHEDULE = "SCHEDULE"
    EMAIL = "EMAIL"
    GITHUB = "GITHUB"
    SLACK = "SLACK"
    GOOGLE_SHEETS = "GOOGLE_SHEETS"


class WorkflowActivationStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"


class TriggerSubscriptionModel(BaseModel):
    id: str
    workflow_id: str
    tenant_id: str = "usr_1"
    trigger_type: TriggerType
    config: Dict[str, Any] = Field(default_factory=dict)
    workflow_spec: Dict[str, Any] = Field(default_factory=dict)
    status: WorkflowActivationStatus = WorkflowActivationStatus.ACTIVE
    created_at: float = Field(default_factory=time.time)


class TriggerEngine:
    """Enterprise Trigger Engine listening for incoming webhooks, cron schedules, and API events to dispatch active workflows."""

    def __init__(self) -> None:
        self._triggers: Dict[str, TriggerSubscriptionModel] = {}
        self._seed_default_triggers()

    def _seed_default_triggers(self) -> None:
        default_trigger = TriggerSubscriptionModel(
            id="trig_gmail_01",
            workflow_id="wf_gmail_drive_slack_sheets",
            trigger_type=TriggerType.EMAIL,
            config={"provider": "Gmail", "query": "label:invoices"},
            status=WorkflowActivationStatus.ACTIVE,
            workflow_spec={
                "workflow_id": "wf_gmail_drive_slack_sheets",
                "name": "Gmail PDF to Drive, Slack & Google Sheets",
                "steps": [
                    {
                        "step_id": "step_1",
                        "provider": "Gmail",
                        "operation_id": "gmail.messages.list",
                        "parameters": {"query": "label:invoices"},
                    },
                    {
                        "step_id": "step_2",
                        "provider": "Google Drive",
                        "operation_id": "drive.files.create",
                        "parameters": {"folder": "Invoices"},
                        "dependencies": ["step_1"],
                    },
                    {
                        "step_id": "step_3",
                        "provider": "Slack",
                        "operation_id": "slack.chat.postMessage",
                        "parameters": {"channel": "#finance-alerts"},
                        "dependencies": ["step_2"],
                    },
                    {
                        "step_id": "step_4",
                        "provider": "Google Sheets",
                        "operation_id": "sheets.spreadsheets.values.append",
                        "parameters": {"range": "Sheet1!A1:Z"},
                        "dependencies": ["step_3"],
                    },
                ],
            },
        )
        self._triggers[default_trigger.id] = default_trigger

    async def register_trigger(
        self,
        workflow_id: str,
        trigger_type: TriggerType,
        config: Dict[str, Any],
        workflow_spec: Dict[str, Any],
        tenant_id: str = "usr_1",
    ) -> TriggerSubscriptionModel:
        trig_id = f"trig_{uuid.uuid4().hex[:10]}"
        sub = TriggerSubscriptionModel(
            id=trig_id,
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            trigger_type=trigger_type,
            config=config,
            workflow_spec=workflow_spec,
            status=WorkflowActivationStatus.ACTIVE,
        )
        self._triggers[trig_id] = sub
        logger.info(f"Registered ACTIVE Trigger [{trig_id}] type [{trigger_type.value}] for workflow [{workflow_id}].")
        return sub

    async def update_activation_status(
        self, trigger_id: str, new_status: WorkflowActivationStatus
    ) -> Optional[TriggerSubscriptionModel]:
        trig = self._triggers.get(trigger_id)
        if trig:
            trig.status = new_status
            logger.info(f"Updated Trigger [{trigger_id}] status to [{new_status.value}].")
            return trig
        return None

    async def process_incoming_event(
        self, trigger_type: TriggerType, payload: Dict[str, Any], tenant_id: str = "usr_1"
    ) -> List[Dict[str, Any]]:
        """Processes an incoming webhook/event payload and dispatches all active matching workflows asynchronously."""
        active_triggers = [
            t for t in self._triggers.values()
            if t.trigger_type == trigger_type and t.status == WorkflowActivationStatus.ACTIVE and t.tenant_id.lower() == tenant_id.lower()
        ]

        logger.info(f"Trigger Engine received event [{trigger_type.value}] matching {len(active_triggers)} ACTIVE workflows.")

        results = []
        for trig in active_triggers:
            initial_context = {"trigger_payload": payload, "event_timestamp": time.time()}
            exec_state = await workflow_runtime_executor_v3.execute_workflow(
                workflow_spec=trig.workflow_spec, initial_context=initial_context
            )
            results.append({"trigger_id": trig.id, "execution_id": exec_state.execution_id, "status": exec_state.status})

        return results


trigger_engine = TriggerEngine()
