import pytest
from app.agents.copilot import copilot_ai_service


def test_copilot_multi_turn_conversation():
    session_id = "test_copilot_session_1"

    # Turn 1: User asks for email workflow without parameters
    turn1 = copilot_ai_service.chat_turn(session_id, "Send a good morning email")
    assert turn1["is_ready_to_generate"] is False
    assert len(turn1["missing_inputs"]) > 0
    assert len(turn1["suggested_replies"]) > 0
    assert turn1["proposed_graph"] is None

    # Turn 2: User provides recipient data source
    turn2 = copilot_ai_service.chat_turn(session_id, "Everyone in HR Employees Sheet")
    assert "spreadsheet_id" in turn2["collected_entities"]

    # Turn 3: User provides schedule time
    turn3 = copilot_ai_service.chat_turn(session_id, "8 AM every weekday")
    assert turn3["is_ready_to_generate"] is True
    assert turn3["proposed_graph"] is not None
    assert len(turn3["proposed_graph"].get("nodes", [])) >= 2
    assert "Great!" in turn3["message"]

    # Retrieve session history
    history = copilot_ai_service.get_session_history(session_id)
    assert len(history["history"]) == 6  # 3 user turns + 3 assistant turns

    # Reset session
    reset_res = copilot_ai_service.reset_session(session_id)
    assert reset_res["reset"] is True
