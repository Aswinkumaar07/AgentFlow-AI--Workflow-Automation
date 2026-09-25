import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("agentflow.agents.connector_ai.ranker")


class OperationResult(BaseModel):
    provider: str
    operation: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
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
        self, query: str, target_provider: Optional[str] = None, top_k: int = 5
    ) -> List[OperationResult]:
        """Discovers and ranks candidate operations for a target query and optional provider filter."""
        q_lower = query.lower()
        results: List[OperationResult] = []

        for item in self.OPERATION_CATALOG:
            provider = item["provider"]
            if target_provider and provider.lower() != target_provider.lower():
                continue

            keywords = item["keywords"]
            match_count = sum(1 for k in keywords if k in q_lower)
            score = 0.5 + (match_count * 0.15)
            confidence = min(0.99, max(0.40, score))

            results.append(
                OperationResult(
                    provider=provider,
                    operation=item["operation"],
                    parameters=item["parameters"],
                    authentication=item["authentication"],
                    confidence=round(confidence, 2),
                )
            )

        results.sort(key=lambda r: r.confidence, reverse=True)
        return results[:top_k]


operation_ranker = OperationRanker()
