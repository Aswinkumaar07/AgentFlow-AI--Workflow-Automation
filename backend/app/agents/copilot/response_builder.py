import logging
from typing import Any, Dict, List, Optional
from app.agents.copilot.conversation_memory import ConversationSession, ConversationTurn

logger = logging.getLogger("agentflow.agents.copilot.response_builder")


class ResponseBuilder:
    """Builds formatted Copilot messages, suggested quick reply chips, and ready workflow DAG specs."""

    def build_ready_response(
        self, session: ConversationSession, proposed_graph: Dict[str, Any]
    ) -> Dict[str, Any]:
        nodes = proposed_graph.get("nodes", [])
        providers = [n.get("provider", "Step") for n in nodes]
        flow_summary = " ➔ ".join(providers) if providers else "Custom Execution DAG"

        msg = (
            f"Great! I have collected all required information for your workflow.\n\n"
            f"**Proposed Architecture:**\n`{flow_summary}`\n\n"
            f"Click **Generate Workflow** below to render the DAG directly onto your canvas!"
        )

        return {
            "session_id": session.session_id,
            "message": msg,
            "is_ready_to_generate": True,
            "suggested_replies": ["Generate Workflow", "Change schedule time", "Add Slack notification step"],
            "proposed_graph": proposed_graph,
            "collected_entities": session.collected_entities,
            "missing_inputs": [],
        }

    def build_question_response(
        self, session: ConversationSession, question: str, suggestions: List[str], missing_inputs: List[str]
    ) -> Dict[str, Any]:
        return {
            "session_id": session.session_id,
            "message": question,
            "is_ready_to_generate": False,
            "suggested_replies": suggestions,
            "proposed_graph": None,
            "collected_entities": session.collected_entities,
            "missing_inputs": missing_inputs,
        }


response_builder = ResponseBuilder()
