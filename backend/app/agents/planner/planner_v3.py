import logging
import re
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.agents.connector_ai import connector_selector, operation_ranker
from app.agents.parameter_ai import parameter_ai_service
from app.agents.validator import validator_ai_service
from app.agents.parameter_autofill import parameter_autofill_engine

logger = logging.getLogger("agentflow.agents.planner_v3")


class PlanningResult(BaseModel):
    intent: str
    entities: Dict[str, Any] = Field(default_factory=dict)
    selected_connectors: List[str] = Field(default_factory=list)
    selected_operations: List[str] = Field(default_factory=list)
    workflow_graph: Dict[str, Any] = Field(default_factory=dict)
    variables: List[str] = Field(default_factory=list)
    missing_inputs: List[str] = Field(default_factory=list)
    confidence: float = 0.95
    reasoning_trace: List[str] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)


class IntelligentPlannerEngineV3:
    """
    AgentFlow AI - Intelligent Planner Engine V3
    Reasoning-based pipeline (9 stages):
    Intent Classification -> Entity Extraction -> Connector Selection -> Operation Ranking ->
    Graph Dependency Construction -> Parameter Extraction -> Variable Planning -> Validation -> Missing Input Detection.
    """

    SUPPORTED_CONNECTORS = [
        "Gmail",
        "Google Drive",
        "Google Sheets",
        "Slack",
        "GitHub",
        "Stripe",
        "Notion",
        "Generic REST",
        "Webhook",
        "Schedule",
        "AI",
        "Condition",
        "Loop",
        "Merge",
        "Approval",
    ]

    def plan(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> PlanningResult:
        p_lower = prompt.lower().strip()
        trace: List[str] = []

        # -------------------------------------------------------------
        # Stage 1: Intent Classification
        # -------------------------------------------------------------
        intents: List[str] = []

        if "weekday" in p_lower or "schedule" in p_lower or "cron" in p_lower or "every" in p_lower or "night" in p_lower or "monday" in p_lower:
            intents.append("SCHEDULE_TRIGGER")

        if "webhook" in p_lower:
            intents.append("WEBHOOK_TRIGGER")

        if "github" in p_lower or "pr" in p_lower or "repo" in p_lower or "issue" in p_lower:
            intents.append("GITHUB_EVENT")

        if "sheet" in p_lower or "excel" in p_lower or "spreadsheet" in p_lower:
            intents.append("SHEETS_OPERATIONS")

        if "unread" in p_lower or "read" in p_lower or "list" in p_lower or "invoice" in p_lower or "arrives" in p_lower:
            intents.append("READ_EMAIL")

        if "email" in p_lower or "gmail" in p_lower or "send" in p_lower:
            if "READ_EMAIL" not in intents and "unread" not in p_lower and "invoice" not in p_lower and "arrives" not in p_lower:
                intents.append("SEND_EMAIL")

        if "slack" in p_lower or "channel" in p_lower or "notify" in p_lower:
            intents.append("SLACK_NOTIFY")

        if "ai" in p_lower or "summarize" in p_lower or "extract" in p_lower:
            intents.append("SUMMARIZE_AI")

        if "stripe" in p_lower or "payment" in p_lower:
            intents.append("STRIPE_EVENT")

        if "notion" in p_lower:
            intents.append("NOTION_OPERATIONS")

        if "drive" in p_lower or "backup" in p_lower:
            intents.append("DRIVE_OPERATIONS")

        if not intents:
            intents.append("GENERIC_AUTOMATION")

        primary_intent = intents[0]
        trace.append(f"Stage 1 [Intent Classification]: Primary Intent = {primary_intent} | All Intents = {intents}")

        # -------------------------------------------------------------
        # Stage 2: Dynamic Entity Extraction
        # -------------------------------------------------------------
        entities: Dict[str, Any] = {}
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", prompt)
        if emails:
            entities["emails"] = emails
            entities["recipient_email"] = emails[0]

        if "good morning" in p_lower:
            entities["subject"] = "Good Morning ☀️"
            entities["body"] = "Good Morning! Hope you have a wonderful day ahead."

        if "#" in prompt:
            channel = prompt[prompt.find("#"):].split()[0]
            entities["channel"] = channel
            entities["slack_channel"] = channel
        elif "slack" in p_lower or "channel" in p_lower or "#" in p_lower:
            entities["slack_channel"] = "#dev-alerts"

        if "repo:" in prompt:
            entities["github_repo"] = prompt.split("repo:")[1].strip().split()[0]
        elif "github" in p_lower:
            entities["github_repo"] = "AgentFlow-AI/TERRAWATCH"

        # Schedule parsing
        if "weekday at 8am" in p_lower or "every weekday" in p_lower:
            entities["schedule_cron"] = "0 8 * * 1-5"
            entities["schedule_desc"] = "Every weekday at 8:00 AM"
        elif "every night" in p_lower or "nightly" in p_lower or "night" in p_lower:
            entities["schedule_cron"] = "0 0 * * *"
            entities["schedule_desc"] = "Every night at 12:00 AM"
        elif "monday" in p_lower:
            entities["schedule_cron"] = "0 9 * * 1"
            entities["schedule_desc"] = "Every Monday at 9:00 AM"

        trace.append(f"Stage 2 [Entity Extraction]: Extracted Entities = {entities}")

        # -------------------------------------------------------------
        # Stage 3: Semantic Connector Selection (via Connector AI)
        # -------------------------------------------------------------
        connector_candidates = connector_selector.select_connectors(prompt, top_k=5)
        connectors = [c.provider for c in connector_candidates]

        if "SCHEDULE_TRIGGER" in intents and "Schedule" not in connectors:
            connectors.append("Schedule")

        if not connectors:
            connectors = ["Gmail"]

        trace.append(f"Stage 3 [Semantic Connector Selection]: Selected Connectors = {connectors}")

        # -------------------------------------------------------------
        # Stage 4: Dynamic Operation Ranking (via Connector AI)
        # -------------------------------------------------------------
        ranked_ops = operation_ranker.rank_operations(prompt, top_k=5)
        operations = [op.operation for op in ranked_ops]
        trace.append(f"Stage 4 [Operation Ranking]: Ranked Candidate Operations = {operations}")

        # -------------------------------------------------------------
        # Stage 5 & 6: Parameter & Dependency Graph Construction
        # -------------------------------------------------------------
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        variables: List[str] = []

        if "SCHEDULE_TRIGGER" in intents:
            variables.append("{{$now}}")

        # Determine Trigger configuration
        if "SCHEDULE_TRIGGER" in intents:
            trigger = {
                "type": "Schedule",
                "cron": entities.get("schedule_cron", "0 8 * * 1-5"),
                "description": entities.get("schedule_desc", "Recurring Schedule Trigger"),
            }
        elif "WEBHOOK_TRIGGER" in intents:
            trigger = {"type": "Webhook", "endpoint": "/api/v1/triggers/webhooks/webhook", "method": "POST"}
            variables.append("{{trigger_payload.body}}")
        elif "GITHUB_EVENT" in intents and "issue" in p_lower:
            trigger = {"type": "GitHub", "event": "issues.opened", "repo": entities.get("github_repo", "AgentFlow-AI/TERRAWATCH")}
            variables.append("{{trigger.issue.title}}")
        elif "GITHUB_EVENT" in intents and ("pr" in p_lower or "pull request" in p_lower):
            trigger = {"type": "GitHub", "event": "pull_request.opened", "repo": entities.get("github_repo", "AgentFlow-AI/TERRAWATCH")}
            variables.append("{{trigger.pull_request.title}}")
        elif "STRIPE_EVENT" in intents:
            trigger = {"type": "Stripe", "event": "payment_intent.succeeded"}
            variables.append("{{trigger_payload.amount}}")
        elif "READ_EMAIL" in intents and "invoice" in p_lower:
            trigger = {"type": "Gmail", "event": "new_message", "query": "label:invoices"}
        elif "READ_EMAIL" in intents and "unread" in p_lower:
            trigger = {"type": "Gmail", "event": "new_message", "query": "is:unread"}
        else:
            trigger = {"type": "Manual", "description": "Manual instant trigger"}

        # -------------------------------------------------------------
        # Dynamic Graph Topology Composition
        # -------------------------------------------------------------

        # 1. Webhook -> AI -> Email
        if "WEBHOOK_TRIGGER" in intents and "SUMMARIZE_AI" in intents and ("SEND_EMAIL" in intents or "email" in p_lower):
            nodes.extend([
                {
                    "id": "step_1",
                    "label": "AI Text Summarizer",
                    "provider": "AI",
                    "operation_id": "ai.summarize",
                },
                {
                    "id": "step_2",
                    "label": "Gmail Send Email",
                    "provider": "Gmail",
                    "operation_id": "gmail.messages.send",
                },
            ])
            edges.append({"id": "e1-2", "source": "step_1", "target": "step_2"})
            variables.extend(["{{trigger_payload.body}}", "{{step_1.summary}}"])

        # 2. Summarize unread Gmail using AI
        elif "unread" in p_lower and "ai" in p_lower:
            nodes.extend([
                {
                    "id": "step_1",
                    "label": "Gmail List Unread Messages",
                    "provider": "Gmail",
                    "operation_id": "gmail.messages.list",
                },
                {
                    "id": "step_2",
                    "label": "AI Summarize Emails",
                    "provider": "AI",
                    "operation_id": "ai.summarize",
                },
            ])
            edges.append({"id": "e1-2", "source": "step_1", "target": "step_2"})
            variables.extend(["{{step_1.messages}}", "{{step_2.summary}}"])

        # 3. Upload Gmail invoices to Drive
        elif "invoice" in p_lower and "drive" in p_lower:
            nodes.extend([
                {
                    "id": "step_1",
                    "label": "Gmail List Messages",
                    "provider": "Gmail",
                    "operation_id": "gmail.messages.list",
                },
                {
                    "id": "step_2",
                    "label": "Loop Attachments",
                    "provider": "Loop",
                    "operation_id": "loop.process",
                },
                {
                    "id": "step_3",
                    "label": "Condition Is PDF",
                    "provider": "Condition",
                    "operation_id": "condition.evaluate",
                },
                {
                    "id": "step_4",
                    "label": "Google Drive Upload File",
                    "provider": "Google Drive",
                    "operation_id": "drive.files.create",
                },
            ])
            edges.extend([
                {"id": "e1-2", "source": "step_1", "target": "step_2"},
                {"id": "e2-3", "source": "step_2", "target": "step_3"},
                {"id": "e3-4", "source": "step_3", "target": "step_4", "sourceHandle": "true_branch"},
            ])
            variables.extend(["{{step_1.attachments}}", "{{$loop.item.name}}"])

        # 4. Google Sheets employees -> Loop -> Gmail
        elif "SHEETS_OPERATIONS" in intents and "loop" in p_lower:
            nodes.extend([
                {
                    "id": "step_1",
                    "label": "Read Sheets Rows",
                    "provider": "Google Sheets",
                    "operation_id": "sheets.spreadsheets.values.get",
                },
                {
                    "id": "step_2",
                    "label": "Loop Employee Rows",
                    "provider": "Loop",
                    "operation_id": "loop.process",
                },
                {
                    "id": "step_3",
                    "label": "Gmail Send Email to Employee",
                    "provider": "Gmail",
                    "operation_id": "gmail.messages.send",
                },
                {
                    "id": "step_4",
                    "label": "Merge Loop Results",
                    "provider": "Merge",
                    "operation_id": "merge.process",
                },
            ])
            edges.extend([
                {"id": "e1-2", "source": "step_1", "target": "step_2"},
                {"id": "e2-3", "source": "step_2", "target": "step_3"},
                {"id": "e3-4", "source": "step_3", "target": "step_4"},
            ])
            variables.extend(["{{step_1.values}}", "{{$loop.item.email}}", "{{$loop.item.name}}"])

        # 5. Backup Google Drive every night
        elif "backup" in p_lower and "drive" in p_lower:
            nodes.extend([
                {
                    "id": "step_1",
                    "label": "Google Drive List Files",
                    "provider": "Google Drive",
                    "operation_id": "drive.files.create",
                },
                {
                    "id": "step_2",
                    "label": "Google Drive Backup Archive",
                    "provider": "Google Drive",
                    "operation_id": "drive.files.create",
                },
            ])
            edges.append({"id": "e1-2", "source": "step_1", "target": "step_2"})
            variables.append("{{$now}}")

        # 6. Stripe payment -> Slack
        elif "stripe" in p_lower and "slack" in p_lower:
            nodes.extend([
                {
                    "id": "step_1",
                    "label": "Stripe Get Charge Details",
                    "provider": "Stripe",
                    "operation_id": "stripe.charges.get",
                },
                {
                    "id": "step_2",
                    "label": "Slack Post Payment Alert",
                    "provider": "Slack",
                    "operation_id": "slack.chat.postMessage",
                },
            ])
            edges.append({"id": "e1-2", "source": "step_1", "target": "step_2"})
            variables.append("{{step_1.amount}}")

        # 7. GitHub Issue -> Notion
        elif "issue" in p_lower and "notion" in p_lower:
            nodes.extend([
                {
                    "id": "step_1",
                    "label": "GitHub Fetch Issue",
                    "provider": "GitHub",
                    "operation_id": "github.issues.get",
                },
                {
                    "id": "step_2",
                    "label": "Notion Create Page",
                    "provider": "Notion",
                    "operation_id": "notion.pages.create",
                },
            ])
            edges.append({"id": "e1-2", "source": "step_1", "target": "step_2"})
            variables.append("{{step_1.title}}")

        # 8. Notify Slack when GitHub PR opens
        elif "GITHUB_EVENT" in intents or ("github" in p_lower and "slack" in p_lower):
            nodes.extend([
                {
                    "id": "step_1",
                    "label": "GitHub Fetch Pull Requests",
                    "provider": "GitHub",
                    "operation_id": "github.pulls.list",
                },
                {
                    "id": "step_2",
                    "label": "Slack Post Message",
                    "provider": "Slack",
                    "operation_id": "slack.chat.postMessage",
                },
            ])
            edges.append({"id": "e1-2", "source": "step_1", "target": "step_2"})
            variables.append("{{step_1.title}}")

        # 9. Send email / Good morning email
        elif "email" in p_lower or "gmail" in p_lower or "send" in p_lower:
            nodes.append({
                "id": "step_1",
                "label": "Gmail Send Email",
                "provider": "Gmail",
                "operation_id": "gmail.messages.send",
            })

        # 10. Fallback dynamic connector mapping
        else:
            nodes.append({
                "id": "step_1",
                "label": f"{connectors[0]} Operation",
                "provider": connectors[0],
                "operation_id": operations[0] if operations else "generic.http.request",
            })

        # Deduplicate variables while preserving order
        unique_vars = []
        for v in variables:
            if v not in unique_vars:
                unique_vars.append(v)
        variables = unique_vars

        # -------------------------------------------------------------
        # Stage 6 & 9: Dynamic Parameter AI Engine & Missing Input Detection
        # -------------------------------------------------------------
        nodes, missing_inputs = parameter_ai_service.populate_node_parameters(prompt, nodes)

        trace.append(f"Stage 5 [Dependency Planning]: Constructed Graph Topology with {len(nodes)} nodes and {len(edges)} edges.")
        trace.append(f"Stage 6 [Parameter AI]: Automatically populated node parameters.")
        trace.append(f"Stage 7 [Variable Planning]: Injected Variables = {variables}")

        workflow_graph = {
            "title": prompt.strip().capitalize(),
            "description": f"Executable DAG dynamically reasoned for intent: {primary_intent}",
            "intent": primary_intent,
            "trigger": trigger,
            "nodes": nodes,
            "edges": edges,
        }

        # Pass workflow graph through Parameter Autofill Engine with prompt context
        workflow_graph = parameter_autofill_engine.autofill_workflow_nodes(workflow_graph, prompt=prompt)

        # -------------------------------------------------------------
        # Stage 8: Graph Validation (AI Validator Engine)
        # -------------------------------------------------------------
        val_res = validator_ai_service.validate(workflow_graph)
        trace.append(f"Stage 8 [Validation]: Graph Validated = {val_res.is_valid} | Errors = {val_res.errors} | Warnings = {val_res.warnings}")

        if not val_res.is_valid:
            logger.error(f"Planner V3 DAG Validation Rejected: {val_res.errors}")

        trace.append(f"Stage 9 [Missing Input Detection]: Missing Inputs Detected = {missing_inputs}")

        return PlanningResult(
            intent=primary_intent,
            entities=entities,
            selected_connectors=connectors,
            selected_operations=operations,
            workflow_graph=workflow_graph,
            variables=variables,
            missing_inputs=missing_inputs,
            confidence=val_res.confidence if val_res.is_valid else 0.0,
            reasoning_trace=trace,
            validation_errors=val_res.errors,
            validation_warnings=val_res.warnings,
        )


intelligent_planner_v3 = IntelligentPlannerEngineV3()
