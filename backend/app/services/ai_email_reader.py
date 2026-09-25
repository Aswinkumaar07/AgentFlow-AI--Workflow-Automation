import json
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("agentflow.services.ai_email_reader")


class AIEmailReader:
    """
    Sprint AI Email Reader: Summarizes and extracts structured intelligence from Gmail messages using Gemini LLM.
    
    Output Format: Structured JSON list or dict with summary, priority, key points, and action items.
    """

    def parse_query_intent(self, prompt: str) -> Dict[str, Any]:
        """Parses user intent for email query parameters using GmailSearchQueryTranslator."""
        from app.services.gmail_search_query_translator import gmail_search_query_translator
        return gmail_search_query_translator.translate_to_gmail_query(prompt)

    def summarize_messages(self, messages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Summarizes a list of message objects into structured email intelligence."""
        if not messages_data:
            return []

        summaries = []
        for msg in messages_data:
            msg_id = msg.get("id") or msg.get("messageId") or "unknown"
            snippet = msg.get("snippet", "")
            payload = msg.get("payload", {})
            headers = payload.get("headers", []) if isinstance(payload, dict) else []

            subject = "No Subject"
            sender = "Unknown Sender"
            for h in headers:
                if isinstance(h, dict):
                    if h.get("name", "").lower() == "subject":
                        subject = h.get("value", subject)
                    elif h.get("name", "").lower() == "from":
                        sender = h.get("value", sender)

            summary_item = self._summarize_single_email(msg_id, subject, sender, snippet)
            summaries.append(summary_item)

        return summaries

    def _summarize_single_email(self, msg_id: str, subject: str, sender: str, snippet: str) -> Dict[str, Any]:
        full_text = f"From: {sender}\nSubject: {subject}\nSnippet: {snippet}"

        try:
            import asyncio
            from app.agents.llm.manager import llm_manager
            system_prompt = (
                "You are an AI Email Reader for AgentFlow AI.\n"
                "Analyze the email content and generate a structured JSON summary object with:\n"
                "{\n"
                '  "id": "<message_id>",\n'
                '  "subject": "<subject>",\n'
                '  "sender": "<sender>",\n'
                '  "snippet": "<snippet>",\n'
                '  "summary": "<2-3 sentence clear summary>",\n'
                '  "priority": "HIGH" | "MEDIUM" | "LOW",\n'
                '  "action_items": ["<action item 1>", ...]\n'
                "}\n"
                "Return ONLY valid JSON. No markdown wrappers."
            )

            response = None
            try:
                loop = asyncio.get_running_loop()
                response = None
            except RuntimeError:
                response = asyncio.run(llm_manager.generate_text(f"{system_prompt}\n\nEmail Content:\n{full_text}"))

            if response:
                cleaned = self._clean_and_parse_json(response)
                if cleaned.get("summary"):
                    cleaned["id"] = msg_id
                    if "bullet_summary" not in cleaned:
                        cleaned["bullet_summary"] = [
                            f"• Sender: {cleaned.get('sender', sender)}",
                            f"• Subject: {cleaned.get('subject', subject)}",
                            f"• Summary: {cleaned.get('summary')}",
                            f"• Priority: {cleaned.get('priority', 'MEDIUM')}",
                        ]
                    return cleaned
        except Exception as exc:
            logger.warning(f"[AI-EMAIL-READER] LLM call exception: {exc}, using fallback summarizer.")

        priority = "HIGH" if any(w in (subject + snippet).lower() for w in ["urgent", "critical", "action", "important", "asap"]) else "MEDIUM"
        action_items = ["Review message details."] if priority == "HIGH" else []
        bullets = [
            f"• Sender: {sender}",
            f"• Subject: {subject}",
            f"• Summary: Email from {sender} regarding '{subject}'. Brief snippet: {snippet[:100]}...",
            f"• Priority: {priority}",
        ]

        return {
            "id": msg_id,
            "subject": subject,
            "sender": sender,
            "snippet": snippet,
            "summary": f"Email from {sender} regarding '{subject}'. Brief snippet: {snippet[:100]}...",
            "bullet_summary": bullets,
            "priority": priority,
            "action_items": action_items,
        }

    def generate_bullet_summaries(self, messages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generates bulleted summary items for each email message."""
        summaries = self.summarize_messages(messages_data)
        for s in summaries:
            if "bullet_summary" not in s:
                s["bullet_summary"] = [
                    f"• Sender: {s.get('sender', 'Unknown')}",
                    f"• Subject: {s.get('subject', 'No Subject')}",
                    f"• Summary: {s.get('summary', '')}",
                ]
        return summaries

    def _clean_and_parse_json(self, raw: str) -> Dict[str, Any]:
        if not raw:
            return {}
        text = raw.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text).strip()
        try:
            return json.loads(text)
        except Exception:
            return {}


ai_email_reader = AIEmailReader()
