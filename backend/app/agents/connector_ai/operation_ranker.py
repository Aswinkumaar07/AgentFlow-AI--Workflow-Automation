import logging
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("agentflow.agents.connector_ai.ranker")


def _stem(w: str) -> str:
    w = w.lower()
    if w.endswith('ies') and len(w) > 4:
        return w[:-3] + 'y'
    if w.endswith('s') and not w.endswith('ss') and len(w) > 3:
        return w[:-1]
    return w


def _flatten_schema_props(schema: Dict[str, Any], prefix: str = "") -> List[Dict[str, Any]]:
    flattened = []
    if not isinstance(schema, dict):
        return flattened
    stype = schema.get("type", "object")
    if stype == "array" and "items" in schema and isinstance(schema["items"], dict):
        return _flatten_schema_props(schema["items"], prefix=prefix)
    props = schema.get("properties", {})
    if isinstance(props, dict):
        for prop_name, prop_def in props.items():
            path = f"{prefix}.{prop_name}" if prefix else prop_name
            p_type = prop_def.get("type", "string") if isinstance(prop_def, dict) else "string"
            flattened.append({
                "name": prop_name,
                "path": path,
                "type": p_type,
            })
            if p_type == "object" and isinstance(prop_def, dict) and "properties" in prop_def:
                flattened.extend(_flatten_schema_props(prop_def, prefix=path))
    return flattened


def _is_type_compatible(src_type: str, tgt_type: str) -> bool:
    if not src_type or not tgt_type:
        return True
    src = src_type.lower()
    tgt = tgt_type.lower()
    if src == tgt:
        return True
    if src in ["integer", "number"] and tgt in ["integer", "number", "string"]:
        return True
    if src == "string" and tgt in ["string", "integer", "number"]:
        return True
    return False


def _compute_parameter_compatibility(item: Dict[str, Any], upstream_response_schema: Optional[Dict[str, Any]]) -> float:
    if not upstream_response_schema or not isinstance(upstream_response_schema, dict):
        return 0.0

    upstream_props = _flatten_schema_props(upstream_response_schema)
    if not upstream_props:
        return 0.0

    params_dict = item.get("parameters", {})
    url = params_dict.get("url", "") if isinstance(params_dict, dict) else ""
    path_params = re.findall(r"\{([a-zA-Z0-9_]+)\}", url) if url else []

    if path_params:
        all_path_matched = True
        for p_name in path_params:
            matched_prop = None
            p_norm = p_name.lower().replace("-", "").replace("_", "")
            for up in upstream_props:
                uname = up["name"]
                unorm = uname.lower().replace("-", "").replace("_", "")
                if uname == p_name or unorm == p_norm or (p_norm.endswith("id") and uname.lower() == "id") or (unorm.endswith("id") and p_norm == unorm):
                    if _is_type_compatible(up["type"], "integer"):
                        matched_prop = up
                        break
            if not matched_prop:
                all_path_matched = False
                break

        if all_path_matched:
            return 1.0

    return 0.0


class OperationResult(BaseModel):
    provider: str
    operation: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    request_schema: Dict[str, Any] = Field(default_factory=dict)
    response_schema: Dict[str, Any] = Field(default_factory=dict)
    optional_params: List[str] = Field(default_factory=list)
    query_params: List[str] = Field(default_factory=list)
    header_params: List[str] = Field(default_factory=list)
    security_schemes: Dict[str, Any] = Field(default_factory=dict)
    security_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    authentication: str = "OAuth2"
    confidence: float = 0.95


class OperationRanker:
    """Dynamic Operation Discovery and Ranking Engine over Connector operation catalog."""

    OPERATION_CATALOG: List[Dict[str, Any]] = [
        {
            "provider": "Gmail",
            "operation": "gmail.messages.send",
            "summary": "Send email message to recipient with subject and body",
            "parameters": {"to": "{{recipient_email}}", "subject": "Notice", "body": "Hello"},
            "authentication": "OAuth2",
            "keywords": ["send email", "email", "gmail send", "mail", "send message", "good morning"],
        },
        {
            "provider": "Gmail",
            "operation": "gmail.messages.list",
            "summary": "List or watch email messages matching query label",
            "parameters": {"query": "label:invoices"},
            "authentication": "OAuth2",
            "keywords": ["read email", "list messages", "gmail watch", "invoice", "unread", "summarize unread"],
        },
        {
            "provider": "Slack",
            "operation": "slack.chat.postMessage",
            "summary": "Post notification message to target Slack channel",
            "parameters": {"channel": "#dev-alerts", "text": "Notification"},
            "authentication": "OAuth2",
            "keywords": ["slack", "post message", "notify channel", "slack alert", "notify slack"],
        },
        {
            "provider": "Google Sheets",
            "operation": "sheets.spreadsheets.values.get",
            "summary": "Read rows and data range from target Google Sheet",
            "parameters": {"spreadsheet_id": "sheet_employees", "range": "Sheet1!A1:Z"},
            "authentication": "OAuth2",
            "keywords": ["sheets", "read rows", "spreadsheet", "read employees", "google sheets employees"],
        },
        {
            "provider": "Google Drive",
            "operation": "drive.files.create",
            "summary": "Upload file or create file in target Google Drive folder",
            "parameters": {"folder": "Invoices", "file_name": "document.pdf"},
            "authentication": "OAuth2",
            "keywords": ["drive", "upload file", "create file", "save to drive", "backup google drive"],
        },
        {
            "provider": "GitHub",
            "operation": "github.pulls.list",
            "summary": "Fetch pull requests or list open PRs for repository",
            "parameters": {"owner": "AgentFlow-AI", "repo": "TERRAWATCH"},
            "authentication": "OAuth2",
            "keywords": ["github", "pull request", "pr", "list prs", "github pr"],
        },
        {
            "provider": "GitHub",
            "operation": "github.issues.get",
            "summary": "Fetch or receive newly created GitHub issue",
            "parameters": {"owner": "AgentFlow-AI", "repo": "TERRAWATCH"},
            "authentication": "OAuth2",
            "keywords": ["github issue", "issue", "github issues"],
        },
        {
            "provider": "Stripe",
            "operation": "stripe.charges.get",
            "summary": "Retrieve Stripe payment intent or charge details",
            "parameters": {"charge_id": "ch_9921"},
            "authentication": "APIKey",
            "keywords": ["stripe", "stripe payment", "charge", "payment"],
        },
        {
            "provider": "Notion",
            "operation": "notion.pages.create",
            "summary": "Create new page or item in Notion workspace database",
            "parameters": {"parent_database": "Issues", "title": "{{step_1.title}}"},
            "authentication": "OAuth2",
            "keywords": ["notion", "create page", "notion page"],
        },
        {
            "provider": "AI",
            "operation": "ai.summarize",
            "summary": "Summarize text or document using LLM AI model",
            "parameters": {"text": "{{trigger_payload.body}}", "max_tokens": 200},
            "authentication": "APIKey",
            "keywords": ["ai", "summarize", "gpt", "gemini", "text summarizer"],
        },
        {
            "provider": "Condition",
            "operation": "condition.evaluate",
            "summary": "Evaluate conditional expression left_value vs right_value",
            "parameters": {"left_value": "{{$loop.item.name}}", "operator": "Ends With", "right_value": ".pdf"},
            "authentication": "None",
            "keywords": ["condition", "if", "check if", "greater than", "equals"],
        },
        {
            "provider": "Loop",
            "operation": "loop.process",
            "summary": "Loop and iterate over items in collection",
            "parameters": {"collection": "{{step_1.values}}"},
            "authentication": "None",
            "keywords": ["loop", "for each", "iterate", "loop attachments"],
        },
        {
            "provider": "Merge",
            "operation": "merge.process",
            "summary": "Wait for all parallel branches and merge results",
            "parameters": {"mode": "Wait All"},
            "authentication": "None",
            "keywords": ["merge", "combine", "wait all"],
        },
        {
            "provider": "Generic REST",
            "operation": "generic.http.request",
            "summary": "Make arbitrary HTTP REST request to target endpoint URL",
            "parameters": {"url": "https://api.example.com", "method": "GET"},
            "authentication": "APIKey",
            "keywords": ["http", "api", "rest", "fetch url"],
        },
    ]

    def rank_operations(
        self,
        query: str,
        target_provider: Optional[str] = None,
        top_k: int = 5,
        upstream_response_schema: Optional[Dict[str, Any]] = None,
    ) -> List[OperationResult]:
        """Discovers and ranks candidate operations for a target query and optional provider filter."""
        q_lower = query.lower()
        query_words = re.findall(r'[a-zA-Z0-9]+', q_lower)
        query_tokens = set(query_words)
        query_stems = {_stem(w) for w in query_words if len(w) > 1}

        # Action Verb Intent Flags
        is_get = any(w in query_stems for w in ["get", "fetch", "find", "list", "read", "show", "search", "lookup"])
        is_create = any(w in query_stems for w in ["create", "add", "new", "post", "make", "insert", "place"])
        is_update = any(w in query_stems for w in ["update", "edit", "modify", "put", "change"])
        is_delete = any(w in query_stems for w in ["delete", "remove", "trash", "purge", "destroy", "cancel"])

        NATIVE_PROVIDERS = {"gmail", "slack", "google sheets", "google drive", "github", "stripe", "notion", "ai", "condition", "loop", "merge", "generic rest"}

        results: List[Any] = []

        for item in self.OPERATION_CATALOG:
            provider = item["provider"]
            if target_provider and provider.lower() != target_provider.lower():
                continue

            op_id = item["operation"]
            keywords = item["keywords"]

            is_dynamic_op = (provider.lower() not in NATIVE_PROVIDERS) or any(k in ["get", "post", "put", "delete", "patch"] for k in keywords)

            if not is_dynamic_op:
                # ── Native Connector Scoring ──
                match_count = 0
                for k in keywords:
                    k_lower = k.lower()
                    if " " in k_lower:
                        if k_lower in q_lower:
                            match_count += 1
                    else:
                        if k_lower in query_tokens or k_lower in query_stems or (len(k_lower) > 2 and _stem(k_lower) in query_stems):
                            match_count += 1

                score = 0.5 + (match_count * 0.15)
                confidence = min(0.99, max(0.40, score))
            else:
                # ── Dynamic OpenAPI Semantic Scoring ──
                op_id_tokens = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', op_id).lower().replace('_', ' ').split()
                op_id_stems = {_stem(w) for w in op_id_tokens}

                # Extract HTTP Method
                http_method = ""
                for m in ["get", "post", "put", "delete", "patch"]:
                    if m in keywords:
                        http_method = m.upper()
                        break

                # Extract Resource Entity Tokens
                op_resource_stems = {
                    _stem(w) for w in op_id_tokens + keywords
                    if len(w) > 2 and w.lower() not in ["get", "post", "put", "delete", "patch", "by", "with", "input", "list", "array", "form", "api", "rest", "openapi", "swagger"]
                }

                # 1. Resource Entity Match vs Mismatch
                resource_matched = False
                resource_mismatched = False
                known_resources = ["user", "pet", "order", "inventory", "customer", "account", "product", "ticket", "issue", "file"]
                query_resources = {q_stem for q_stem in query_stems if q_stem in known_resources}

                for q_r in query_resources:
                    if q_r in op_resource_stems:
                        resource_matched = True
                        break

                if query_resources and not resource_matched:
                    resource_mismatched = True

                # 2. Action Verb & HTTP Method Alignment
                action_matched = False
                if is_delete and (http_method == "DELETE" or "delete" in op_id_stems):
                    action_matched = True
                elif is_create and (http_method == "POST" or "create" in op_id_stems or "add" in op_id_stems or "place" in op_id_stems):
                    action_matched = True
                elif is_update and (http_method in ["PUT", "PATCH"] or "update" in op_id_stems or "edit" in op_id_stems):
                    action_matched = True
                elif is_get and (http_method == "GET" or "get" in op_id_stems or "find" in op_id_stems or "list" in op_id_stems):
                    action_matched = True

                # 3. Specific Modifier & Endpoint Sibling Disambiguation
                modifier_score = 0.0
                if any(w in query_stems for w in ["name", "named"]) and any(w in op_id_stems or w in keywords for w in ["name", "username"]):
                    modifier_score += 0.20
                if "id" in query_tokens and ("id" in op_id_stems or "id" in keywords or any(w.endswith("id") for w in op_id_stems)):
                    modifier_score += 0.15

                # Single vs Batch Endpoint (e.g., createUser vs createUsersWithListInput)
                if not any(w in query_stems for w in ["list", "batch", "array", "bulk", "many", "multiple"]) and any(w in op_id_stems for w in ["list", "input", "array", "batch", "bulk"]):
                    modifier_score -= 0.25

                # 4. Keyword Token Overlap Count
                token_matches = 0
                for k in keywords:
                    k_lower = k.lower()
                    if k_lower in query_tokens or k_lower in query_stems or (len(k_lower) > 2 and _stem(k_lower) in query_stems):
                        token_matches += 1

                # 5. Composite Score Assembly
                score = 0.40
                if resource_matched:
                    score += 0.35
                elif resource_mismatched:
                    score -= 0.30

                if action_matched:
                    score += 0.25

                score += modifier_score
                score += (token_matches * 0.05)

                confidence = min(0.99, max(0.30, score))

            param_compat = 0.0
            if upstream_response_schema and isinstance(upstream_response_schema, dict):
                param_compat = _compute_parameter_compatibility(item, upstream_response_schema)

            results.append(
                (
                    round(confidence, 2),
                    round(score, 3),
                    round(param_compat, 2),
                    OperationResult(
                        provider=provider,
                        operation=item["operation"],
                        parameters=item["parameters"],
                        request_schema=item.get("request_schema", {}),
                        response_schema=item.get("response_schema", {}),
                        optional_params=item.get("optional_params", []),
                        query_params=item.get("query_params", []),
                        header_params=item.get("header_params", []),
                        security_schemes=item.get("security_schemes", {}),
                        security_requirements=item.get("security_requirements", []),
                        authentication=item["authentication"],
                        confidence=round(confidence, 2),
                    )
                )
            )

        results.sort(key=lambda r: (r[0], r[1], r[2]), reverse=True)
        return [r[3] for r in results[:top_k]]


operation_ranker = OperationRanker()
