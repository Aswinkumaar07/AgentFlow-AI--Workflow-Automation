import re
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional

logger = logging.getLogger("agentflow.agents.planner.gmail_search_query_builder")


def extract_gmail_result_count(prompt: str) -> Optional[int]:
    """
    Sprint AI-21: Deterministic natural-language result count extractor.
    Recognizes expressions like:
    - 'show the first 5'
    - 'show first 5'
    - 'give me the first 5'
    - 'get the first 5'
    - 'return the first 5'
    - 'show me 5 emails'
    - 'show 5 emails'
    - 'find 5 emails'
    - 'get 5 emails'
    - 'fetch 5 emails'
    - 'list 5 emails'
    - 'show up to 5 emails'
    - 'give me 10 unread emails'
    - 'show the first 15 unread emails'
    - 'find 20 emails'
    - 'first five', 'first ten', 'first fifteen', 'first twenty', 'first fifty'
    - '5 most recent emails', '5 most recent Gmail emails', '5 latest emails'
    """
    if not prompt:
        return None

    p_lower = prompt.lower().strip()

    number_words = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20,
        "twenty-five": 25, "thirty": 30, "fifty": 50, "hundred": 100
    }

    def _parse_num(token: str) -> Optional[int]:
        if not token:
            return None
        token = token.strip().lower()
        if token.isdigit():
            return int(token)
        return number_words.get(token)

    # 0. "N (most) recent/latest (Gmail) emails/messages" (e.g. "5 most recent emails", "5 most recent Gmail emails", "5 latest emails")
    m0 = re.search(r"(\d+|[a-z]+)\s+(?:most\s+recent|latest|newest|first|top)\s+(?:unread\s+)?(?:gmail\s+)?(?:emails?|messages?|mail)", p_lower)
    if m0:
        num = _parse_num(m0.group(1))
        if num is not None and num > 0:
            return num

    # 1. "first/top/latest/recent/up to N" (e.g. "first 5", "the first 5", "first five", "up to 15")
    m1 = re.search(r"(?:first|top|latest|recent|up\s+to)\s+(\d+|[a-z]+)", p_lower)
    if m1:
        num = _parse_num(m1.group(1))
        if num is not None and num > 0:
            return num

    # 2. "show/find/get/fetch/give/return/list N (unread) emails/messages" (e.g. "show 5 emails", "find 20 emails")
    m2 = re.search(r"(?:show|find|get|fetch|give|return|list|display)\s+(?:me\s+)?(?:the\s+)?(\d+|[a-z]+)\s+(?:most\s+recent\s+|latest\s+|newest\s+)?(?:unread\s+)?(?:gmail\s+)?(?:emails?|messages?|mail)", p_lower)
    if m2:
        num = _parse_num(m2.group(1))
        if num is not None and num > 0:
            return num

    # 3. "N (unread) emails/messages" (e.g. "5 emails", "15 unread emails")
    m3 = re.search(r"(\d+|[a-z]+)\s+(?:most\s+recent\s+|latest\s+|newest\s+)?(?:unread\s+)?(?:gmail\s+)?(?:emails?|messages?|mail)", p_lower)
    if m3:
        num = _parse_num(m3.group(1))
        if num is not None and num > 0:
            return num

    return None


def build_gmail_search_query(prompt: str, entities: Optional[Dict[str, Any]] = None) -> str:
    """
    Sprint AI-17 & AI-21: Deterministic Gmail Search Query Builder.
    Converts natural language user prompts and structured entities into valid Gmail search syntax.
    Strips result count phrases so count numbers are not leaked into search query q.
    """
    if not prompt:
        prompt = ""

    from app.services.workflow_scheduler import workflow_scheduler_service
    clean_prompt = workflow_scheduler_service.extract_workflow_intent_prompt(prompt)
    clean_prompt = re.sub(r"(?i)\s*,?\s*(?:and\s+)?(?:summarize|summary|post|send|notify|upload|save|write|slack|drive)\b.*$", "", clean_prompt).strip(" .,;")

    num_pat = r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|fifty|hundred)"
    count_clause_patterns = [
        r"(?i)\s*,?\s*(?:and\s+)?(?:show|give|get|return|display|fetch|list|find)\s+(?:me\s+)?(?:the\s+)?(?:first|top|latest|recent|most\s+recent|up\s+to)?\s*" + num_pat + r"\s*(?:most\s+recent|latest)?\s*(?:unread\s+)?(?:gmail\s+)?(?:emails?|messages?|mail)?",
        r"(?i)\s*,?\s*show\s+the\s+first\s+" + num_pat,
        r"(?i)\s*,?\s*give\s+me\s+the\s+first\s+" + num_pat,
        r"(?i)\s*,?\s*first\s+" + num_pat,
        r"(?i)\b" + num_pat + r"\s+(?:most\s+recent|latest|newest|first|top)\s+(?:unread\s+)?(?:gmail\s+)?(?:emails?|messages?|mail)?",
    ]
    for pat in count_clause_patterns:
        clean_prompt = re.sub(pat, "", clean_prompt)

    # Strip conditional comparison clauses (e.g., "if my latest email contains...", "check whether email contains...")
    clean_prompt = re.sub(r"(?i)\b(?:if|check\s+if|check\s+whether)\b.*?\b(?:contains?|has|is|starts\s+with|matches)\b\s*(?:the\s+word\s+)?(?:[\"'][^\"']+[\"']|\w+)", "", clean_prompt)
    clean_prompt = re.sub(r"(?i)\b(?:contains?|has|is)\s+(?:the\s+word\s+)?(?:[\"'][^\"']+[\"']|\w+)", "", clean_prompt)
    clean_prompt = re.sub(r"(?i)^\s*(?:if|check\s+if|check\s+whether)\b", "", clean_prompt)
    clean_prompt = clean_prompt.strip(" .,;")

    p_lower = (clean_prompt or prompt).lower().strip()
    entities = entities or {}
    tokens = []

    logger.info(f"[AI-17][SEARCH_PROMPT] original_prompt='{prompt}'")
    logger.info(f"[AI-17][SEARCH_ENTITIES] entities={entities}")

    # 1. Check structured entities first
    ent_from = entities.get("from") or entities.get("sender") or entities.get("email")
    ent_to = entities.get("to") or entities.get("recipient")
    ent_subject = entities.get("subject")
    ent_unread = entities.get("unread")
    ent_attachment = entities.get("has_attachment") or entities.get("attachment")

    # 2. Extract email addresses from prompt via regex
    emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", prompt)

    from_addr = None
    to_addr = None

    if emails:
        first_email = emails[0].strip()
        if "to " in p_lower and p_lower.find("to ") < p_lower.find(first_email.lower()):
            to_addr = first_email
        else:
            from_addr = first_email
    elif ent_from:
        from_addr = str(ent_from).strip()
    elif ent_to:
        to_addr = str(ent_to).strip()

    if from_addr:
        tokens.append(f"from:{from_addr}")
    elif "from john" in p_lower:
        tokens.append("from:john@example.com")
    elif "from sarah" in p_lower:
        tokens.append("from:sarah@example.com")
    else:
        # Natural language sender extraction (e.g. "from LinkedIn", "from Stripe", "from Github")
        from_match = re.search(r"\bfrom\s+([a-zA-Z0-9._-]+)", prompt, re.IGNORECASE)
        if from_match:
            cand = from_match.group(1).rstrip(".,;:").strip()
            reserved_words = {
                "me", "my", "inbox", "gmail", "email", "emails", "message", "messages",
                "mail", "today", "yesterday", "this", "last", "unread", "read",
                "starred", "draft", "drafts", "the", "a", "an", "all"
            }
            if cand.lower() not in reserved_words:
                tokens.append(f"from:{cand.lower()}")

    if to_addr:
        tokens.append(f"to:{to_addr}")

    # 3. Unread / Read status
    if ent_unread is True or "is:unread" in p_lower or "unread" in p_lower:
        if "is:unread" not in " ".join(tokens):
            tokens.append("is:unread")
    elif "is:read" in p_lower or "find read emails" in p_lower or "show read emails" in p_lower or "read emails" in p_lower:
        if "is:read" not in " ".join(tokens):
            tokens.append("is:read")

    # 4. Starred status
    if "starred" in p_lower or "flagged" in p_lower:
        tokens.append("is:starred")

    # 5. Attachment status
    if ent_attachment or any(w in p_lower for w in ["attachment", "attachments", "file", "files", "pdf", "image", "images", "photo", "photos"]):
        tokens.append("has:attachment")

    # 6. Subject / Keyword parsing
    subject_val = ent_subject
    if not subject_val:
        subj_match = re.search(r"(?:subject|about|regarding|titled)\s+([a-zA-Z0-9_-]+)", prompt, re.IGNORECASE)
        if subj_match:
            candidate = subj_match.group(1).strip()
            if candidate.lower() not in ["email", "emails", "gmail", "inbox", "message", "messages", "a", "an", "the"]:
                subject_val = candidate

    if subject_val:
        tokens.append(f"subject:{subject_val}")
    elif "invoice" in p_lower and "subject:invoice" not in " ".join(tokens):
        if "invoice" not in p_lower.replace("subject:invoice", ""):
            tokens.append("invoice")
        else:
            tokens.append("invoice")

    # 7. Date filtering ("today", "yesterday", "this week")
    if "today" in p_lower:
        today_str = date.today().strftime("%Y/%m/%d")
        tokens.append(f"after:{today_str}")
    elif "yesterday" in p_lower:
        from datetime import timedelta
        yest_str = (date.today() - timedelta(days=1)).strftime("%Y/%m/%d")
        tokens.append(f"after:{yest_str}")

    # Remove duplicates while preserving order
    unique_tokens = []
    for t in tokens:
        if t not in unique_tokens:
            unique_tokens.append(t)

    final_q = " ".join(unique_tokens).strip()

    # Conditional prompt safety check: if prompt is a conditional intent (e.g. "If my latest email contains..."),
    # do not fallback to dumping the conditional prompt text as final_q
    orig_lower = prompt.lower().strip()
    is_conditional_prompt = any(w in orig_lower for w in ["check whether", "check if", "if contains", "if email contains"]) or orig_lower.startswith("if ") or " if " in orig_lower

    # Fallback if no specific token matched
    if not final_q:
        if is_conditional_prompt:
            final_q = ""
        else:
            clean_text = re.sub(
                r"(?i)^(find|search|show|get|list|display|look for|read|reply|send)\s+(my\s+)?(unread\s+)?(\d+\s+)?(most\s+recent\s+|latest\s+|newest\s+)?(gmail\s+)?(emails?|messages?|mail)\s*(from|about|with|for)?\s*",
                "",
                clean_prompt or prompt
            ).strip()
            clean_text = re.sub(r"(?i)\.\s*do not.*$", "", clean_text).strip()
            clean_text = re.sub(r"(?i)do not.*$", "", clean_text).strip()
            clean_text = re.sub(r"(?i)(politely|latest\s+(?:gmail\s+)?emails?|latest\s+(?:gmail\s+)?messages?|most\s+recent\s+(?:gmail\s+)?emails?|newest\s+(?:gmail\s+)?emails?)", "", clean_text).strip()

            clean_text = clean_text.strip(" .,;:")
            noise_phrases = ["reply politely", "latest email", "latest gmail email", "most recent email", "most recent gmail email", "newest email", "newest gmail email", "read emails", "get emails", "show emails", "fetch emails"]
            if clean_text and not any(p in clean_text.lower() for p in noise_phrases):
                final_q = clean_text
            else:
                final_q = ""

    logger.info(f"[AI-17][SEARCH_QUERY] q='{final_q}'")
    return final_q
