import pytest
from app.services.ai_email_writer import ai_email_writer, AIEmailWriter


def test_ai_email_writer_triggers():
    assert ai_email_writer.is_writer_prompt("Write an apology email to Sarah")
    assert ai_email_writer.is_writer_prompt("Generate a marketing newsletter")
    assert ai_email_writer.is_writer_prompt("Compose a follow-up email")
    assert ai_email_writer.is_writer_prompt("Draft a sales offer")
    assert not ai_email_writer.is_writer_prompt("Read my latest email")


def test_ai_email_writer_tone_detection():
    assert ai_email_writer.detect_tone("Write an apology email for delay") == "Apology"
    assert ai_email_writer.detect_tone("Generate a happy birthday email") == "Birthday"
    assert ai_email_writer.detect_tone("Compose a sales deal offer") == "Sales"
    assert ai_email_writer.detect_tone("Draft a newsletter for subscribers") == "Newsletter"
    assert ai_email_writer.detect_tone("Write a reminder email") == "Reminder"
    assert ai_email_writer.detect_tone("Compose a formal business letter") == "Formal"


def test_ai_email_writer_json_output_structure():
    prompts = [
        ("Write an apology email to John", "Apology"),
        ("Compose a welcome email for new client", "Professional"),
        ("Generate a sales offer for discount", "Sales"),
        ("Draft a birthday email for Sarah", "Birthday"),
        ("Write a reminder email for tomorrow meeting", "Reminder"),
    ]

    for prompt, expected_tone in prompts:
        res = ai_email_writer.generate_email_content(prompt)
        assert isinstance(res, dict)
        assert "subject" in res and "body" in res
        assert len(res["subject"]) > 0
        assert len(res["body"]) > 0
        # Verify no raw unparsed JSON fences
        assert not res["subject"].startswith("```")
        assert not res["body"].startswith("```")


def test_ai_email_writer_clean_and_parse_json():
    raw_llm_output = """```json
    {
      "subject": "Exclusive 50% Off Special Offer",
      "body": "Hi,\\n\\nWe are thrilled to offer you 50% off on all AgentFlow subscriptions this month!\\n\\nBest regards,\\nSales Team"
    }
    ```"""
    parsed = ai_email_writer.clean_and_parse_json(raw_llm_output)
    assert parsed["subject"] == "Exclusive 50% Off Special Offer"
    assert "50% off" in parsed["body"]
