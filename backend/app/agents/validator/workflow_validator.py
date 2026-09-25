import re
import logging
from collections import defaultdict
from typing import Any, Dict, List, Set, Optional, Tuple
from pydantic import BaseModel, Field
from app.connectors.registry import connector_registry

logger = logging.getLogger("agentflow.agents.validator")

# ---------------------------------------------------------------------------
# Known providers — used for "Unknown connector" check.
# We accept case-insensitive, and both short names (gmail, slack) and full names.
# ---------------------------------------------------------------------------
_KNOWN_PROVIDERS: Set[str] = {
    "gmail", "google_gmail",
    "google_drive", "drive",
    "google_sheets", "sheets",
    "slack",
    "github",
    "stripe",
    "notion",
    "schedule", "scheduler",
    "ai", "openai", "gemini",
    "webhook",
    "condition", "if", "switch",
    "loop", "iterator",
    "hubspot", "salesforce",
    "jira", "linear",
    "twilio", "sendgrid",
    "dropbox", "onedrive",
    "trello", "asana",
}

# Operations that require specific params
_REQUIRED_PARAMS: Dict[str, List[str]] = {
    "gmail.messages.send":       ["to", "subject", "body"],
    "gmail.messages.reply":      ["message_id", "thread_id", "body"],
    "slack.chat.postMessage":    ["channel", "text"],
    "slack.chat.scheduleMessage":["channel", "text"],
    "drive.files.create":        ["name"],
    "github.issues.create":      ["title"],
    "notion.pages.create":       ["title"],
    "stripe.payment.create":     ["amount", "currency"],
}

# OAuth-requiring providers
_OAUTH_PROVIDERS: Set[str] = {
    "gmail", "google_gmail", "google_drive", "drive",
    "google_sheets", "sheets", "slack", "github",
    "stripe", "notion", "hubspot", "salesforce",
    "dropbox", "onedrive",
}

# Valid trigger types
_VALID_TRIGGER_TYPES: Set[str] = {
    "manual", "schedule", "webhook",
    "github", "gmail", "stripe", "custom",
}


class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    confidence: float = 1.0


class WorkflowValidator:
    """
    Sprint AI-9: Enterprise Workflow Pre-Execution Validator.

    Checks:
      1. Trigger presence & type validity
      2. Node integrity (IDs, duplicates, missing fields)
      3. Unknown / unsupported connectors
      4. Unsupported operations
      5. Required parameter completeness (only when params dict is explicitly provided)
      6. OAuth authentication metadata warnings
      7. Edge integrity (source/target existence, duplicate IDs)
      8. Cycle detection (DFS-based, DAG violation)
      9. Expression & variable syntax ({{ }} balance, $node references)
     10. Dangling nodes (nodes with no edges in a multi-node graph)

    Returns a structured ValidationResult.
    Execution is BLOCKED if is_valid=False.
    """

    # -----------------------------------------------------------------------
    # Public entry point
    # -----------------------------------------------------------------------

    def validate_workflow(self, workflow_graph: Dict[str, Any]) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        suggestions: List[str] = []

        nodes = workflow_graph.get("nodes") or []
        edges = workflow_graph.get("edges") or []
        trigger = workflow_graph.get("trigger")

        # ── 1. Trigger ──────────────────────────────────────────────────────
        trigger_errors = self._check_trigger(trigger)
        errors.extend(trigger_errors)

        # ── 2. Empty workflow ────────────────────────────────────────────────
        if not nodes:
            errors.append("Workflow contains no execution nodes.")
            return ValidationResult(is_valid=False, errors=errors, confidence=0.0)

        # ── 3. Node validation ───────────────────────────────────────────────
        node_ids, node_errors, node_warnings = self._check_nodes(nodes, workflow_graph)
        errors.extend(node_errors)
        warnings.extend(node_warnings)

        # ── 4. Edge validation ───────────────────────────────────────────────
        adj_list, edge_errors = self._check_edges(edges, node_ids)
        errors.extend(edge_errors)

        # ── 5. Cycle detection ───────────────────────────────────────────────
        cycle_errors = self._check_cycles(node_ids, adj_list)
        errors.extend(cycle_errors)

        # ── 6. Expression syntax ─────────────────────────────────────────────
        expr_errors = self._check_expressions(nodes, node_ids)
        errors.extend(expr_errors)

        # ── 7. Dangling nodes (optional suggestions) ─────────────────────────
        if len(nodes) > 1:
            dangling = self._find_dangling_nodes(node_ids, edges)
            for dn in dangling:
                suggestions.append(
                    f"Node '{dn}' has no connections. Consider linking it into the workflow."
                )

        # ── 8. Final result ──────────────────────────────────────────────────
        is_valid = len(errors) == 0
        confidence = 1.0 if is_valid and not warnings else (0.85 if is_valid else 0.0)

        logger.info(
            f"[AI-9] Validation complete: valid={is_valid} errors={len(errors)} "
            f"warnings={len(warnings)} confidence={confidence}"
        )

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            confidence=confidence,
        )

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _check_trigger(self, trigger: Optional[Dict[str, Any]]) -> List[str]:
        errors: List[str] = []
        if not trigger or not trigger.get("type"):
            errors.append(
                "Workflow missing mandatory trigger (Manual, Schedule, GitHub, Gmail, or Webhook)."
            )
            return errors
        ttype = trigger["type"].lower()
        if ttype not in _VALID_TRIGGER_TYPES:
            errors.append(
                f"Unknown trigger type '{trigger['type']}'. "
                f"Supported: {sorted(t.title() for t in _VALID_TRIGGER_TYPES)}"
            )
        return errors

    def _normalize_provider(self, provider: str) -> str:
        """Normalise provider strings to lowercase slug."""
        return provider.lower().replace(" ", "_")

    def _is_known_provider(self, provider: str) -> bool:
        """Return True if provider is known/registered."""
        slug = self._normalize_provider(provider)
        # 1. Check internal known set
        if slug in _KNOWN_PROVIDERS:
            return True
        # 2. Check connector registry (flexible)
        try:
            if connector_registry.has(provider):
                return True
            # Try slug variant
            if connector_registry.has(slug):
                return True
        except Exception:
            pass
        return False

    def _check_nodes(
        self, nodes: List[Dict[str, Any]], workflow_graph: Optional[Dict[str, Any]] = None
    ) -> Tuple[Set[str], List[str], List[str]]:
        workflow_graph = workflow_graph or {}
        errors: List[str] = []
        warnings: List[str] = []
        node_ids: Set[str] = set()

        for node in nodes:
            nid = node.get("id") or node.get("step_id") or ""
            provider = node.get("provider") or ""
            op_id = node.get("operation") or node.get("operation_id") or ""
            auth = node.get("authentication")
            # Only validate params when the node explicitly carries a params dict
            slug = self._normalize_provider(provider) if provider else ""
            op_schema = None
            params: Optional[Dict] = node.get("parameters")

            # ── ID checks ───────────────────────────────────────────────────
            if not nid:
                errors.append("Node missing required 'id' attribute.")
            elif nid in node_ids:
                errors.append(f"Duplicate node ID detected: '{nid}'.")
            else:
                node_ids.add(nid)

            # ── Provider checks ─────────────────────────────────────────────
            if provider:
                if not self._is_known_provider(provider):
                    errors.append(
                        f"Unknown connector provider '{provider}' in node '{nid}'. "
                        f"Please register it in the Connector Registry."
                    )

            # ── Operation checks ─────────────────────────────────────────────
            if op_id and provider:
                # Skip operation validation for non-API providers
                if slug not in ("schedule", "scheduler", "ai", "openai", "gemini", "webhook", "condition", "if", "switch", "loop", "iterator"):
                    try:
                        op_schema = connector_registry.get_operation_schema(provider, op_id)
                    except Exception:
                        pass

                    if op_schema is None:
                        # Unsupported operation — check against known op list
                        warnings.append(
                            f"Operation '{op_id}' in node '{nid}' not found in registry schema."
                        )
                    else:
                        # Required params — only enforce if params dict was explicitly provided
                        if params is not None:
                            for p in op_schema.required_parameters:
                                val = params.get(p.name)
                                if val is None or val == "" or val == "missing":
                                    # Template references count as provided
                                    if not isinstance(val, str) or "{{" not in str(val):
                                        errors.append(
                                            f"Required parameter '{p.name}' missing for node '{nid}' "
                                            f"({provider} -> {op_id})."
                                        )

            # ── AI-23: Condition Node Validation ─────────────────────────────
            if op_id == "condition.if" or slug in ("condition", "if") or op_id.startswith("condition."):
                if params is not None:
                    raw_op = str(params.get("operator") or "").lower().strip().replace(" ", "_")
                    valid_ops = {
                        "equals", "equal", "==", "not_equals", "not_equal", "!=",
                        "contains", "not_contains", "exists", "not_exists",
                        "starts_with", "startswith", "ends_with", "endswith",
                        "greater_than", "greaterthan", ">", "less_than", "lessthan", "<",
                        "greater_or_equal", "greater_equal", ">=", "less_or_equal", "less_equal", "<="
                    }
                    if raw_op and raw_op not in valid_ops:
                        errors.append(f"Invalid condition operator '{params.get('operator')}' in node '{nid}'.")

                    true_tgt = params.get("true_branch") or params.get("true_step_id")
                    false_tgt = params.get("false_branch") or params.get("false_step_id")
                    all_ids = {n.get("id") or n.get("step_id") for n in nodes if n.get("id") or n.get("step_id")}
                    if true_tgt and true_tgt not in all_ids:
                        errors.append(f"Condition node '{nid}' references non-existent true_branch target '{true_tgt}'.")
                    if false_tgt and false_tgt not in all_ids:
                        errors.append(f"Condition node '{nid}' references non-existent false_branch target '{false_tgt}'.")

            # ── Sprint AI-17: Gmail Search Validation Guard ─────────────────
            if op_id in ["gmail.messages.search", "gmail.messages.list"] and params is not None:
                q_val = str(params.get("q") or "").strip()
                noise_patterns = ["find email", "find emails", "search email", "search emails", "search for emails", "search my gmail", "search my email", "show me emails", "show emails", "look for emails", "get emails", "find unread emails"]
                prompt = workflow_graph.get("user_prompt") or workflow_graph.get("prompt") or ""
                if q_val and (q_val == prompt.strip() or any(p in q_val.lower() for p in noise_patterns)):
                    from app.agents.planner.gmail_search_query_builder import build_gmail_search_query
                    cleaned_q = build_gmail_search_query(q_val if q_val != prompt else prompt)
                    if cleaned_q and not any(p in cleaned_q.lower() for p in noise_patterns) and cleaned_q != prompt:
                        params["q"] = cleaned_q
                    else:
                        logger.error(f"[AI-17][SEARCH_QUERY_ERROR] Unable to convert natural-language search request into Gmail query: '{q_val}'")
                        errors.append(f"Invalid Gmail search query parameter 'q' in node '{nid}': Search query must be in Gmail syntax (e.g. from:user@example.com), not natural language ('{q_val}').")
                logger.info(f"[AI-17.1][VALIDATED_QUERY] step={nid} op={op_id} q='{params.get('q')}'")

            # ── Fallback required-param check (when no registry schema) ─────
            # Only fires when params dict explicitly provided AND has values
            if params is not None and op_id in _REQUIRED_PARAMS:
                for req_param in _REQUIRED_PARAMS[op_id]:
                    val = params.get(req_param)
                    if val is None:
                        # Only flag if no template reference exists anywhere in params
                        has_template = any(
                            isinstance(v, str) and "{{" in v
                            for v in params.values()
                        )
                        if not has_template:
                            errors.append(
                                f"Required parameter '{req_param}' missing for node '{nid}' "
                                f"({provider} -> {op_id})."
                            )

            # ── AI-14: Placeholder message_id guard ────────────────────────
            if op_id == "gmail.messages.get" and params is not None:
                msg_id = params.get("message_id")
                if not msg_id or msg_id == "Gmail message unique ID" or "unique ID" in str(msg_id):
                    errors.append(
                        f"Node '{nid}' (gmail.messages.get) contains invalid/unresolved message_id: '{msg_id}'."
                    )

            # ── AI-14: Side-Effect Guard for Read-Only / Search Intents ─────
            intent_val = str(workflow_graph.get("intent") or "").upper()
            title_val = str(workflow_graph.get("title") or "").lower()
            explicitly_allowed = any(w in title_val for w in ["email the summary", "send the summary", "send email summary", "email me", "mail to"])

            is_read_only_intent = (
                "READ" in intent_val or "SEARCH" in intent_val or "SUMMARIZE" in intent_val
            ) and not (
                "SEND" in intent_val or "REPLY" in intent_val or "FORWARD" in intent_val or 
                "DELETE" in intent_val or "MODIFY" in intent_val or "SCHEDULE" in intent_val or 
                explicitly_allowed
            )

            forbidden_side_effects = {
                "gmail.messages.send", "gmail.messages.reply", "gmail.messages.forward",
                "gmail.messages.delete", "gmail.messages.mark_read", "gmail.messages.mark_unread",
                "gmail.drafts.create"
            }
            if is_read_only_intent and op_id in forbidden_side_effects:
                logger.info(f"[AI-14][SIDE_EFFECT_GUARD] blocked operation={op_id} in node={nid} reason=READ_ONLY_INTENT")
                errors.append(
                    f"Side-effect operation '{op_id}' in node '{nid}' is forbidden for read-only/search intent '{intent_val}'."
                )

            # ── Auth warnings ────────────────────────────────────────────────
            if provider:
                slug = self._normalize_provider(provider)
                if slug in _OAUTH_PROVIDERS and not auth:
                    warnings.append(
                        f"Node '{nid}' ({provider}) missing explicit OAuth authentication metadata."
                    )

        logger.info(f"[AI-14][VALIDATION] node_count={len(nodes)} error_count={len(errors)} warning_count={len(warnings)}")
        return node_ids, errors, warnings

    def _check_edges(
        self, edges: List[Dict[str, Any]], node_ids: Set[str]
    ) -> Tuple[Dict[str, List[str]], List[str]]:
        errors: List[str] = []
        edge_ids: Set[str] = set()
        adj_list: Dict[str, List[str]] = {nid: [] for nid in node_ids}

        for edge in edges:
            eid = edge.get("id")
            source = edge.get("source")
            target = edge.get("target")

            if eid:
                if eid in edge_ids:
                    errors.append(f"Duplicate edge ID detected: '{eid}'.")
                edge_ids.add(eid)

            if source not in node_ids:
                errors.append(f"Edge source node '{source}' does not exist.")
            if target not in node_ids:
                errors.append(f"Edge target node '{target}' does not exist.")

            if source in adj_list and target in node_ids:
                adj_list[source].append(target)

        return adj_list, errors

    def _check_cycles(
        self, node_ids: Set[str], adj_list: Dict[str, List[str]]
    ) -> List[str]:
        errors: List[str] = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def _dfs(u: str) -> bool:
            visited.add(u)
            rec_stack.add(u)
            for v in adj_list.get(u, []):
                if v not in visited:
                    if _dfs(v):
                        return True
                elif v in rec_stack:
                    return True
            rec_stack.discard(u)
            return False

        for nid in node_ids:
            if nid not in visited:
                if _dfs(nid):
                    errors.append("Cycle detected in workflow graph (DAG violation).")
                    break

        return errors

    def _check_expressions(
        self, nodes: List[Dict[str, Any]], node_ids: Set[str]
    ) -> List[str]:
        errors: List[str] = []
        has_loop_node = any(
            "loop" in (node.get("provider") or "").lower() for node in nodes
        )

        for node in nodes:
            nid = node.get("id") or node.get("step_id") or "unknown"
            params = node.get("parameters") or {}
            for key, val in params.items():
                if not isinstance(val, str):
                    continue
                open_cnt = val.count("{{")
                close_cnt = val.count("}}")
                if open_cnt != close_cnt:
                    errors.append(
                        f"Invalid expression syntax in node '{nid}' "
                        f"parameter '{key}': '{val}'."
                    )

                if "{{$loop.item" in val or "{{loop.item" in val:
                    if not has_loop_node:
                        errors.append(
                            f"Invalid variable reference '{val}' in node '{nid}': "
                            f"No preceding Loop node in workflow."
                        )

                node_refs = re.findall(r'\{\{\$node\.([a-zA-Z0-9_-]+)', val)
                for ref_id in node_refs:
                    if ref_id not in node_ids:
                        errors.append(
                            f"Invalid variable reference in node '{nid}': "
                            f"Referenced node '{ref_id}' does not exist."
                        )

        return errors

    def _find_dangling_nodes(
        self, node_ids: Set[str], edges: List[Dict[str, Any]]
    ) -> Set[str]:
        """Return node IDs with no incoming or outgoing edges."""
        connected: Set[str] = set()
        for edge in edges:
            src = edge.get("source")
            tgt = edge.get("target")
            if src:
                connected.add(src)
            if tgt:
                connected.add(tgt)
        return node_ids - connected


workflow_validator = WorkflowValidator()
