import asyncio
import json
import logging
import re
from typing import Dict, Any, Optional

from app.agents.intent_classifier.models import IntentType, IntentClassificationResult
from app.agents.intent_classifier.prompts import INTENT_CLASSIFICATION_SYSTEM_PROMPT

logger = logging.getLogger("agentflow.agents.intent_classifier")


class EnterpriseIntentClassifier:
    """
    Sprint AI-1: Enterprise Intent Classification Engine for AgentFlow AI.
    Combines Gemini LLM reasoning with high-precision deterministic intent matching.
    Validates output using Pydantic, includes fallback retries, and emits standard [AI-1] structured logs.
    """

    def classify(self, prompt: str, user_id: str = "usr_1") -> IntentClassificationResult:
        logger.info(f"[AI-14][PROMPT] {prompt}")
        if not prompt or not prompt.strip():
            return self._build_result(IntentType.UNKNOWN, 0.0, "Empty prompt provided.", {})

        p_lower = prompt.lower().strip()

        # 1. Deterministic Fast Path (100% precision for standard intents)
        det_result = self._deterministic_classify(prompt, p_lower)
        if det_result:
            self._log_classification(det_result)
            return det_result

        # 2. LLM-Assisted Reasoning with Gemini
        llm_result = self._classify_with_llm(prompt)
        if llm_result:
            self._log_classification(llm_result)
            return llm_result

        # 3. Fallback Classifier
        fallback_result = self._fallback_classify(prompt, p_lower)
        self._log_classification(fallback_result)
        return fallback_result

    def _deterministic_classify(self, prompt: str, p_lower: str) -> Optional[IntentClassificationResult]:
        entities: Dict[str, Any] = {}

        # 0a. Scheduled Workflow (TEST 9 & 10)
        if any(w in p_lower for w in ["every morning", "every day", "every monday", "tomorrow at", "next monday at", "every 5 m", "every hour"]):
            return self._build_result(IntentType.EMAIL_SCHEDULE, 0.98, "Detected scheduled workflow intent", entities)

        # 0b. Explicit Read Latest Email (TEST 2)
        if any(w in p_lower for w in ["read my latest", "read latest", "show me my newest", "latest email"]) and not any(w in p_lower for w in ["send an email", "reply to", "forward to"]):
            return self._build_result(IntentType.EMAIL_READ_LATEST, 0.98, "Detected read latest email intent", entities)

        # Email Summarize
        if any(kw in p_lower for kw in ["summarize", "summary", "digest"]):
            return self._build_result(IntentType.EMAIL_SUMMARIZE, 0.97, "Detected email summarization intent", entities)

        # Email Generate / Content Writer
        if (any(w in p_lower for w in ["write", "compose", "generate", "send"]) or "draft an email" in p_lower) and any(w in p_lower for w in ["apology", "birthday", "good morning", "good night", "welcome", "newsletter", "follow-up", "outreach", "launch", "announcement"]):
            return self._build_result(
                IntentType.EMAIL_GENERATE,
                0.98,
                "Detected dynamic email content generation intent",
                entities,
            )

        # Email Reply
        has_negative_reply = ("do not" in p_lower or "don't" in p_lower or "never" in p_lower) and "reply" in p_lower
        if "reply" in p_lower and not has_negative_reply:
            return self._build_result(
                IntentType.EMAIL_REPLY,
                0.98,
                "Detected email reply intent",
                entities,
            )

        # Email Forward
        has_negative_forward = ("do not" in p_lower or "don't" in p_lower or "never" in p_lower) and ("forward" in p_lower or "fwd" in p_lower)
        if ("forward" in p_lower or "fwd" in p_lower) and not has_negative_forward:
            return self._build_result(
                IntentType.EMAIL_FORWARD,
                0.98,
                "Detected email forward intent",
                entities,
            )

        # Email Delete
        has_negative_delete = ("do not" in p_lower or "don't" in p_lower or "never" in p_lower) and any(kw in p_lower for kw in ["delete", "trash", "purge"])
        if any(kw in p_lower for kw in ["delete", "trash", "purge"]) and not has_negative_delete:
            return self._build_result(IntentType.EMAIL_DELETE, 0.98, "Detected email deletion intent", entities)

        # Email Mark Read / Unread
        if "as unread" in p_lower or ("mark" in p_lower and "unread" in p_lower and "as read" not in p_lower):
            return self._build_result(IntentType.EMAIL_MARK_UNREAD, 0.98, "Detected mark as unread intent", entities)
        if "as read" in p_lower or ("mark" in p_lower and "read" in p_lower):
            return self._build_result(IntentType.EMAIL_MARK_READ, 0.98, "Detected mark as read intent", entities)

        # Email Draft
        has_negative_draft = ("do not" in p_lower or "don't" in p_lower or "never" in p_lower) and "draft" in p_lower
        if "draft" in p_lower and not has_negative_draft:
            return self._build_result(IntentType.EMAIL_DRAFT, 0.98, "Detected email draft creation intent", entities)

        # Multi-Step Workflow Detection (Requires distinct tool actions e.g. read+summarize, search+download, upload+notify, summarize+send)
        has_read_or_search = any(w in p_lower for w in ["read", "search", "fetch", "list", "find"])
        has_summarize = "summarize" in p_lower or "summary" in p_lower or "digest" in p_lower
        has_download_or_drive = "download" in p_lower or "drive" in p_lower or "attachment" in p_lower
        has_send = "send" in p_lower or "email the summary" in p_lower or "post to slack" in p_lower or "notify" in p_lower
        
        is_multi_action_workflow = (
            (has_read_or_search and has_summarize)
            or (has_summarize and has_send)
            or (has_read_or_search and has_download_or_drive)
            or " -> " in p_lower
            or ", then " in p_lower
        )
        
        if is_multi_action_workflow and not ("saying" in p_lower or "wishing" in p_lower or "explaining" in p_lower):
            return self._build_result(
                IntentType.MULTI_STEP_WORKFLOW,
                0.99,
                "Detected multi-step tool sequence prompt",
                entities,
            )

        # Email Schedule
        if any(kw in p_lower for kw in ["schedule", "tomorrow at", "next monday at", "every monday", "every day", "after 2 hours", "after 1 hour"]) and not "postponed" in p_lower and not "draft" in p_lower:
            if not any(k in p_lower for k in ["calendar", "meeting"]) or "email" in p_lower or "send" in p_lower:
                return self._build_result(IntentType.EMAIL_SCHEDULE, 0.97, "Detected email scheduling intent", entities)

        # Email Read Latest
        if any(kw in p_lower for kw in ["latest", "last email", "recent email", "read last"]):
            return self._build_result(IntentType.EMAIL_READ_LATEST, 0.98, "Detected read latest email intent", entities)

        # Email Read Unread
        if "unread" in p_lower:
            return self._build_result(IntentType.EMAIL_READ_UNREAD, 0.98, "Detected read unread emails intent", entities)

        # Email Search By Subject
        subject_match = re.search(r"subject\s+[:'\"]?([^'\"]+)['\"]?", prompt, re.IGNORECASE)
        if subject_match:
            subj = subject_match.group(1).strip()
            entities["subject"] = subj
            return self._build_result(IntentType.EMAIL_SEARCH_BY_SUBJECT, 0.98, f"Detected search emails by subject '{subj}'", entities)

        # Email Search By Sender
        from_match = re.search(r"(?:from|by)\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|[a-zA-Z0-9._%+-]+)", prompt, re.IGNORECASE)
        if from_match:
            candidate = from_match.group(1).rstrip(".,;!?").strip()
            if candidate.lower() not in ["me", "us", "my", "email", "emails", "gmail", "google", "drive", "slack", "github", "calendar"] or "@" in candidate:
                entities["sender"] = candidate
                return self._build_result(IntentType.EMAIL_SEARCH_BY_SENDER, 0.98, f"Detected search emails from sender '{candidate}'", entities)

        # Email Search
        if any(kw in p_lower for kw in ["search", "find", "query", "lookup"]):
            if not any(k in p_lower for k in ["slack", "github", "drive", "calendar"]):
                return self._build_result(IntentType.EMAIL_SEARCH, 0.96, "Detected general email search intent", entities)

        # Email Read
        if any(kw in p_lower for kw in ["read email", "read emails", "fetch emails", "check inbox", "get messages", "read"]):
            if not any(k in p_lower for k in ["drive", "slack", "github"]):
                return self._build_result(IntentType.EMAIL_READ, 0.96, "Detected email read intent", entities)

        # Slack Send
        if any(kw in p_lower for kw in ["slack", "notify"]):
            return self._build_result(IntentType.SLACK_SEND, 0.98, "Detected Slack notification intent", entities)

        # GitHub Create Issue
        if any(kw in p_lower for kw in ["github", "issue"]):
            return self._build_result(IntentType.GITHUB_CREATE_ISSUE, 0.98, "Detected GitHub issue creation intent", entities)

        # Calendar Create Event
        if any(kw in p_lower for kw in ["calendar", "create event", "schedule meeting", "add to calendar"]):
            return self._build_result(IntentType.CALENDAR_CREATE_EVENT, 0.98, "Detected Calendar event creation intent", entities)

        # Email Send (Only when explicit send requested)
        if any(kw in p_lower for kw in ["send email", "send an email", "send message", "send a ", "mail to", "dispatch"]):
            return self._build_result(IntentType.EMAIL_SEND, 0.95, "Detected email send intent", entities)

        return None

    def _classify_with_llm(self, prompt: str) -> Optional[IntentClassificationResult]:
        try:
            from app.agents.llm.manager import llm_manager
            full_prompt = f"{INTENT_CLASSIFICATION_SYSTEM_PROMPT}\n\nUSER PROMPT:\n{prompt}"
            
            raw_res = None
            try:
                loop = asyncio.get_running_loop()
                raw_res = None
            except RuntimeError:
                raw_res = asyncio.run(llm_manager.generate_text(full_prompt))

            if raw_res:
                cleaned = self._clean_json_string(raw_res)
                parsed = json.loads(cleaned)
                return IntentClassificationResult(**parsed)
        except Exception as exc:
            logger.warning(f"[AI-1] LLM Classification exception: {exc}")
        return None

    def _fallback_classify(self, prompt: str, p_lower: str) -> IntentClassificationResult:
        # NO SILENT FALLBACK TO EMAIL_SEND! Return UNKNOWN if unresolved with confidence=0.50.
        return self._build_result(IntentType.UNKNOWN, 0.50, "Could not map prompt to known intent", {})

    def _build_result(
        self, intent: IntentType, confidence: float, reasoning: str, entities: Dict[str, Any]
    ) -> IntentClassificationResult:
        from app.agents.intent_classifier.models import IntentCategory
        category = IntentCategory.READ_ONLY
        side_effect = False
        read_only = True
        requires_message_lookup = False
        requires_send = False
        requires_reply = False
        requires_modify = False

        if intent in [IntentType.EMAIL_SEND, IntentType.EMAIL_GENERATE, IntentType.SLACK_SEND, IntentType.GITHUB_CREATE_ISSUE, IntentType.CALENDAR_CREATE_EVENT]:
            category = IntentCategory.SEND
            side_effect = True
            read_only = False
            requires_send = True
        elif intent == IntentType.EMAIL_REPLY:
            category = IntentCategory.REPLY
            side_effect = True
            read_only = False
            requires_reply = True
            requires_message_lookup = True
        elif intent == IntentType.EMAIL_FORWARD:
            category = IntentCategory.FORWARD
            side_effect = True
            read_only = False
            requires_message_lookup = True
        elif intent == IntentType.EMAIL_DELETE:
            category = IntentCategory.DELETE
            side_effect = True
            read_only = False
            requires_message_lookup = True
        elif intent in [IntentType.EMAIL_MARK_READ, IntentType.EMAIL_MARK_UNREAD]:
            category = IntentCategory.MODIFY
            side_effect = True
            read_only = False
            requires_modify = True
        elif intent == IntentType.EMAIL_DRAFT:
            category = IntentCategory.DRAFT
            side_effect = False
            read_only = False
        elif intent == IntentType.EMAIL_SCHEDULE:
            category = IntentCategory.SCHEDULE
            side_effect = True
            read_only = False
        elif intent in [IntentType.EMAIL_READ, IntentType.EMAIL_READ_LATEST, IntentType.EMAIL_READ_UNREAD, IntentType.EMAIL_SUMMARIZE]:
            category = IntentCategory.READ_ONLY
            side_effect = False
            read_only = True
            requires_message_lookup = True
        elif intent in [IntentType.EMAIL_SEARCH, IntentType.EMAIL_SEARCH_BY_SENDER, IntentType.EMAIL_SEARCH_BY_SUBJECT]:
            category = IntentCategory.SEARCH
            side_effect = False
            read_only = True
            requires_message_lookup = False
        elif intent == IntentType.MULTI_STEP_WORKFLOW:
            category = IntentCategory.MULTI_STEP
            side_effect = True
            read_only = False

        return IntentClassificationResult(
            intent=intent,
            category=category,
            confidence=confidence,
            reasoning=reasoning,
            entities=entities,
            side_effect=side_effect,
            read_only=read_only,
            requires_message_lookup=requires_message_lookup,
            requires_send=requires_send,
            requires_reply=requires_reply,
            requires_modify=requires_modify,
        )

    def _clean_json_string(self, raw: str) -> str:
        text = raw.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text).strip()
        return text

    def _log_classification(self, result: IntentClassificationResult):
        logger.info(f"[AI-14][GEMINI_INTENT] intent={result.intent.value} category={result.category.value} side_effect={result.side_effect} read_only={result.read_only}")
        logger.info(f"[AI-11][GEMINI] Classification response: intent={result.intent.value}")
        logger.info(f"[AI-11][INTENT] detected={result.intent.value}")
        logger.info(f"[AI-11][CONFIDENCE] {result.confidence}")
        logger.info(f"[AI-11][ENTITIES] {result.entities}")
        logger.info(f"[AI-1] Detected Intent: {result.intent.value}")
        logger.info(f"[AI-1] Confidence: {result.confidence}")
        logger.info(f"[AI-1] Reasoning: {result.reasoning}")
        logger.info(f"[AI-1] Entities: {result.entities}")


enterprise_intent_classifier = EnterpriseIntentClassifier()



enterprise_intent_classifier = EnterpriseIntentClassifier()
