import re
import logging
from typing import Dict, Tuple

logger = logging.getLogger("agentflow.agents.planner.gmail_parameter_extractor")


def extract_gmail_parameters(prompt: str) -> Dict[str, str]:
    """
    Sprint AUTH-12: Deterministic Gmail Parameter Extraction Pipeline.
    
    Requirements:
    1. Extract recipient email into parameters.to using email pattern matching.
    2. Extract only text following Subject: into parameters.subject.
    3. Extract only text following Body: into parameters.body.
    4. Do not include To:, Subject:, or Body: labels in extracted values.
    5. Trim leading/trailing whitespace from all parameters.
    6. Preserve newlines only in body; remove \\r and \\n from to and subject.
    7. If Subject: is missing, generate a concise subject (3-8 words) from intent.
    8. If Body: is missing, generate clean email body from request.
    """
    if not prompt:
        prompt = ""

    # 1. Recipient email extraction via regex
    emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", prompt)
    to_val = emails[0].strip() if emails else ""
    to_val = re.sub(r"[\r\n]+", "", to_val).strip()

    # 2. Extract explicit Subject and Body labels (case-insensitive)
    subject_val = None
    body_val = None

    # Regex for Subject: label up to Body: or end of prompt
    subj_match = re.search(r"(?i)\bsubject:\s*(.*?)(?=\s*(?:body:|$))", prompt, re.DOTALL)
    if subj_match:
        raw_subj = subj_match.group(1).strip()
        if raw_subj:
            # Remove \r and \n from subject header
            subject_val = re.sub(r"[\r\n]+", " ", raw_subj).strip()

    # Regex for Body: label
    body_match = re.search(r"(?i)\bbody:\s*(.*)", prompt, re.DOTALL)
    if body_match:
        raw_body = body_match.group(1).strip()
        if raw_body:
            # Preserve newlines in body, remove \r
            body_val = raw_body.replace("\r", "").strip()

    # Extract target recipient name if present (e.g., "Wish Sarah happy birthday" -> "Sarah")
    recipient_name = ""
    name_match = re.search(r'(?:wish|send|to|apology|sorry)\s+([a-zA-Z]+)', prompt, re.IGNORECASE)
    if name_match:
        candidate = name_match.group(1).strip()
        if candidate.lower() not in ["email", "gmail", "good", "happy", "mail", "message", "a", "an", "the", "apology"]:
            recipient_name = candidate.capitalize()

    p_lower = prompt.lower()

    # 3. AI Email Writer Generation if Subject or Body is missing
    if not subject_val or not body_val:
        from app.services.ai_email_writer import ai_email_writer
        ai_generated = ai_email_writer.generate_email_content(prompt)
        if not subject_val:
            subject_val = ai_generated.get("subject", "AgentFlow Automated Email Notice")
        if not body_val:
            body_val = ai_generated.get("body", "Hello,\n\nThis email was generated automatically by AgentFlow AI.\n\nRegards,\nAgentFlow")

    subject_val = re.sub(r"[\r\n]+", " ", subject_val).strip()
    body_val = body_val.replace("\r", "").strip()

    # 5. Remove any accidentally embedded label prefixes from values
    for label_prefix in [r"(?i)^to:\s*", r"(?i)^subject:\s*", r"(?i)^body:\s*"]:
        to_val = re.sub(label_prefix, "", to_val).strip()
        subject_val = re.sub(label_prefix, "", subject_val).strip()
        body_val = re.sub(label_prefix, "", body_val).strip()

    # 6. Final Header Safety: Strict enforcement of no \r or \n in 'to' and 'subject'
    to_val = re.sub(r"[\r\n]+", "", to_val).strip()
    subject_val = re.sub(r"[\r\n]+", " ", subject_val).strip()

    logger.info(f"[AUTH-12] Extracted Gmail parameters: to='{to_val}' subject='{subject_val}' body_len={len(body_val)}")

    return {
        "to": to_val,
        "subject": subject_val,
        "body": body_val,
    }
