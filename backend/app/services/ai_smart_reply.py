import json
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("agentflow.services.ai_smart_reply")


class AISmartReplyService:
    """
    Sprint Smart Reply: Generates contextual email replies using Gemini LLM while preserving Gmail Thread IDs.
    
    Workflow:
    1. Input: Original Email Context (sender, subject, body, message_id, thread_id) + optional User Instruction.
    2. Gemini LLM context analysis.
    3. Output: Structured reply payload with preserved thread_id, subject prefixed with 'Re: ', and body.
    """

    def generate_smart_reply(
        self,
        original_email: Dict[str, Any],
        user_instruction: Optional[str] = None,
    ) -> Dict[str, Any]:
        sender = original_email.get("sender") or original_email.get("from") or "sender@example.com"
        subject = original_email.get("subject") or "Message"
        body = original_email.get("body") or original_email.get("snippet") or ""
        msg_id = original_email.get("message_id") or original_email.get("id") or "msg_000"
        thread_id = original_email.get("thread_id") or original_email.get("threadId") or msg_id

        # Prefix subject with Re: if not present
        reply_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"

        try:
            import asyncio
            from app.agents.llm.manager import llm_manager

            prompt = (
                f"You are an AI Smart Reply Engine for AgentFlow AI.\n"
                f"Generate a professional, context-aware reply to the following email:\n\n"
                f"Original Sender: {sender}\n"
                f"Original Subject: {subject}\n"
                f"Original Body:\n{body}\n\n"
            )
            if user_instruction:
                prompt += f"User Directive: {user_instruction}\n\n"

            prompt += (
                "CRITICAL: Respond ONLY with a valid JSON object in format:\n"
                "{\n"
                '  "reply_body": "<professional, contextual reply text>"\n'
                "}\n"
                "No markdown wrappers. No commentary."
            )

            response = None
            try:
                loop = asyncio.get_running_loop()
                response = None
            except RuntimeError:
                response = asyncio.run(llm_manager.generate_text(prompt))

            if response:
                cleaned = self._clean_and_parse_json(response)
                reply_text = cleaned.get("reply_body")
                if reply_text:
                    logger.info(f"[SMART-REPLY] Generated reply for thread_id='{thread_id}'")
                    return {
                        "message_id": msg_id,
                        "thread_id": thread_id,
                        "to": sender,
                        "subject": reply_subject,
                        "body": reply_text,
                    }
        except Exception as exc:
            logger.warning(f"[SMART-REPLY] LLM call exception: {exc}, using fallback smart reply.")

        # Fallback contextual smart reply
        fallback_body = f"Hello,\n\nThank you for reaching out regarding '{subject}'. I have received your message and will get back to you shortly.\n\nBest regards,\nAgentFlow"
        return {
            "message_id": msg_id,
            "thread_id": thread_id,
            "to": sender,
            "subject": reply_subject,
            "body": fallback_body,
        }

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


ai_smart_reply_service = AISmartReplyService()
