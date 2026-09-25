import logging
from typing import List, Tuple
from app.agents.copilot.conversation_memory import ConversationSession

logger = logging.getLogger("agentflow.agents.copilot.question_generator")


class QuestionGenerator:
    """Generates intelligent follow-up questions and quick-reply suggestion chips for missing workflow parameters."""

    def generate_followup_question(
        self, missing_input: str, goal: str, session: ConversationSession
    ) -> Tuple[str, List[str]]:
        prefs = session.user_preferences

        if missing_input in ["recipient_email", "recipient", "to"]:
            question = "Who should receive the email?"
            suggestions = ["Everyone in HR Employees Sheet", "john@example.com", "customer@company.com"]

        elif missing_input in ["spreadsheet_id", "sheet", "spreadsheet"]:
            question = "Which Google Sheet contains the employee/target data?"
            suggestions = ["HR Employees", "Customer Contacts Sheet", "Sales Leads 2026"]

        elif missing_input in ["schedule_time", "schedule_cron", "schedule"]:
            question = "What time or frequency should this workflow run?"
            suggestions = ["8 AM every weekday", "Every Monday at 9:00 AM", "Daily at 8:00 AM"]

        elif missing_input in ["slack_channel", "channel"]:
            chans = prefs.preferred_slack_channels
            question = f"Which Slack channel should be notified? (e.g. {', '.join(chans)})"
            suggestions = chans + ["#announcements"]

        elif missing_input in ["folder"]:
            folders = prefs.preferred_drive_folders
            question = f"Which Google Drive folder should files be saved into? (e.g. {', '.join(folders)})"
            suggestions = folders + ["Invoices 2026"]

        elif missing_input in ["github_repo", "repo"]:
            question = "Which GitHub repository should be monitored?"
            suggestions = ["AgentFlow-AI/TERRAWATCH", "my-org/core-backend", "my-org/frontend"]

        elif missing_input in ["webhook_url", "target_url"]:
            question = "What target HTTP URL endpoint should receive requests?"
            suggestions = ["https://api.example.com/v1/webhook", "https://hooks.slack.com/services/xxx"]

        else:
            question = f"Could you provide the '{missing_input}' for this workflow?"
            suggestions = ["Use default configuration", "Skip this step"]

        return question, suggestions


question_generator = QuestionGenerator()
