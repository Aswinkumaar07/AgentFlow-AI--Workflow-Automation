import math
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("agentflow.agents.connector_ai.selector")


class ConnectorCandidate(BaseModel):
    provider: str
    category: str
    capabilities: List[str]
    authentication: str
    confidence: float


class ConnectorSelector:
    """Semantic Connector Search Engine using vector/embedding similarity over connector metadata."""

    CONNECTOR_CATALOG: List[Dict[str, Any]] = [
        {
            "provider": "Gmail",
            "category": "Communication",
            "capabilities": ["send email", "read email", "list messages", "watch mailbox", "attachments"],
            "authentication": "OAuth2",
            "keywords": ["gmail", "email", "mail", "inbox", "message", "good morning", "customer", "invoice", "unread"],
        },
        {
            "provider": "Slack",
            "category": "Communication",
            "capabilities": ["send message", "post channel alert", "upload file", "read channels"],
            "authentication": "OAuth2",
            "keywords": ["slack", "notify", "alert", "channel", "#engineering", "#general", "#dev-alerts", "#finance-alerts", "message", "report"],
        },
        {
            "provider": "Google Sheets",
            "category": "Productivity",
            "capabilities": ["read rows", "append rows", "update rows", "read employees", "spreadsheet"],
            "authentication": "OAuth2",
            "keywords": ["sheets", "google sheets", "spreadsheet", "excel", "table", "rows", "employees"],
        },
        {
            "provider": "Google Drive",
            "category": "Storage",
            "capabilities": ["upload file", "download file", "create folder", "search files", "backup"],
            "authentication": "OAuth2",
            "keywords": ["drive", "google drive", "upload", "file", "save file", "pdf", "storage", "backup", "nightly"],
        },
        {
            "provider": "GitHub",
            "category": "Developer Tools",
            "capabilities": ["list pull requests", "create issue", "get issue", "commits", "webhooks"],
            "authentication": "OAuth2",
            "keywords": ["github", "pr", "pull request", "issue", "issues", "commit", "repository", "code"],
        },
        {
            "provider": "Stripe",
            "category": "Payments",
            "capabilities": ["process payment", "get charge", "refund charge", "list invoices"],
            "authentication": "APIKey",
            "keywords": ["stripe", "payment", "charge", "refund", "paid", "stripe payment"],
        },
        {
            "provider": "Notion",
            "category": "Productivity",
            "capabilities": ["create page", "update database", "query database"],
            "authentication": "OAuth2",
            "keywords": ["notion", "page", "database", "notion page", "workspace"],
        },
        {
            "provider": "AI",
            "category": "Artificial Intelligence",
            "capabilities": ["summarize text", "generate text", "extract entities", "sentiment analysis"],
            "authentication": "APIKey",
            "keywords": ["ai", "summarize", "gpt", "gemini", "openai", "text summarizer", "llm"],
        },
        {
            "provider": "Webhook",
            "category": "Triggers",
            "capabilities": ["http webhook trigger", "receive payload", "post listener"],
            "authentication": "WebhookSecret",
            "keywords": ["webhook", "http trigger", "incoming request", "api listener"],
        },
        {
            "provider": "Schedule",
            "category": "Triggers",
            "capabilities": ["cron schedule", "interval timer", "recurring trigger"],
            "authentication": "None",
            "keywords": ["schedule", "cron", "daily", "monday", "every", "morning", "weekly", "timer", "weekday", "8am", "night"],
        },
        {
            "provider": "Condition",
            "category": "Logic",
            "capabilities": ["if else branch", "evaluate comparison", "equals", "greater than", "contains"],
            "authentication": "None",
            "keywords": ["condition", "if", "check if", "greater than", "equals", "branch", "pdf"],
        },
        {
            "provider": "Loop",
            "category": "Control Flow",
            "capabilities": ["for each collection", "loop over items", "iterate rows"],
            "authentication": "None",
            "keywords": ["loop", "for each", "iterate", "every employee", "attachments", "rows", "loop over"],
        },
        {
            "provider": "Merge",
            "category": "Control Flow",
            "capabilities": ["wait all branches", "merge loop results", "combine outputs"],
            "authentication": "None",
            "keywords": ["merge", "combine", "wait all", "aggregate", "loop over", "loop"],
        },
        {
            "provider": "Approval",
            "category": "Human-in-the-Loop",
            "capabilities": ["human approval", "wait for manager", "approve action"],
            "authentication": "None",
            "keywords": ["approval", "approve", "manager", "human"],
        },
        {
            "provider": "Generic REST",
            "category": "HTTP",
            "capabilities": ["generic http get", "http post", "rest request"],
            "authentication": "APIKey",
            "keywords": ["http", "api", "rest", "fetch url", "endpoint"],
        },
    ]

    def _compute_embedding_similarity(self, text1: str, text2: str) -> float:
        """Computes word overlap and frequency vector similarity."""
        w1 = set(text1.lower().split())
        w2 = set(text2.lower().split())
        if not w1 or not w2:
            return 0.0
        intersection = w1.intersection(w2)
        union = w1.union(w2)
        return len(intersection) / len(union)

    def select_connectors(self, query: str, top_k: int = 5) -> List[ConnectorCandidate]:
        """Semantically selects matching connectors from catalog for a given query prompt."""
        q_lower = query.lower()
        candidates: List[ConnectorCandidate] = []

        for item in self.CONNECTOR_CATALOG:
            provider = item["provider"]
            keywords = item["keywords"]

            match_count = sum(1 for k in keywords if k in q_lower)
            sim_score = self._compute_embedding_similarity(query, " ".join(keywords + item["capabilities"]))

            raw_score = (match_count * 0.3) + (sim_score * 0.7)
            confidence = min(0.99, max(0.40, raw_score))

            if match_count > 0 or sim_score > 0.05:
                candidates.append(
                    ConnectorCandidate(
                        provider=provider,
                        category=item["category"],
                        capabilities=item["capabilities"],
                        authentication=item["authentication"],
                        confidence=round(confidence, 2),
                    )
                )

        candidates.sort(key=lambda c: c.confidence, reverse=True)
        return candidates[:top_k]


connector_selector = ConnectorSelector()
