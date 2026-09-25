import re
import logging
from typing import Dict, Optional

logger = logging.getLogger("agentflow.agents.planner.slack_parameter_extractor")


def extract_slack_text(prompt: str) -> str:
    """
    Sprint SLACK-TEXT: Deterministic Slack Message Text Extractor.
    Extracts the message text payload from natural language prompts.
    
    Requirements:
    1. Support keywords: saying, message, text, content, with message, etc.
    2. Support double quotes, single quotes, and curly quotes.
    3. Support action-preceded quoted strings (e.g. Send "Hello" to #channel).
    4. Preserve dynamic expressions like {{step_2.summary}}.
    5. Avoid capturing quoted emails, URLs, or non-message parameters.
    6. Fallback to raw prompt if text cannot be deterministically isolated.
    """
    if not prompt:
        return ""

    prompt_clean = prompt.strip()

    # 1. If prompt is already a direct dynamic template expression like {{step_1.output}}
    if prompt_clean.startswith("{{") and prompt_clean.endswith("}}"):
        return prompt_clean

    # 2. Match keyword + quoted text: saying "...", with message "...", text '...', content "..."
    pattern_keyword_quoted = (
        r"(?i)\b(?:saying|with\s+message|with\s+text|with\s+content|message|text|content|body|payload)\s*"
        r"(?:[:=]\s*)?"
        r"(?:\"([^\"]+)\"|'([^']+)'|“([^”]+)”|‘([^’]+)’)"
    )
    keyword_quoted = re.search(pattern_keyword_quoted, prompt_clean)
    if keyword_quoted:
        for g in keyword_quoted.groups():
            if g is not None:
                extracted = g.strip()
                logger.info(f"[SLACK_EXTRACTOR] Extracted text via keyword-quoted: '{extracted}'")
                return extracted

    # 3. Match action + quoted text: Send "...", Post the Slack message "..."
    pattern_action_quoted = (
        r"(?i)\b(?:send|post|notify|publish|share)\s+"
        r"(?:the\s+)?(?:slack\s+)?(?:message|text|notification|content)?\s*"
        r"(?:\"([^\"]+)\"|'([^']+)'|“([^”]+)”|‘([^’]+)’)"
    )
    action_quoted = re.search(pattern_action_quoted, prompt_clean)
    if action_quoted:
        for g in action_quoted.groups():
            if g is not None:
                extracted = g.strip()
                logger.info(f"[SLACK_EXTRACTOR] Extracted text via action-quoted: '{extracted}'")
                return extracted

    # 4. Keyword + unquoted text until channel / target directive or end of prompt
    pattern_keyword_unquoted = (
        r"(?i)\b(?:saying|with\s+message|with\s+text|with\s+content)\s+"
        r"(.+?)"
        r"(?=\s+(?:to|in|on|at)\s+(?:#[a-zA-Z0-9_-]+|(?:the\s+|our\s+)?(?:[a-zA-Z0-9_-]+\s+)?channel|slack)|$)"
    )
    keyword_unquoted = re.search(pattern_keyword_unquoted, prompt_clean)
    if keyword_unquoted:
        extracted = keyword_unquoted.group(1).strip()
        # Clean surrounding quotes if present
        if (extracted.startswith('"') and extracted.endswith('"')) or (extracted.startswith("'") and extracted.endswith("'")):
            extracted = extracted[1:-1].strip()
        if extracted and not extracted.startswith("#") and not extracted.startswith("http"):
            logger.info(f"[SLACK_EXTRACTOR] Extracted text via keyword-unquoted: '{extracted}'")
            return extracted

    # 5. Fallback to prompt if no specific message content could be isolated
    return prompt_clean


def extract_slack_parameters(prompt: str) -> Dict[str, str]:
    """
    Extracts both channel and text parameters for Slack operations.
    """
    from app.agents.planner.deterministic_normalizer import deterministic_normalizer
    ch = deterministic_normalizer.extract_slack_channel(prompt) or "#general"
    txt = extract_slack_text(prompt)
    return {
        "channel": ch,
        "text": txt
    }
