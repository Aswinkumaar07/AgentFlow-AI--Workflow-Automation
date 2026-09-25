import re
import logging
from typing import Dict, Any

logger = logging.getLogger("agentflow.services.gmail_search_query_translator")


class GmailSearchQueryTranslator:
    """
    Translates natural language search prompts into standard Gmail Search Query strings (`q`).
    """

    def translate_to_gmail_query(self, prompt: str) -> Dict[str, Any]:
        if not prompt:
            return {"query": "is:unread", "max_results": 10}

        p_lower = prompt.lower().strip()

        # 1. Check max results
        max_results = 10
        if "latest" in p_lower or "last email" in p_lower or "recent email" in p_lower:
            max_results = 1

        match_num = re.search(r"\blast\s+(\d+)\s+emails?", p_lower)
        if match_num:
            max_results = int(match_num.group(1))

        # 2. Extract specific operators
        # A. From [Sender] pattern (e.g. "Find emails from Amazon", "Find Amazon emails", "Read emails from John")
        from_match = re.search(r"\b(?:find|search|read)?\s*(?:emails?\s+)?from\s+([a-zA-Z0-9._%+-]+|[a-zA-Z0-9]+)\b", prompt, re.IGNORECASE)
        if not from_match:
            from_match = re.search(r"\b(?:find|search)\s+([a-zA-Z0-9]+)\s+emails?\b", prompt, re.IGNORECASE)
        if from_match:
            candidate = from_match.group(1).rstrip(".,;!?").strip()
            if candidate.lower() not in ["me", "us", "my", "email", "emails", "gmail", "invoices", "invoice", "interview", "interviews", "latest", "unread", "recent", "all", "starred", "important"]:
                return {"query": f"from:{candidate}", "max_results": max_results}

        # B. Subject pattern (e.g. "Find emails with the subject invoice", "subject:invoice")
        subj_match = re.search(r"\b(?:with\s+(?:the\s+)?)?subject\s*[:\s]\s*[\"']?([a-zA-Z0-9._%+-]+)[\"']?", prompt, re.IGNORECASE)
        if subj_match:
            candidate = subj_match.group(1).rstrip(".,;!?").strip()
            if candidate.lower() not in ["line", "header", "text"]:
                return {"query": f"subject:{candidate}", "max_results": max_results}

        # C. Date range patterns
        if "this week" in p_lower or "past week" in p_lower or "last week" in p_lower:
            return {"query": "newer_than:7d", "max_results": max_results}
        if "today" in p_lower:
            return {"query": "newer_than:1d", "max_results": max_results}

        # C. Status and Attachment patterns
        if "attachment" in p_lower or "attachments" in p_lower:
            return {"query": "has:attachment", "max_results": max_results}
        if "unread" in p_lower or "summarize" in p_lower or "summary" in p_lower:
            return {"query": "is:unread", "max_results": max_results}
        if "starred" in p_lower:
            return {"query": "is:starred", "max_results": max_results}
        if "important" in p_lower:
            return {"query": "is:important", "max_results": max_results}

        # D. Specific topic / keyword patterns (e.g., invoices, interview)
        if "invoice" in p_lower or "invoices" in p_lower:
            return {"query": "invoice", "max_results": max_results}
        if "interview" in p_lower or "interviews" in p_lower:
            return {"query": "interview", "max_results": max_results}

        # E. General cleanup fallback
        clean_q = re.sub(r"(?i)\b(find|search|emails|email|show|get|list|fetch|messages|message|my|for|me|all|read|latest|last|recent|\d+)\b", "", prompt)
        clean_q = re.sub(r"[\r\n.]+", " ", clean_q).strip()
        clean_q = re.sub(r"\s+", " ", clean_q)

        final_query = clean_q if clean_q else "is:unread"
        return {"query": final_query, "max_results": max_results}


gmail_search_query_translator = GmailSearchQueryTranslator()
