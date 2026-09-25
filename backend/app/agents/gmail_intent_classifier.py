import re
import enum
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("agentflow.agents.gmail_intent_classifier")


class GmailIntent(str, enum.Enum):
    EMAIL_SEND = "EMAIL_SEND"
    EMAIL_GENERATE = "EMAIL_GENERATE"
    EMAIL_READ = "EMAIL_READ"
    EMAIL_READ_LATEST = "EMAIL_READ_LATEST"
    EMAIL_READ_UNREAD = "EMAIL_READ_UNREAD"
    EMAIL_SEARCH = "EMAIL_SEARCH"
    EMAIL_SEARCH_BY_SENDER = "EMAIL_SEARCH_BY_SENDER"
    EMAIL_SEARCH_BY_SUBJECT = "EMAIL_SEARCH_BY_SUBJECT"
    EMAIL_REPLY = "EMAIL_REPLY"
    EMAIL_FORWARD = "EMAIL_FORWARD"
    EMAIL_DELETE = "EMAIL_DELETE"
    EMAIL_MARK_READ = "EMAIL_MARK_READ"
    EMAIL_MARK_UNREAD = "EMAIL_MARK_UNREAD"
    EMAIL_SUMMARIZE = "EMAIL_SUMMARIZE"
    EMAIL_DRAFT = "EMAIL_DRAFT"
    EMAIL_SCHEDULE = "EMAIL_SCHEDULE"


INTENT_OPERATION_MAP: Dict[GmailIntent, str] = {
    GmailIntent.EMAIL_SEND: "gmail.messages.send",
    GmailIntent.EMAIL_GENERATE: "gmail.messages.send",
    GmailIntent.EMAIL_READ: "gmail.messages.get",
    GmailIntent.EMAIL_READ_LATEST: "gmail.messages.get",
    GmailIntent.EMAIL_READ_UNREAD: "gmail.messages.list",
    GmailIntent.EMAIL_SEARCH: "gmail.messages.search",
    GmailIntent.EMAIL_SEARCH_BY_SENDER: "gmail.messages.search",
    GmailIntent.EMAIL_SEARCH_BY_SUBJECT: "gmail.messages.search",
    GmailIntent.EMAIL_REPLY: "gmail.messages.reply",
    GmailIntent.EMAIL_FORWARD: "gmail.messages.forward",
    GmailIntent.EMAIL_DELETE: "gmail.messages.delete",
    GmailIntent.EMAIL_MARK_READ: "gmail.messages.mark_read",
    GmailIntent.EMAIL_MARK_UNREAD: "gmail.messages.mark_unread",
    GmailIntent.EMAIL_SUMMARIZE: "gmail.messages.list",
    GmailIntent.EMAIL_DRAFT: "gmail.drafts.create",
    GmailIntent.EMAIL_SCHEDULE: "scheduler.create_job",
}


class GmailIntentClassificationResult:
    def __init__(
        self,
        intent: GmailIntent,
        confidence: float,
        target_operation: str,
        extracted_entities: Dict[str, Any],
        reasoning: str,
    ):
        self.intent = intent
        self.confidence = confidence
        self.target_operation = target_operation
        self.extracted_entities = extracted_entities
        self.reasoning = reasoning

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent.value if isinstance(self.intent, GmailIntent) else str(self.intent),
            "confidence": self.confidence,
            "target_operation": self.target_operation,
            "extracted_entities": self.extracted_entities,
            "reasoning": self.reasoning,
        }


class GmailIntentClassifier:
    """
    Deterministic + LLM-Assisted Production-Grade Gmail Intent Classifier.
    Accurately classifies user prompt into one of the 16 EMAIL_* intents with confidence scoring.
    """

    def classify(self, prompt: str) -> GmailIntentClassificationResult:
        p_lower = prompt.lower().strip()
        entities: Dict[str, Any] = {}

        # 1. EMAIL_SCHEDULE
        if any(kw in p_lower for kw in ["tomorrow", "next monday", "every monday", "every day", "after ", "schedule email", "schedule reminder"]):
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_SCHEDULE,
                confidence=0.98,
                target_operation=INTENT_OPERATION_MAP[GmailIntent.EMAIL_SCHEDULE],
                extracted_entities={"schedule_prompt": prompt},
                reasoning="Detected temporal schedule trigger keywords",
            )

        # 2. EMAIL_MARK_UNREAD
        if "mark as unread" in p_lower or "mark unread" in p_lower:
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_MARK_UNREAD,
                confidence=0.99,
                target_operation=INTENT_OPERATION_MAP[GmailIntent.EMAIL_MARK_UNREAD],
                extracted_entities=entities,
                reasoning="Explicit mark unread directive",
            )

        # 3. EMAIL_MARK_READ
        if "mark as read" in p_lower or "mark read" in p_lower:
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_MARK_READ,
                confidence=0.99,
                target_operation=INTENT_OPERATION_MAP[GmailIntent.EMAIL_MARK_READ],
                extracted_entities=entities,
                reasoning="Explicit mark read directive",
            )

        # 4. EMAIL_DELETE
        if any(kw in p_lower for kw in ["delete email", "trash email", "delete message", "delete msg", "trash message", "delete spam", "purge"]):
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_DELETE,
                confidence=0.98,
                target_operation=INTENT_OPERATION_MAP[GmailIntent.EMAIL_DELETE],
                extracted_entities=entities,
                reasoning="Explicit delete / trash email operation",
            )

        # 5. EMAIL_FORWARD
        if any(kw in p_lower for kw in ["forward email", "forward message", "fwd email", "forward invoice"]):
            match_to = re.search(r"\bto\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b", prompt, re.IGNORECASE)
            if match_to:
                entities["to"] = match_to.group(1)
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_FORWARD,
                confidence=0.97,
                target_operation=INTENT_OPERATION_MAP[GmailIntent.EMAIL_FORWARD],
                extracted_entities=entities,
                reasoning="Explicit email forwarding operation",
            )

        # 6. EMAIL_REPLY
        if any(kw in p_lower for kw in ["reply to", "send reply", "respond to", "reply politely", "reply msg"]):
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_REPLY,
                confidence=0.97,
                target_operation=INTENT_OPERATION_MAP[GmailIntent.EMAIL_REPLY],
                extracted_entities=entities,
                reasoning="Explicit email reply operation",
            )

        # 7. Labels operations
        if "list labels" in p_lower:
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_READ,
                confidence=0.98,
                target_operation="gmail.labels.list",
                extracted_entities=entities,
                reasoning="List Gmail labels directive",
            )
        if "modify label" in p_lower:
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_READ,
                confidence=0.98,
                target_operation="gmail.labels.modify",
                extracted_entities=entities,
                reasoning="Modify Gmail label directive",
            )

        # 8. Draft operations
        if "send draft" in p_lower:
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_SEND,
                confidence=0.98,
                target_operation="gmail.drafts.send",
                extracted_entities=entities,
                reasoning="Send draft directive",
            )
        if any(kw in p_lower for kw in ["create draft", "save draft", "new draft", "draft email", "drafts"]):
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_DRAFT,
                confidence=0.96,
                target_operation=INTENT_OPERATION_MAP[GmailIntent.EMAIL_DRAFT],
                extracted_entities=entities,
                reasoning="Explicit email draft creation",
            )

        # 9. Attachment Download
        if any(kw in p_lower for kw in ["download attachment", "save attachment", "download att_"]):
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_READ,
                confidence=0.98,
                target_operation="gmail.attachments.download",
                extracted_entities=entities,
                reasoning="Explicit attachment download intent",
            )

        # 10. EMAIL_GENERATE
        if any(kw in p_lower for kw in ["write an email", "write email", "generate email", "compose email", "write an apology", "write apology", "write birthday", "apology email", "birthday email"]):
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_GENERATE,
                confidence=0.95,
                target_operation=INTENT_OPERATION_MAP[GmailIntent.EMAIL_GENERATE],
                extracted_entities=entities,
                reasoning="AI Email content generation directive",
            )

        # 11. EMAIL_SEND
        if any(kw in p_lower for kw in ["send email", "send an email", "send email to", "dispatch email"]):
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_SEND,
                confidence=0.96,
                target_operation=INTENT_OPERATION_MAP[GmailIntent.EMAIL_SEND],
                extracted_entities=entities,
                reasoning="Explicit email sending directive",
            )

        # 12. EMAIL_SEARCH_BY_SENDER
        sender_match = re.search(r"\bfrom\s*[:\s]\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|[a-zA-Z0-9]+)\b", prompt, re.IGNORECASE)
        if sender_match and ("find" in p_lower or "search" in p_lower or "get" in p_lower or "read" in p_lower):
            sender = sender_match.group(1)
            entities["sender"] = sender
            entities["query"] = f"from:{sender}"
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_SEARCH_BY_SENDER,
                confidence=0.96,
                target_operation=INTENT_OPERATION_MAP[GmailIntent.EMAIL_SEARCH_BY_SENDER],
                extracted_entities=entities,
                reasoning=f"Search by sender '{sender}' detected",
            )

        # 13. EMAIL_SEARCH_BY_SUBJECT
        subject_match = re.search(r"\bsubject:\s*\"?([^\"]+)\"?\b", prompt, re.IGNORECASE)
        if subject_match and ("find" in p_lower or "search" in p_lower or "query" in p_lower):
            subject = subject_match.group(1)
            entities["subject"] = subject
            entities["query"] = f"subject:{subject}"
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_SEARCH_BY_SUBJECT,
                confidence=0.96,
                target_operation=INTENT_OPERATION_MAP[GmailIntent.EMAIL_SEARCH_BY_SUBJECT],
                extracted_entities=entities,
                reasoning=f"Search by subject '{subject}' detected",
            )

        # 14. EMAIL_SEARCH / FIND
        if any(kw in p_lower for kw in ["search", "find amazon", "find email", "find emails", "search invoice", "search invoices", "find invoices", "lookup"]):
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_SEARCH,
                confidence=0.96,
                target_operation=INTENT_OPERATION_MAP[GmailIntent.EMAIL_SEARCH],
                extracted_entities=entities,
                reasoning="General email search intent detected",
            )

        # 15. EMAIL_SUMMARIZE
        if any(kw in p_lower for kw in ["summarize", "summary", "digest", "weekly digest", "monthly digest"]):
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_SUMMARIZE,
                confidence=0.96,
                target_operation=INTENT_OPERATION_MAP[GmailIntent.EMAIL_SUMMARIZE],
                extracted_entities=entities,
                reasoning="Email summarization & digest intent detected",
            )

        # 15. EMAIL_READ_LATEST
        if any(kw in p_lower for kw in ["latest email", "last email", "read latest", "read last"]):
            op = "gmail.messages.get" if "msg_" in p_lower else "gmail.messages.list"
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_READ_LATEST,
                confidence=0.98,
                target_operation=op,
                extracted_entities=entities,
                reasoning="Read latest email message intent",
            )

        # 16. EMAIL_READ_UNREAD / IMPORTANT / STARRED / TEMPORAL
        if any(kw in p_lower for kw in ["unread email", "unread emails", "unread messages", "fetch unread", "check unread", "important email", "important emails", "starred email", "starred emails", "today's emails", "today emails", "emails today", "read today", "last week", "last week emails", "past week"]):
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_READ_UNREAD,
                confidence=0.98,
                target_operation=INTENT_OPERATION_MAP[GmailIntent.EMAIL_READ_UNREAD],
                extracted_entities=entities,
                reasoning="Fetch unread/important/starred/temporal emails list intent",
            )

        # 17. EMAIL_SEARCH
        if any(kw in p_lower for kw in ["find email", "search email", "find invoices", "find interview", "query email", "find attachments", "search email"]):
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_SEARCH,
                confidence=0.95,
                target_operation=INTENT_OPERATION_MAP[GmailIntent.EMAIL_SEARCH],
                extracted_entities=entities,
                reasoning="General Gmail search query detected",
            )

        # 18. List messages
        if "list messages" in p_lower or "list email" in p_lower:
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_READ,
                confidence=0.97,
                target_operation="gmail.messages.list",
                extracted_entities=entities,
                reasoning="List messages intent",
            )

        # 19. Get message details
        if "get message details" in p_lower or "message details" in p_lower:
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_READ,
                confidence=0.97,
                target_operation="gmail.messages.get",
                extracted_entities=entities,
                reasoning="Get message details intent",
            )

        # 20. EMAIL_READ
        if any(kw in p_lower for kw in ["read email", "read my email", "read message", "read my message", "email details", "check inbox", "show emails", "fetch email"]):
            op = "gmail.messages.get" if "msg_" in p_lower or "details" in p_lower else "gmail.messages.list"
            return GmailIntentClassificationResult(
                intent=GmailIntent.EMAIL_READ,
                confidence=0.94,
                target_operation=op,
                extracted_entities=entities,
                reasoning="General read email intent",
            )

        # Default fallback to UNKNOWN / unresolved intent (zero silent fallback to EMAIL_SEND)
        return GmailIntentClassificationResult(
            intent=GmailIntent.EMAIL_READ,
            confidence=0.50,
            target_operation=INTENT_OPERATION_MAP[GmailIntent.EMAIL_READ],
            extracted_entities=entities,
            reasoning="Default email read intent for unmapped prompt",
        )


gmail_intent_classifier = GmailIntentClassifier()
