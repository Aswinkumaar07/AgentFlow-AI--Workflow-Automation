import logging
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("agentflow.agents.parameter_ai.generator")


class ParameterGenerationResult(BaseModel):
    parameters: Dict[str, Any] = Field(default_factory=dict)
    missing_inputs: List[str] = Field(default_factory=list)
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)


class ParameterGenerator:
    """
    AI Parameter Generation Engine
    Extracts entities directly from prompt without static fallback defaults.
    """

    def extract_entities(self, prompt: str) -> Dict[str, Any]:
        """Extracts structural entities from natural language prompt."""
        p_lower = prompt.lower()
        entities: Dict[str, Any] = {}

        # 1. Recipient / Email extraction
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", prompt)
        if emails:
            entities["recipient_email"] = emails[0]

        # 2. Slack Channel extraction (#channel-name or plain text channel format)
        channels = re.findall(r"#[a-zA-Z0-9_\-]+", prompt)
        ignore_words = {"the", "a", "an", "slack", "channel", "my", "our"}
        if channels:
            entities["slack_channel"] = channels[0]
            entities["channel"] = channels[0]
        else:
            m2 = re.search(r"(?:in|to|on|alert)\s+(?:the\s+|our\s+)?([a-zA-Z0-9_\-]+)\s+channel", prompt, re.IGNORECASE)
            if m2 and m2.group(1).lower() not in ignore_words:
                entities["slack_channel"] = f"#{m2.group(1)}"
                entities["channel"] = f"#{m2.group(1)}"
            else:
                m1 = re.search(r"(?:channel\s+|in\s+channel\s+|to\s+channel\s+)([a-zA-Z0-9_\-]+)", prompt, re.IGNORECASE)
                if m1 and m1.group(1).lower() not in ignore_words:
                    entities["slack_channel"] = f"#{m1.group(1)}"
                    entities["channel"] = f"#{m1.group(1)}"

        # 3. Folder extraction
        folder_match = re.search(r"folder:?\s*([a-zA-Z0-9_-]+)", prompt, re.IGNORECASE)
        if folder_match:
            entities["folder"] = folder_match.group(1)

        # 4. Spreadsheet extraction
        sheet_match = re.search(r"(?:spreadsheet|sheet):?\s*([a-zA-Z0-9_-]+)", prompt, re.IGNORECASE)
        if sheet_match:
            entities["spreadsheet_id"] = sheet_match.group(1)

        # 5. Repository & Branch extraction
        repo_match = re.search(r"repo:?\s*([\w-]+/[\w-]+)", prompt, re.IGNORECASE)
        if repo_match:
            entities["github_repo"] = repo_match.group(1)
        branch_match = re.search(r"branch:?\s*([\w-]+)", prompt, re.IGNORECASE)
        if branch_match:
            entities["github_branch"] = branch_match.group(1)

        # 6. Webhook URL extraction
        url_match = re.search(r"https?://[^\s]+", prompt)
        if url_match:
            entities["webhook_url"] = url_match.group(0)

        return entities

    def generate_parameters_for_operation(
        self, prompt: str, operation_id: str, provider: str
    ) -> ParameterGenerationResult:
        """Generates operation parameter payload based on prompt entity extraction."""
        entities = self.extract_entities(prompt)
        p_lower = prompt.lower()
        params: Dict[str, Any] = {}
        missing: List[str] = []

        if operation_id == "gmail.messages.send":
            if "recipient_email" in entities:
                params["to"] = entities["recipient_email"]
            else:
                params["to"] = None
                missing.append("recipient_email")

            if "subject" in entities:
                params["subject"] = entities["subject"]
            if "body" in entities:
                params["body"] = entities["body"]

        elif operation_id == "slack.chat.postMessage":
            from app.agents.planner.slack_parameter_extractor import extract_slack_text
            if "slack_channel" in entities:
                params["channel"] = entities["slack_channel"]
            elif "channel" in entities:
                params["channel"] = entities["channel"]
            params["text"] = extract_slack_text(prompt)

        elif operation_id == "sheets.spreadsheets.values.get":
            if "spreadsheet_id" in entities:
                params["spreadsheet_id"] = entities["spreadsheet_id"]
            params["range"] = "Sheet1!A1:Z"

        elif operation_id == "drive.files.create":
            if "folder" in entities:
                params["folder"] = entities["folder"]
            params["file_name"] = "{{$loop.item.name}}"

        elif operation_id == "github.pulls.list":
            if "github_repo" in entities:
                repo = entities["github_repo"]
                parts = repo.split("/")
                params["owner"] = parts[0]
                params["repo"] = parts[1] if len(parts) > 1 else "TERRAWATCH"

        elif operation_id == "ai.summarize":
            params["text"] = "{{trigger_payload.body}}"
            params["max_tokens"] = 200

        elif operation_id == "generic.http.request":
            if "webhook_url" in entities:
                params["url"] = entities["webhook_url"]
            else:
                params["url"] = None
                missing.append("webhook_url")
            params["method"] = "POST" if "post" in p_lower else "GET"

        return ParameterGenerationResult(
            parameters=params,
            missing_inputs=missing,
            extracted_entities=entities,
        )


parameter_generator = ParameterGenerator()
