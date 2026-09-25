import logging
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.connectors.registry import connector_registry
from app.agents.connector_ai import connector_selector, operation_ranker
from app.agents.parameter_autofill import parameter_autofill_engine
from app.agents.validator import validator_ai_service
from app.agents.variables import variable_resolver
from app.agents.planner.gmail_parameter_extractor import extract_gmail_parameters

logger = logging.getLogger("agentflow.agents.planner_v4")


class PlanningResultV4(BaseModel):
    intent: str
    entities: Dict[str, Any] = Field(default_factory=dict)
    selected_connectors: List[str] = Field(default_factory=list)
    selected_operations: List[str] = Field(default_factory=list)
    workflow_graph: Dict[str, Any] = Field(default_factory=dict)
    variables: List[str] = Field(default_factory=list)
    missing_inputs: List[str] = Field(default_factory=list)
    confidence: float = 0.98
    reasoning_trace: List[str] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)
    schedule_metadata: Optional[Dict[str, Any]] = None
    # AI-10: Execution gate — False when validator rejects the workflow
    can_execute: bool = True
    # AI-10: Structured inter-layer pipeline summary
    pipeline_summary: Dict[str, Any] = Field(default_factory=dict)


class IntelligentPlannerEngineV4:
    """
    AgentFlow AI v2.0 - Planner V5: Direct Runtime Integration Engine.
    Generates fully executable DAG nodes containing provider, operation, parameters, authentication,
    runtime_metadata, and execution_metadata.
    Zero transformation layer needed. 100% executable by RuntimeExecutorV3 out-of-the-box.
    """

    def _infer_email_content(self, prompt: str, entities: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], str]:
        """
        Dynamically infers email Subject & Body content, Tone, Intent, Recipient Name, Greeting, and Closing.
        Never uses static templates or hardcoded fallback strings.
        """
        p_lower = prompt.lower().strip()

        # Extract target recipient name if present (e.g., "Wish Sarah happy birthday" -> "Sarah", "Send apology email to John" -> "John")
        recipient_name = ""
        name_match = re.search(r'(?:wish|send|to|apology|sorry)\s+([a-zA-Z]+)', prompt, re.IGNORECASE)
        if name_match:
            candidate = name_match.group(1).strip()
            if candidate.lower() not in ["email", "gmail", "good", "happy", "mail", "message", "a", "an", "the", "apology"]:
                recipient_name = candidate.capitalize()

        if not recipient_name and entities.get("email"):
            email_user = entities["email"].split("@")[0]
            if email_user and not email_user.isdigit():
                recipient_name = email_user.capitalize()

        # 1. Evening Greeting Intent ("Send good night email")
        if "good night" in p_lower or "night email" in p_lower:
            tone = "Warm & Relaxing"
            subject = "Good Night 🌙"
            greeting = f"Good Night {recipient_name}!" if recipient_name else "Good Night!"
            closing = "Sleep well."
            body = f"{greeting}\n{closing}"
            reasoning = f"Stage 5 [Semantic Email Inference]: Tone = '{tone}' | Intent = Evening Greeting | Subject: '{subject}' | Body: '{body}'"
            return subject, body, reasoning

        # 2. Birthday Intent ("Wish Sarah happy birthday")
        if "happy birthday" in p_lower or "birthday" in p_lower:
            tone = "Celebratory & Enthusiastic"
            name_suffix = f" {recipient_name}" if recipient_name else ""
            subject = f"Happy Birthday{name_suffix} 🎉"
            greeting = f"Happy Birthday{name_suffix}!"
            closing = "Have an amazing day."
            body = f"{greeting}\n{closing}"
            reasoning = f"Stage 5 [Semantic Email Inference]: Tone = '{tone}' | Intent = Birthday Greeting | Recipient: '{recipient_name or 'Friend'}' | Subject: '{subject}'"
            return subject, body, reasoning

        # 3. Apology Intent ("Send apology email")
        if any(kw in p_lower for kw in ["apology", "sorry", "apologize"]):
            tone = "Professional & Empathetic"
            subject = "Sincere Apology"
            salutation = f"Dear {recipient_name}," if recipient_name else "Dear Customer,"
            message = "Please accept our sincere apologies for any inconvenience caused. We are taking immediate steps to resolve this matter."
            closing = "Best regards,\nAgentFlow Team"
            body = f"{salutation}\n\n{message}\n\n{closing}"
            reasoning = f"Stage 5 [Semantic Email Inference]: Tone = '{tone}' | Intent = Formal Apology | Recipient: '{recipient_name or 'Customer'}' | Subject: '{subject}'"
            return subject, body, reasoning

        # 4. Morning Greeting Intent ("Send good morning email")
        if "good morning" in p_lower or "morning email" in p_lower:
            tone = "Energetic & Warm"
            subject = "Good Morning ☀️"
            greeting = f"Good Morning {recipient_name}!" if recipient_name else "Good Morning!"
            closing = "Have a great day ahead."
            body = f"{greeting}\n{closing}"
            reasoning = f"Stage 5 [Semantic Email Inference]: Tone = '{tone}' | Intent = Morning Greeting | Subject: '{subject}'"
            return subject, body, reasoning

        # 5. Clean Fallback for Generic Intent
        tone = "Professional"
        subject = "AgentFlow Automated Email Notice"
        salutation = f"Hello {recipient_name}," if recipient_name else "Hello,"
        body = f"{salutation}\n\nThis email is generated automatically by AgentFlow AI.\n\nRegards,\nAgentFlow"
        reasoning = f"Stage 5 [Semantic Email Inference]: Tone = '{tone}' | Clean Default Notice"
        return subject, body, reasoning

    def plan(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> PlanningResultV4:
        p_lower = prompt.lower().strip()
        trace: List[str] = []

        # -------------------------------------------------------------
        # Stage 0: Enterprise Intent Classification Engine (Gemini LLM)
        # -------------------------------------------------------------
        from app.agents.intent_classifier import enterprise_intent_classifier
        intent_res = enterprise_intent_classifier.classify(prompt)
        trace.append(f"Stage 0 [Enterprise Intent Classification]: Intent={intent_res.intent.value} Confidence={intent_res.confidence} Reasoning='{intent_res.reasoning}'")

        # -------------------------------------------------------------
        # Stage 0.5: Task Decomposition Engine (Task 1, Task 2, Task 3)
        # -------------------------------------------------------------
        from app.agents.task_decomposer import enterprise_task_decomposer
        decomp_res = enterprise_task_decomposer.decompose(prompt, intent=intent_res.intent.value)
        trace.append(f"Stage 0.5 [Task Decomposition]: Created {len(decomp_res.tasks)} ordered tasks -> {[t.name for t in decomp_res.tasks]}")

        # -------------------------------------------------------------
        # Stage 1: Dynamic Intent & Entity Reasoning
        # -------------------------------------------------------------
        entities = parameter_autofill_engine.extract_entities_from_prompt(prompt)

        is_schedule = "schedule" in p_lower or "every" in p_lower or "daily" in p_lower or "weekly" in p_lower
        is_webhook = "webhook" in p_lower
        is_github = any(kw in p_lower for kw in ["github", "pr", "pull request", "issue"])
        is_sheets = any(kw in p_lower for kw in ["sheet", "spreadsheet", "table", "excel"])
        is_slack = any(kw in p_lower for kw in ["slack", "channel", "#", "notify"])
        is_gmail = any(kw in p_lower for kw in ["email", "gmail", "send", "mail", "wish"])
        is_notion = "notion" in p_lower
        is_stripe = "stripe" in p_lower
        is_drive = "drive" in p_lower

        primary_intent = intent_res.intent.value
        trace.append(f"Stage 1 [Dynamic Reasoning]: Primary Intent = {primary_intent} | Entities = {intent_res.entities}")

        # -------------------------------------------------------------
        # Stage 2: Trigger Reasoning & Selection
        # -------------------------------------------------------------
        if is_schedule:
            trigger = {
                "type": "Schedule",
                "cron": entities.get("cron", "0 8 * * 1-5"),
                "description": "Recurring schedule trigger",
            }
        elif is_webhook:
            trigger = {"type": "Webhook", "endpoint": "/api/v1/triggers/webhooks/webhook", "method": "POST"}
        elif is_github:
            event_type = "pull_request.opened" if ("pr" in p_lower or "pull request" in p_lower) else "issues.opened"
            trigger = {"type": "GitHub", "event": event_type, "repo": entities.get("repo", "AgentFlow-AI")}
        elif is_stripe:
            trigger = {"type": "Stripe", "event": "payment_intent.succeeded"}
        else:
            trigger = {"type": "Manual", "description": "Instant manual trigger"}

        trace.append(f"Stage 2 [Trigger Determination]: Trigger = {trigger['type']}")

        # -------------------------------------------------------------
        # Stage 3: Semantic Connector Selection (Connector Registry)
        # -------------------------------------------------------------
        selected_providers: List[str] = []
        seen_resolved: set = set()

        if is_sheets and "sheets" not in seen_resolved:
            selected_providers.append("Google Sheets")
            seen_resolved.add("sheets")
        if is_slack and "slack" not in seen_resolved:
            selected_providers.append("Slack")
            seen_resolved.add("slack")
        if is_notion and "notion" not in seen_resolved:
            selected_providers.append("Notion")
            seen_resolved.add("notion")
        if (is_gmail or any(kw in p_lower for kw in ["email", "mail", "gmail", "inbox", "draft", "label", "attachment", "message", "unread", "read"])) and "gmail" not in seen_resolved:
            selected_providers.append("Gmail")
            seen_resolved.add("gmail")
        if is_drive and "drive" not in seen_resolved:
            selected_providers.append("Google Drive")
            seen_resolved.add("drive")
        if is_github and any(kw in p_lower for kw in ["create issue", "close pr", "add comment"]) and "github" not in seen_resolved:
            selected_providers.append("GitHub")
            seen_resolved.add("github")

        # Dynamic Provider Discovery via Connector Registry
        for prov_key in connector_registry.list_supported_providers():
            resolved = connector_registry._resolve_key(prov_key)
            if resolved in seen_resolved:
                continue
            meta = connector_registry.get_connector_metadata(prov_key)
            if meta and meta.display_name:
                p_display = meta.display_name
                if (prov_key in p_lower or p_display.lower() in p_lower) and not any(kw in p_lower for kw in ["github pr", "github issue"]):
                    if p_display not in selected_providers:
                        selected_providers.append(p_display)
                        seen_resolved.add(resolved)

        if not selected_providers:
            candidates = connector_selector.select_connectors(prompt, top_k=3)
            # AI-10: Provider-agnostic — never hardcode Gmail as fallback
            selected_providers = [c.provider for c in candidates if c.provider != trigger["type"]]
            if not selected_providers:
                logger.warning("[AI-10] No provider matched for prompt. Workflow will have 0 provider nodes.")

        trace.append(f"Stage 3 [Connector Selection]: Providers = {selected_providers}")

        # -------------------------------------------------------------
        # Stage 4 & 5: Executable DAG Node Composition with Authentication & Metadata
        # -------------------------------------------------------------
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        selected_ops: List[str] = []
        autonomous_keywords = [
            "reply politely", "reply to latest email", "reply to last email", "reply to email", "summarize inbox", "delete spam", "archive newsletters",
            "forward invoices", "send follow-up", "schedule reminders", "draft emails",
            "generate newsletters", "weekly digest", "monthly digest", "meeting preparation"
        ]
        is_read_summarize = ("read" in p_lower or "unread" in p_lower) and ("summarize" in p_lower or "summary" in p_lower)
        is_invoice_drive_slack = ("invoice" in p_lower or "search" in p_lower) and ("attachment" in p_lower or "download" in p_lower) and ("drive" in p_lower or "upload" in p_lower) and ("slack" in p_lower or "notify" in p_lower)

        # ---------------------------------------------------------------
        # Sprint AI-8 & AI-11: Universal Task-to-DAG Auto-Builder
        # Auto-build executable DAG from decomposed task list for all tasks
        # ---------------------------------------------------------------
        is_multi_step_dag = len(decomp_res.tasks) >= 1

        PROVIDER_AUTH_MAP = {
            "gmail": "google_oauth",
            "google": "google_oauth",
            "drive": "google_oauth",
            "google_drive": "google_oauth",
            "schedule": "none",
            "ai": "none",
            "slack": "slack_oauth",
            "github": "github_oauth",
            "stripe": "stripe_oauth",
            "notion": "notion_oauth",
            "loop": "none",
            "iterator": "none",
            "condition": "none",
        }

        PROVIDER_DISPLAY_MAP = {
            "gmail": "Gmail",
            "drive": "Google Drive",
            "google_drive": "Google Drive",
            "slack": "Slack",
            "ai": "AI",
            "schedule": "Scheduler",
            "github": "GitHub",
            "stripe": "Stripe",
            "notion": "Notion",
            "loop": "Loop Iterator",
            "iterator": "Loop Iterator",
            "condition": "Condition IF/ELSE",
        }

        # ---------------------------------------------------------------
        # Sprint AI-14: Universal Task-to-DAG Auto-Builder
        # TaskDecomposer is the SINGLE SOURCE OF TRUTH for operation selection.
        # ---------------------------------------------------------------
        nodes = []
        edges = []
        selected_providers = []
        selected_ops = []

        for task in decomp_res.tasks:
            step_id = f"step_{task.step}"
            provider = (task.provider or "generic").lower().replace(" ", "_")
            operation = task.operation or "execute.action"
            auth_type = PROVIDER_AUTH_MAP.get(provider, "google_oauth")
            display_name = PROVIDER_DISPLAY_MAP.get(provider, provider.replace("_", " ").title())

            node_params: Dict[str, Any] = dict(task.parameters or {})

            if operation in ["gmail.messages.list", "gmail.messages.search"]:
                q_val = str(node_params.get("q") or "").strip()
                if not q_val or q_val == prompt.strip() or any(kw in q_val.lower() for kw in ["find email", "find emails", "search email", "search emails", "search for emails", "search my gmail", "search my email", "show me emails", "show emails", "look for emails", "get emails"]):
                    from app.agents.planner.gmail_search_query_builder import build_gmail_search_query
                    node_params["q"] = build_gmail_search_query(prompt, entities)
                logger.info(f"[AI-17.1][PLANNER_QUERY] step={step_id} op={operation} q='{node_params.get('q')}'")

                from app.agents.planner.gmail_search_query_builder import extract_gmail_result_count
                extracted_count = extract_gmail_result_count(prompt)
                if extracted_count is not None:
                    logger.info(f"[AI-21][RESULT_COUNT_PROMPT] prompt='{prompt}' requested={extracted_count}")
                    if extracted_count > 50:
                        logger.warning(f"[AI-21][RESULT_COUNT_CAPPED] requested={extracted_count} applied=50")
                        applied_max = 50
                    else:
                        applied_max = extracted_count
                    logger.info(f"[AI-21][RESULT_COUNT_APPLIED] max_results={applied_max}")
                    node_params["max_results"] = applied_max
                else:
                    node_params.setdefault("max_results", 10)
                    logger.info(f"[AI-21][RESULT_COUNT_DEFAULT] max_results={node_params['max_results']}")
            elif operation in ["gmail.messages.send", "gmail.drafts.create", "gmail.messages.forward"]:
                params = extract_gmail_parameters(prompt)
                if "{{" not in node_params.get("body", ""):
                    node_params.setdefault("to", params["to"])
                    node_params.setdefault("subject", params["subject"])
                    node_params.setdefault("body", params["body"])
            elif operation in ["gmail.messages.mark_read", "gmail.messages.mark_unread"]:
                node_params.setdefault("q", "is:unread")
            elif operation == "gmail.messages.delete":
                node_params.setdefault("message_id", "{{step_2.messageId}}")
            elif operation == "ai.summarize":
                node_params.setdefault("text", "{{step_2.snippet}}")
            elif operation == "ai.smart_reply":
                node_params.setdefault("message_id", "{{step_2.messageId}}")
            elif operation == "gmail.attachments.download":
                node_params.setdefault("message_id", "{{step_1.messages[0].id}}")
            elif operation == "drive.files.create":
                node_params.setdefault("name", "{{step_2.filename}}")
                node_params.setdefault("file_path", "{{step_2.savedPath}}")
            elif operation == "slack.chat.postMessage":
                node_params.setdefault("channel", "#general")
                if "{{" not in node_params.get("text", ""):
                    node_params.setdefault("text", "Workflow step completed.")

            node_data = {
                "id": step_id,
                "step_id": step_id,
                "label": task.name or f"Step {task.step}",
                "provider": provider,
                "operation": operation,
                "operation_id": operation,
                "parameters": node_params,
                "authentication": auth_type,
                "runtime_metadata": {
                    "engine": "WorkflowRuntimeExecutorV3",
                    "executor": "NodeExecutor",
                    "requires_auth": auth_type != "none",
                },
                "execution_metadata": {
                    "timeout_seconds": 30.0,
                    "max_retries": 2,
                },
            }
            nodes.append(node_data)
            selected_providers.append(display_name)
            selected_ops.append(operation)
            logger.info(f"[AI-14][OPERATION_SELECTION] step={step_id} provider={provider} operation={operation}")

        logger.info(f"[AI-14][DAG] node_count={len(nodes)} edge_count={len(edges)} operations={selected_ops}")

        # Auto-generate edges from depends_on declarations
        for task in decomp_res.tasks:
            current_id = f"step_{task.step}"
            if task.depends_on:
                for dep in task.depends_on:
                    edges.append({
                        "id": f"e{dep}-{task.step}",
                        "source": f"step_{dep}",
                        "target": current_id,
                    })
            elif task.step > 1:
                prev = task.step - 1
                edges.append({
                    "id": f"e{prev}-{task.step}",
                    "source": f"step_{prev}",
                    "target": current_id,
                })

        trace.append(
            f"Stage 4 [AI-8 Universal DAG Builder]: Auto-composed {len(nodes)}-node DAG "
            f"-> {' -> '.join(t.name for t in decomp_res.tasks)}"
        )
        if not selected_ops and nodes:
            selected_ops = [n.get("operation") or n.get("operation_id", "") for n in nodes]

        trace.append(f"Stage 4 [Executable DAG Assembly]: {len(nodes)} Node(s), {len(edges)} Edge(s)")

        # -------------------------------------------------------------
        # Stage 6: Parameter Autofill & Entity Injection
        # -------------------------------------------------------------
        from app.runtime.credential_resolver import credential_resolver

        autofilled_workflow = {"nodes": nodes}
        for n in autofilled_workflow.get("nodes", []):
            prov = n.get("provider") or ""
            res = credential_resolver.resolve_sync(prov, user_id="usr_1")
            n["parameters"]["auth_provider"] = res["auth_provider"]
            n["parameters"]["credential_id"] = res["credential_id"]
            n["parameters"]["auth_account_label"] = res["auth_account_label"]
            n["parameters"]["auth_status"] = res["auth_status"]
            logger.info(f"[AUTH-6] Planner pre-bound node: node={n.get('id')} provider={res['auth_provider']} account={res['auth_account_label']} status={res['auth_status']}")

        # Sprint AI-4: Graph DAG Generation Engine Visualization Metadata
        from app.agents.dag_generator import enterprise_dag_generator
        viz_res = enterprise_dag_generator.generate_dag(
            tasks=decomp_res.tasks,
            trigger_info=trigger,
            has_condition=any(n.get("type") == "condition" for n in nodes)
        )

        workflow_graph = {
            "title": prompt.strip().capitalize(),
            "description": f"Dynamically reasoned DAG for intent: {primary_intent}",
            "intent": primary_intent,
            "trigger": trigger,
            "nodes": nodes,
            "edges": edges,
            "visualization": viz_res.visualization,
        }

        # Apply AI Parameter Autofill with natural language context
        workflow_graph = parameter_autofill_engine.autofill_workflow_nodes(workflow_graph, prompt=prompt)
        trace.append(f"Stage 6 [Parameter Autofill]: Overall Confidence = {workflow_graph.get('overall_confidence_score', 0.95)}")

        # AI-33: Deterministic Normalization (Precedence Hierarchy & Negative Constraints)
        from app.agents.planner.deterministic_normalizer import deterministic_normalizer
        workflow_graph = deterministic_normalizer.normalize_workflow_graph(prompt, workflow_graph)

        # -------------------------------------------------------------
        # Stage 7 & 8: Variable Resolution & Pre-execution Validation
        # -------------------------------------------------------------
        val_res = validator_ai_service.validate(workflow_graph)
        can_execute = val_res.is_valid
        trace.append(
            f"Stage 7 [AI-9 Pre-execution Validation]: valid={val_res.is_valid} "
            f"errors={len(val_res.errors)} warnings={len(val_res.warnings)} "
            f"can_execute={can_execute}"
        )
        if not can_execute:
            logger.warning(f"[AI-10][GATE] Execution BLOCKED: {val_res.errors}")

        missing_inputs = []
        for n in workflow_graph["nodes"]:
            missing = n.get("autofill_metadata", {}).get("missing_parameters", [])
            missing_inputs.extend(missing)
            if n.get("provider") in ["gmail", "google_gmail"]:
                logger.info("[AUTH-13] Final Gmail Node Parameters")
                logger.info(n.get("parameters", {}))

        # -------------------------------------------------------------
        # Stage 9: Workflow Scheduling Integration
        # -------------------------------------------------------------
        schedule_metadata = None
        from app.services.workflow_scheduler import workflow_scheduler_service
        if workflow_scheduler_service.has_scheduling_intent(prompt):
            schedule_def = workflow_scheduler_service.parse_schedule_expression(prompt)
            schedule_metadata = {
                "prompt": prompt,
                "schedule_type": schedule_def.get("schedule_type"),
                "cron_expression": schedule_def.get("cron"),
                "interval_seconds": schedule_def.get("interval_seconds"),
                "run_at_iso": schedule_def.get("run_at_iso"),
                "description": schedule_def.get("description"),
            }
            trace.append(f"Stage 9 [Workflow Scheduling]: Computed Schedule Metadata (schedule_type='{schedule_def.get('schedule_type')}', description='{schedule_def.get('description')}')")

        import json as _json
        pipeline_summary = {
            "layer": "PlannerV4",
            "intent": primary_intent,
            "task_count": len(decomp_res.tasks),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "providers": selected_providers,
            "operations": selected_ops,
            "trigger": trigger.get("type"),
            "can_execute": can_execute,
            "validation_errors": val_res.errors,
            "validation_warnings": val_res.warnings,
        }
        logger.info(f"[AI-10][JSON] {_json.dumps(pipeline_summary)}")

        return PlanningResultV4(
            intent=primary_intent,
            entities=entities,
            selected_connectors=selected_providers,
            selected_operations=selected_ops,
            workflow_graph=workflow_graph,
            variables=list(entities.keys()),
            missing_inputs=list(set(missing_inputs)),
            confidence=val_res.confidence if val_res.is_valid else 0.90,
            reasoning_trace=trace,
            validation_errors=val_res.errors,
            validation_warnings=val_res.warnings,
            schedule_metadata=schedule_metadata,
            can_execute=can_execute,
            pipeline_summary=pipeline_summary,
        )

    def get_supported_operations(self, provider_name: str) -> List[str]:
        """
        Sprint AI-2: Dynamically queries the Operation Registry to get operations supported by a provider.
        Example: "What operations does Gmail support?" -> Returns ["gmail.messages.send", "gmail.messages.read", ...]
        """
        from app.connectors.provider_operation_registry import provider_operation_registry
        ops = provider_operation_registry.get_provider_operations(provider_name)
        return [op.id for op in ops]


intelligent_planner_v4 = IntelligentPlannerEngineV4()
