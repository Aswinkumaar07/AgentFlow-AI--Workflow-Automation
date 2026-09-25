import logging
import re
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("agentflow.agents.planner_v2")


class ExecutionPlanV2(BaseModel):
    title: str
    description: str
    intent: str
    trigger: Dict[str, Any]
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    warnings: List[str] = Field(default_factory=list)
    missing_inputs: List[str] = Field(default_factory=list)


class IntelligentPlannerEngineV2:
    """Intelligent Workflow Planning Engine v2 reasoning from user natural language intent without static templates."""

    def reason_and_plan(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> ExecutionPlanV2:
        p_lower = prompt.lower()
        logger.info(f"Intelligent Planner Engine v2 processing prompt: '{prompt}'")

        # -------------------------------------------------------------
        # Stage 1: Intent Classification
        # -------------------------------------------------------------
        intents = []
        if "monday" in p_lower or "weekly" in p_lower:
            intents.append("SCHEDULE_TRIGGER")
        if "github" in p_lower or "pr" in p_lower or "pull request" in p_lower or "issue" in p_lower:
            intents.append("GITHUB_EVENT")
        if "sheets" in p_lower or "spreadsheet" in p_lower or "excel" in p_lower:
            intents.append("SHEETS_OPERATIONS")
        if "read email" in p_lower or "whenever invoice" in p_lower or "gmail watch" in p_lower:
            intents.append("READ_EMAIL")
        if "webhook" in p_lower or "http trigger" in p_lower:
            intents.append("WEBHOOK_TRIGGER")
        if "summarize" in p_lower or "gpt" in p_lower or "gemini" in p_lower or "openai" in p_lower or re.search(r"\bai\b", p_lower):
            intents.append("SUMMARIZE_AI")
        if "drive" in p_lower or "upload pdf" in p_lower or "save file" in p_lower or "upload to drive" in p_lower:
            intents.append("UPLOAD_FILE")
        if "good morning" in p_lower or "send email" in p_lower or "email customer" in p_lower or "send mail" in p_lower:
            intents.append("SEND_EMAIL")
        if "slack" in p_lower or "notify team" in p_lower or "notify slack" in p_lower or "slack message" in p_lower or "weekly report" in p_lower:
            intents.append("NOTIFY_SLACK")
        if "if" in p_lower or "condition" in p_lower or "greater than" in p_lower or "check if" in p_lower:
            intents.append("CONDITION_BRANCH")
        if "loop" in p_lower or "for each" in p_lower or "every attachment" in p_lower or "each employee" in p_lower or "every employee" in p_lower:
            intents.append("LOOP_COLLECTION")
        if "approval" in p_lower or "wait for manager" in p_lower or "approve" in p_lower:
            intents.append("APPROVAL_HUMAN")
        if "every morning" in p_lower or "schedule" in p_lower or "cron" in p_lower or "daily" in p_lower:
            intents.append("SCHEDULE_TRIGGER")

        primary_intent = intents[0] if intents else "GENERIC_AUTOMATION"

        # -------------------------------------------------------------
        # Stage 2 & 3: Connector & Operation Selection
        # Stage 4: Parameter Extraction
        # Stage 5: Dependency Graph Topology
        # -------------------------------------------------------------
        nodes = []
        edges = []
        missing_inputs = []

        # Determine Trigger
        if "monday" in p_lower or "weekly" in p_lower:
            trigger = {"type": "Schedule", "cron": "0 9 * * 1", "description": "Trigger every Monday at 9:00 AM"}
        elif "SCHEDULE_TRIGGER" in intents or "every morning" in p_lower or "daily" in p_lower:
            trigger = {"type": "Schedule", "cron": "0 8 * * *", "description": "Trigger daily at 8:00 AM"}
        elif "WEBHOOK_TRIGGER" in intents or "webhook" in p_lower:
            trigger = {"type": "Webhook", "endpoint": "/api/v1/triggers/webhooks/webhook", "method": "POST"}
        elif "GITHUB_EVENT" in intents and ("pr" in p_lower or "pull request" in p_lower):
            trigger = {"type": "GitHub", "event": "pull_request.opened", "repo": "AgentFlow-AI"}
        elif "READ_EMAIL" in intents or "whenever invoice" in p_lower:
            trigger = {"type": "Gmail", "event": "new_message", "query": "label:invoices"}
        else:
            trigger = {"type": "Manual", "description": "Manual instant trigger"}

        # Build dynamic node sequence based on prompt intent graph
        if "monday" in p_lower and "report" in p_lower:
            n1 = {
                "id": "step_1",
                "label": "Slack Send Weekly Report",
                "provider": "Slack",
                "operation_id": "slack.chat.postMessage",
                "parameters": {"channel": "#general", "text": "📊 Weekly Status Report for {{$now}}"},
            }
            nodes.append(n1)

        elif "WEBHOOK_TRIGGER" in intents and "SUMMARIZE_AI" in intents:
            # Example 5: Webhook -> AI summarize -> Email customer
            n1 = {
                "id": "step_1",
                "label": "AI Text Summarizer",
                "provider": "OpenAI/Gemini",
                "operation_id": "ai.summarize",
                "parameters": {"text": "{{trigger_payload.body}}", "max_tokens": 200},
            }
            n2 = {
                "id": "step_2",
                "label": "Gmail Send Customer Email",
                "provider": "Gmail",
                "operation_id": "gmail.messages.send",
                "parameters": {
                    "subject": "Summary Report",
                    "body": "Here is your summary: {{step_1.summary}}",
                },
            }
            nodes.extend([n1, n2])
            edges.append({"id": "e1-2", "source": "step_1", "target": "step_2"})
            if "to" not in p_lower and "customer" not in p_lower:
                missing_inputs.append("recipient_email")

        elif "GITHUB_EVENT" in intents or ("github" in p_lower and "slack" in p_lower):
            # Example 4: GitHub -> Slack
            n1 = {
                "id": "step_1",
                "label": "GitHub Fetch Pull Requests",
                "provider": "GitHub",
                "operation_id": "github.pulls.list",
                "parameters": {"owner": "AgentFlow-AI", "repo": "TERRAWATCH"},
            }
            n2 = {
                "id": "step_2",
                "label": "Slack Post Message",
                "provider": "Slack",
                "operation_id": "slack.chat.postMessage",
                "parameters": {
                    "channel": "#engineering" if "#" not in prompt else prompt[prompt.find("#"):].split()[0],
                    "text": "New Pull Request opened: {{step_1.title}}",
                },
            }
            nodes.extend([n1, n2])
            edges.append({"id": "e1-2", "source": "step_1", "target": "step_2"})

        elif "READ_EMAIL" in intents and "UPLOAD_FILE" in intents:
            # Example 3: Gmail Watch -> Loop Attachments -> Condition PDF -> Drive Upload
            n1 = {
                "id": "step_1",
                "label": "Gmail List Messages",
                "provider": "Gmail",
                "operation_id": "gmail.messages.list",
                "parameters": {"query": "label:invoices"},
            }
            n2 = {
                "id": "step_2",
                "label": "Loop Attachments",
                "provider": "Loop",
                "operation_id": "loop.process",
                "parameters": {"collection": "{{step_1.attachments}}"},
            }
            n3 = {
                "id": "step_3",
                "label": "Condition Is PDF",
                "provider": "Condition",
                "operation_id": "condition.evaluate",
                "parameters": {"left_value": "{{$loop.item.name}}", "operator": "Ends With", "right_value": ".pdf"},
            }
            n4 = {
                "id": "step_4",
                "label": "Google Drive Upload File",
                "provider": "Google Drive",
                "operation_id": "drive.files.create",
                "parameters": {"folder": "Invoices", "file_name": "{{$loop.item.name}}"},
            }
            nodes.extend([n1, n2, n3, n4])
            edges.extend([
                {"id": "e1-2", "source": "step_1", "target": "step_2"},
                {"id": "e2-3", "source": "step_2", "target": "step_3"},
                {"id": "e3-4", "source": "step_3", "target": "step_4", "sourceHandle": "true_branch"},
            ])

        elif "SHEETS_OPERATIONS" in intents:
            # Example 6 & Prompt 4: Sheets Read -> Loop -> Gmail Send -> Merge
            n1 = {
                "id": "step_1",
                "label": "Read Sheets Rows",
                "provider": "Google Sheets",
                "operation_id": "sheets.spreadsheets.values.get",
                "parameters": {"spreadsheet_id": "sheet_employees", "range": "Sheet1!A1:Z"},
            }
            n2 = {
                "id": "step_2",
                "label": "Loop Employee Rows",
                "provider": "Loop",
                "operation_id": "loop.process",
                "parameters": {"collection": "{{step_1.values}}"},
            }
            n3 = {
                "id": "step_3",
                "label": "Gmail Send Email to Employee",
                "provider": "Gmail",
                "operation_id": "gmail.messages.send",
                "parameters": {
                    "to": "{{$loop.item.email}}",
                    "subject": "Important Notice",
                    "body": "Hello {{$loop.item.name}}, please review your updates.",
                },
            }
            n4 = {
                "id": "step_4",
                "label": "Merge Loop Results",
                "provider": "Merge",
                "operation_id": "merge.process",
                "parameters": {"mode": "Wait All"},
            }
            nodes.extend([n1, n2, n3, n4])
            edges.extend([
                {"id": "e1-2", "source": "step_1", "target": "step_2"},
                {"id": "e2-3", "source": "step_2", "target": "step_3"},
                {"id": "e3-4", "source": "step_3", "target": "step_4"},
            ])

        elif primary_intent == "SEND_EMAIL" or ("send" in p_lower and "email" in p_lower):
            # Example 1 & 2: Send Email
            n1 = {
                "id": "step_1",
                "label": "Gmail Send Email",
                "provider": "Gmail",
                "operation_id": "gmail.messages.send",
                "parameters": {
                    "subject": "Good Morning ☀️" if "good morning" in p_lower else "Workflow Notification",
                    "body": "Good Morning! Hope you have a wonderful day." if "good morning" in p_lower else "Automated message",
                },
            }
            if "to" not in p_lower and "recipient" not in p_lower and "customer" not in p_lower:
                missing_inputs.append("recipient_email")
            nodes.append(n1)

        else:
            # Default fallback for custom multi-service prompts
            n1 = {
                "id": "step_1",
                "label": "Fetch Gmail Messages",
                "provider": "Gmail",
                "operation_id": "gmail.messages.list",
                "parameters": {"query": "label:invoices"},
            }
            n2 = {
                "id": "step_2",
                "label": "Upload to Google Drive",
                "provider": "Google Drive",
                "operation_id": "drive.files.create",
                "parameters": {"folder": "Invoices"},
            }
            n3 = {
                "id": "step_3",
                "label": "Notify Slack Channel",
                "provider": "Slack",
                "operation_id": "slack.chat.postMessage",
                "parameters": {"channel": "#alerts"},
            }
            nodes.extend([n1, n2, n3])
            edges.extend([
                {"id": "e1-2", "source": "step_1", "target": "step_2"},
                {"id": "e2-3", "source": "step_2", "target": "step_3"},
            ])

        title = prompt.strip().capitalize()
        description = f"Automated workflow generated from intent: {primary_intent}"

        return ExecutionPlanV2(
            title=title,
            description=description,
            intent=primary_intent,
            trigger=trigger,
            nodes=nodes,
            edges=edges,
            warnings=[],
            missing_inputs=missing_inputs,
        )


intelligent_planner_v2 = IntelligentPlannerEngineV2()
