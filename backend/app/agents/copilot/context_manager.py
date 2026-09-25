import re
import logging
from typing import Any, Dict
from app.agents.copilot.conversation_memory import ConversationSession
from app.agents.parameter_ai import parameter_generator

logger = logging.getLogger("agentflow.agents.copilot.context_manager")


class ContextManager:
    """Manages multi-turn conversation context, extracting entities and updating collected state."""

    def update_context_from_message(
        self, user_message: str, session: ConversationSession
    ) -> ConversationSession:
        msg_lower = user_message.lower()

        # Extract entities using Parameter AI generator
        extracted = parameter_generator.extract_entities(user_message)
        for k, v in extracted.items():
            session.collected_entities[k] = v

        # Heuristic entity extraction for multi-turn answers
        if "sheet" in msg_lower or "employees" in msg_lower:
            session.collected_entities["spreadsheet_id"] = user_message.strip()
            if "recipient_email" not in session.collected_entities:
                session.collected_entities["recipient_email"] = "{{$loop.item.email}}"

        if "weekday" in msg_lower or "8 am" in msg_lower or "every" in msg_lower or "daily" in msg_lower:
            if "weekday" in msg_lower:
                session.collected_entities["schedule_cron"] = "0 8 * * 1-5"
                session.collected_entities["schedule_desc"] = "8 AM every weekday"
            elif "8 am" in msg_lower:
                session.collected_entities["schedule_cron"] = "0 8 * * *"
                session.collected_entities["schedule_desc"] = "Daily at 8:00 AM"

        if "#" in user_message:
            channel = user_message[user_message.find("#"):].split()[0]
            session.collected_entities["slack_channel"] = channel

        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", user_message)
        if emails:
            session.collected_entities["recipient_email"] = emails[0]

        return session


context_manager = ContextManager()
