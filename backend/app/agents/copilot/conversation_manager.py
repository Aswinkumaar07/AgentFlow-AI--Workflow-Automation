import datetime
import logging
from typing import Any, Dict, List, Optional

from app.agents.copilot.conversation_memory import conversation_memory_store, ConversationSession, ConversationTurn
from app.agents.copilot.context_manager import context_manager
from app.agents.copilot.question_generator import question_generator
from app.agents.copilot.response_builder import response_builder
from app.agents.planner.planner_v3 import intelligent_planner_v3

logger = logging.getLogger("agentflow.agents.copilot.manager")


class ConversationManager:
    """
    AgentFlow AI - AI Copilot Conversation Manager
    Orchestrates multi-turn conversation sessions, state memory, question generation,
    entity collection, and conditional workflow DAG synthesis.
    """

    def process_turn(self, session_id: str, user_message: str) -> Dict[str, Any]:
        session: ConversationSession = conversation_memory_store.get_or_create_session(session_id)

        # 1. Update session user goal if first turn
        if not session.user_goal:
            session.user_goal = user_message.strip()

        # 2. Add user message turn to history
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        session.history.append(
            ConversationTurn(role="user", message=user_message, timestamp=now_str)
        )

        # 3. Extract entities and update context
        session = context_manager.update_context_from_message(user_message, session)

        # 4. Synthesize accumulated prompt with collected entities
        accumulated_prompt = session.user_goal
        if session.collected_entities:
            entity_str = ", ".join([f"{k}: {v}" for k, v in session.collected_entities.items()])
            accumulated_prompt += f" with parameters: {entity_str}"

        # 5. Plan DAG via Intelligent Planner V3 to evaluate missing inputs
        plan_res = intelligent_planner_v3.plan(accumulated_prompt)
        missing_inputs = plan_res.missing_inputs

        # Deduplicate missing inputs against collected entities
        real_missing = [
            m for m in missing_inputs
            if m not in session.collected_entities and m != "recipient_email" or ("recipient_email" not in session.collected_entities and m == "recipient_email")
        ]

        # Filter out recipient if email/sheet loop is specified
        if "spreadsheet_id" in session.collected_entities and "recipient_email" in real_missing:
            real_missing.remove("recipient_email")
            session.collected_entities["recipient_email"] = "{{$loop.item.email}}"

        # 6. Branching Logic: Question vs Ready
        if real_missing:
            next_missing = real_missing[0]
            question, suggestions = question_generator.generate_followup_question(
                next_missing, session.user_goal, session
            )
            session.missing_inputs = real_missing
            session.is_ready_to_generate = False

            # Add AI turn to history
            session.history.append(
                ConversationTurn(
                    role="assistant",
                    message=question,
                    timestamp=now_str,
                    suggested_replies=suggestions,
                )
            )
            conversation_memory_store.update_session(session)

            return response_builder.build_question_response(
                session, question, suggestions, real_missing
            )
        else:
            session.is_ready_to_generate = True
            session.proposed_graph = plan_res.workflow_graph
            session.missing_inputs = []

            ready_resp = response_builder.build_ready_response(session, plan_res.workflow_graph)

            session.history.append(
                ConversationTurn(
                    role="assistant",
                    message=ready_resp["message"],
                    timestamp=now_str,
                    suggested_replies=ready_resp["suggested_replies"],
                )
            )
            conversation_memory_store.update_session(session)

            return ready_resp


conversation_manager = ConversationManager()
