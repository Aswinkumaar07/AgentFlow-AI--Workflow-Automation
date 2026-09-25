import re
import logging
from typing import Any, Dict, List, Optional, Tuple
from app.connectors.registry import connector_registry

logger = logging.getLogger("agentflow.agents.parameter_autofill")


class ParameterAutofillEngine:
    """
    AI Parameter Autofill Engine (Sprint REAL-1 Enforced).
    Dynamically extracts entities from natural language prompts and merges them with node parameters.
    No hardcoded Good Morning or static fallback templates.
    """

    def extract_entities_from_prompt(self, prompt: str) -> Dict[str, Any]:
        """Extracts structural entities (emails, channels, URLs, cron) directly from user prompt."""
        prompt_clean = prompt.strip()
        entities: Dict[str, Any] = {}

        # 1. Recipient email extraction
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", prompt_clean)
        if emails:
            entities["email"] = emails[0]
            entities["to"] = emails[0]

        # 2. Slack Channel extraction (#channel-name or plain text channel format)
        channels = re.findall(r"#[a-zA-Z0-9_\-]+", prompt_clean)
        ignore_words = {"the", "a", "an", "slack", "channel", "my", "our"}
        if channels:
            entities["channel"] = channels[0]
        else:
            m2 = re.search(r"(?:in|to|on|alert)\s+(?:the\s+|our\s+)?([a-zA-Z0-9_\-]+)\s+channel", prompt_clean, re.IGNORECASE)
            if m2 and m2.group(1).lower() not in ignore_words:
                entities["channel"] = f"#{m2.group(1)}"
            else:
                m1 = re.search(r"(?:channel\s+|in\s+channel\s+|to\s+channel\s+)([a-zA-Z0-9_\-]+)", prompt_clean, re.IGNORECASE)
                if m1 and m1.group(1).lower() not in ignore_words:
                    entities["channel"] = f"#{m1.group(1)}"

        # 3. URLs extraction
        urls = re.findall(r"https?://[^\s]+", prompt_clean)
        if urls:
            entities["url"] = urls[0]

        # 4. Cron / Schedule extraction
        if re.search(r"every\s*5\s*m", prompt_clean, re.IGNORECASE):
            entities["cron"] = "*/5 * * * *"
        elif re.search(r"every\s*hour|hourly", prompt_clean, re.IGNORECASE):
            entities["cron"] = "0 * * * *"
        elif re.search(r"every\s*day|daily", prompt_clean, re.IGNORECASE):
            entities["cron"] = "0 9 * * *"

        return entities

    def autofill_node(
        self,
        provider: str,
        operation_id: str,
        existing_params: Optional[Dict[str, Any]] = None,
        prompt: str = "",
        prev_node_id: str = "",
        prev_provider: str = "",
    ) -> Tuple[Dict[str, Any], Dict[str, float], List[str]]:
        """
        Autofills parameters for a single node preserving prompt entities.
        Does NOT override existing subject/body set by Planner V5.
        """
        params = dict(existing_params or {})
        confidence_scores: Dict[str, float] = {}
        missing_parameters: List[str] = []

        entities = self.extract_entities_from_prompt(prompt)
        op_schema = connector_registry.get_operation_schema(provider, operation_id)

        req_params = op_schema.required_parameters if op_schema else []
        opt_params = op_schema.optional_parameters if op_schema else []

        # 1. Fill Required Parameters from Existing Params & Entities
        for p in req_params:
            name = p.name
            val = params.get(name)

            if name == "channel" and "channel" in entities:
                params["channel"] = entities["channel"]
                confidence_scores["channel"] = 0.95
                continue

            if val is not None and val != "" and val != "missing":
                confidence_scores[name] = 1.0
                continue

            if name == "to" and "email" in entities:
                params["to"] = entities["email"]
                confidence_scores["to"] = 0.95
            elif name in entities:
                params[name] = entities[name]
                confidence_scores[name] = 0.90
            else:
                missing_parameters.append(name)
                confidence_scores[name] = 0.0

        # Preserve and refine parameters set by Planner for Gmail operations
        if provider.lower() in ["gmail", "google gmail", "google_gmail"]:
            if operation_id in ["gmail.messages.send", "gmail.drafts.create", "gmail.messages.reply", "gmail.messages.forward"]:
                from app.agents.planner.gmail_parameter_extractor import extract_gmail_parameters
                gmail_params = extract_gmail_parameters(prompt)
                for k, v in gmail_params.items():
                    if v and (k not in params or not params[k] or params[k] == "missing"):
                        params[k] = v
                        confidence_scores[k] = 0.95
            elif operation_id in ["gmail.messages.search", "gmail.messages.list"]:
                from app.agents.planner.gmail_search_query_builder import build_gmail_search_query
                q_val = str(params.get("q") or "").strip()
                noise_words = ["find email", "find emails", "search email", "search emails", "search for emails", "search my gmail", "search my email", "show me emails", "show emails", "look for emails", "get emails", "find unread emails"]
                if not q_val or q_val == prompt.strip() or any(w in q_val.lower() for w in noise_words):
                    cleaned_q = build_gmail_search_query(prompt, entities)
                    params["q"] = cleaned_q
                    confidence_scores["q"] = 0.98
                logger.info(f"[AI-17.1][PIPELINE_QUERY] provider={provider} op={operation_id} q='{params.get('q')}'")
        elif provider.lower() in ["slack"] or operation_id == "slack.chat.postMessage":
            from app.agents.planner.slack_parameter_extractor import extract_slack_text
            curr_text = str(params.get("text") or "").strip()
            if not curr_text or curr_text == prompt.strip():
                params["text"] = extract_slack_text(prompt)
                confidence_scores["text"] = 0.95

        # 2. Fill Optional Parameters
        for p in opt_params:
            name = p.name
            val = params.get(name)

            if name == "channel" and "channel" in entities:
                params["channel"] = entities["channel"]
                confidence_scores["channel"] = 0.95
                continue

            if val is not None and val != "" and val != "missing":
                confidence_scores[name] = 1.0
                continue

            if name in entities:
                params[name] = entities[name]
                confidence_scores[name] = 0.95

        return params, confidence_scores, missing_parameters

    def autofill_workflow_nodes(self, graph: Dict[str, Any], prompt: str = "") -> Dict[str, Any]:
        """Autofills all node parameters in a workflow graph while strictly preserving Planner V5 intent."""
        nodes = graph.get("nodes", [])
        overall_confidence_scores: List[float] = []

        effective_prompt = prompt or graph.get("title", "") or graph.get("description", "")
        prev_node_id = ""
        prev_provider = ""

        for idx, node in enumerate(nodes):
            provider = node.get("provider", "Generic")
            op_id = node.get("operation_id", node.get("operation", ""))
            existing_params = node.get("parameters", {}) or {}

            params, conf_scores, missing = self.autofill_node(
                provider=provider,
                operation_id=op_id,
                existing_params=existing_params,
                prompt=effective_prompt,
                prev_node_id=prev_node_id,
                prev_provider=prev_provider,
            )

            node["parameters"] = params
            node["autofill_metadata"] = {
                "confidence_scores": conf_scores,
                "missing_parameters": missing,
                "is_complete": len(missing) == 0,
            }
            node["is_fully_configured"] = len(missing) == 0

            avg_conf = (sum(conf_scores.values()) / len(conf_scores)) if conf_scores else 0.9
            overall_confidence_scores.append(avg_conf)

            prev_node_id = node.get("id", f"node_{idx}")
            prev_provider = provider

        avg_overall = (sum(overall_confidence_scores) / len(overall_confidence_scores)) if overall_confidence_scores else 0.95
        graph["nodes"] = nodes
        graph["overall_confidence_score"] = round(avg_overall, 2)
        graph["is_fully_configured"] = True
        logger.info(f"[AI-14][PARAMETERS] Configured {len(nodes)} node(s): {[n.get('parameters') for n in nodes]}")
        logger.info(f"Parameter Autofill Engine configured {len(nodes)} node(s) with {avg_overall:.2f} confidence.")
        return graph


parameter_autofill_engine = ParameterAutofillEngine()
