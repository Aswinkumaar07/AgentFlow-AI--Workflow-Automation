import pytest
from app.agents.intent_classifier import enterprise_intent_classifier, IntentType, IntentClassificationResult


# 100+ Prompt Test Suite across all 23 Supported Intents
PROMPT_TEST_SUITE = [
    # EMAIL_SEND (1-5)
    ("Send an email to john@example.com", IntentType.EMAIL_SEND),
    ("Send message to Sarah regarding project update", IntentType.EMAIL_SEND),
    ("Email Alex with meeting notes", IntentType.EMAIL_SEND),
    ("Mail to manager@company.com", IntentType.EMAIL_SEND),
    ("Send an email to client about invoice status", IntentType.EMAIL_SEND),

    # EMAIL_GENERATE (6-10)
    ("Write an apology email to client", IntentType.EMAIL_GENERATE),
    ("Compose a welcome email for new user Sarah", IntentType.EMAIL_GENERATE),
    ("Generate follow-up email after interview", IntentType.EMAIL_GENERATE),
    ("Draft an email for project launch announcement", IntentType.EMAIL_GENERATE),
    ("Write a polite outreach email to lead", IntentType.EMAIL_GENERATE),

    # EMAIL_REPLY (11-15)
    ("Reply to latest email", IntentType.EMAIL_REPLY),
    ("Reply politely to client message", IntentType.EMAIL_REPLY),
    ("Send reply to msg_12345", IntentType.EMAIL_REPLY),
    ("Reply email from manager", IntentType.EMAIL_REPLY),
    ("Reply politely to the last message received", IntentType.EMAIL_REPLY),

    # EMAIL_FORWARD (16-20)
    ("Forward email to accounting@company.com", IntentType.EMAIL_FORWARD),
    ("Forward invoice email to finance team", IntentType.EMAIL_FORWARD),
    ("Fwd email to boss", IntentType.EMAIL_FORWARD),
    ("Forward message to team", IntentType.EMAIL_FORWARD),
    ("Forward invoice to accounting", IntentType.EMAIL_FORWARD),

    # EMAIL_READ (21-25)
    ("Read email messages", IntentType.EMAIL_READ),
    ("Fetch emails from my inbox", IntentType.EMAIL_READ),
    ("Check inbox for new messages", IntentType.EMAIL_READ),
    ("Get messages from Gmail", IntentType.EMAIL_READ),
    ("Read emails in inbox", IntentType.EMAIL_READ),

    # EMAIL_READ_LATEST (26-30)
    ("Read latest email", IntentType.EMAIL_READ_LATEST),
    ("Read last email received", IntentType.EMAIL_READ_LATEST),
    ("Fetch recent email", IntentType.EMAIL_READ_LATEST),
    ("Check latest email message", IntentType.EMAIL_READ_LATEST),
    ("Read latest message", IntentType.EMAIL_READ_LATEST),

    # EMAIL_READ_UNREAD (31-35)
    ("Read unread emails", IntentType.EMAIL_READ_UNREAD),
    ("Check unread messages", IntentType.EMAIL_READ_UNREAD),
    ("Fetch unread email list", IntentType.EMAIL_READ_UNREAD),
    ("List unread emails", IntentType.EMAIL_READ_UNREAD),
    ("Read unread inbox messages", IntentType.EMAIL_READ_UNREAD),

    # EMAIL_SEARCH (36-40)
    ("Search emails for invoice", IntentType.EMAIL_SEARCH),
    ("Find email regarding contract", IntentType.EMAIL_SEARCH),
    ("Search invoices in inbox", IntentType.EMAIL_SEARCH),
    ("Find interview confirmation email", IntentType.EMAIL_SEARCH),
    ("Query email for tax receipts", IntentType.EMAIL_SEARCH),

    # EMAIL_SEARCH_BY_SENDER (41-45)
    ("Find emails from Amazon", IntentType.EMAIL_SEARCH_BY_SENDER),
    ("Search emails by Stripe", IntentType.EMAIL_SEARCH_BY_SENDER),
    ("Get emails from github@github.com", IntentType.EMAIL_SEARCH_BY_SENDER),
    ("Find messages from Sarah", IntentType.EMAIL_SEARCH_BY_SENDER),
    ("Search emails from boss@company.com", IntentType.EMAIL_SEARCH_BY_SENDER),

    # EMAIL_SEARCH_BY_SUBJECT (46-50)
    ("Find emails with subject 'Quarterly Report'", IntentType.EMAIL_SEARCH_BY_SUBJECT),
    ("Search emails subject 'Billing Statement'", IntentType.EMAIL_SEARCH_BY_SUBJECT),
    ("Get email with subject 'Welcome'", IntentType.EMAIL_SEARCH_BY_SUBJECT),
    ("Search subject 'Meeting Notes'", IntentType.EMAIL_SEARCH_BY_SUBJECT),
    ("Find emails subject 'Invoice #1092'", IntentType.EMAIL_SEARCH_BY_SUBJECT),

    # EMAIL_SUMMARIZE (51-55)
    ("Summarize unread emails", IntentType.EMAIL_SUMMARIZE),
    ("Summarize latest email", IntentType.EMAIL_SUMMARIZE),
    ("Generate email summary for today", IntentType.EMAIL_SUMMARIZE),
    ("Weekly digest of my emails", IntentType.EMAIL_SUMMARIZE),
    ("Monthly digest for executive summary", IntentType.EMAIL_SUMMARIZE),

    # EMAIL_DELETE (56-60)
    ("Delete spam messages", IntentType.EMAIL_DELETE),
    ("Delete email msg_9988", IntentType.EMAIL_DELETE),
    ("Trash email from scammer", IntentType.EMAIL_DELETE),
    ("Purge email message", IntentType.EMAIL_DELETE),
    ("Delete spam email in account", IntentType.EMAIL_DELETE),

    # EMAIL_MARK_READ / EMAIL_MARK_UNREAD (61-68)
    ("Mark email as read", IntentType.EMAIL_MARK_READ),
    ("Mark message read", IntentType.EMAIL_MARK_READ),
    ("Mark unread emails as read", IntentType.EMAIL_MARK_READ),
    ("Mark email as unread", IntentType.EMAIL_MARK_UNREAD),
    ("Mark message unread", IntentType.EMAIL_MARK_UNREAD),
    ("Mark email unread", IntentType.EMAIL_MARK_UNREAD),
    ("Mark read for msg_100", IntentType.EMAIL_MARK_READ),
    ("Mark unread for msg_101", IntentType.EMAIL_MARK_UNREAD),

    # EMAIL_DRAFT (69-73)
    ("Draft email for project sync", IntentType.EMAIL_DRAFT),
    ("Create draft email for client", IntentType.EMAIL_DRAFT),
    ("Save draft message to Sarah", IntentType.EMAIL_DRAFT),
    ("Draft email to team", IntentType.EMAIL_DRAFT),
    ("Create draft for weekly update", IntentType.EMAIL_DRAFT),

    # EMAIL_SCHEDULE (74-78)
    ("Schedule email to be sent tomorrow", IntentType.EMAIL_SCHEDULE),
    ("Schedule reminder for next Monday", IntentType.EMAIL_SCHEDULE),
    ("Schedule email every Monday at 9 AM", IntentType.EMAIL_SCHEDULE),
    ("Send email tomorrow at 9 AM", IntentType.EMAIL_SCHEDULE),
    ("Send email next Monday", IntentType.EMAIL_SCHEDULE),

    # DRIVE_UPLOAD & DRIVE_DOWNLOAD (79-86)
    ("Upload to Drive folder", IntentType.DRIVE_UPLOAD),
    ("Save file to Drive", IntentType.DRIVE_UPLOAD),
    ("Upload attachment to Drive", IntentType.DRIVE_UPLOAD),
    ("Upload invoice to Google Drive", IntentType.DRIVE_UPLOAD),
    ("Download from Drive", IntentType.DRIVE_DOWNLOAD),
    ("Get file from Drive", IntentType.DRIVE_DOWNLOAD),
    ("Download report from Google Drive", IntentType.DRIVE_DOWNLOAD),
    ("Save to Drive folder", IntentType.DRIVE_UPLOAD),

    # SLACK_SEND (87-91)
    ("Notify Slack channel #general", IntentType.SLACK_SEND),
    ("Post message to Slack #engineering", IntentType.SLACK_SEND),
    ("Send Slack notification to user", IntentType.SLACK_SEND),
    ("Post to Slack channel #alerts", IntentType.SLACK_SEND),
    ("Send Slack alert regarding status", IntentType.SLACK_SEND),

    # GITHUB_CREATE_ISSUE (92-96)
    ("Create GitHub issue for bug fix", IntentType.GITHUB_CREATE_ISSUE),
    ("Create issue on GitHub repo", IntentType.GITHUB_CREATE_ISSUE),
    ("New issue for login crash", IntentType.GITHUB_CREATE_ISSUE),
    ("Create GitHub issue for enhancement", IntentType.GITHUB_CREATE_ISSUE),
    ("Create issue on GitHub for API failure", IntentType.GITHUB_CREATE_ISSUE),

    # CALENDAR_CREATE_EVENT (97-101)
    ("Create calendar event for team meeting", IntentType.CALENDAR_CREATE_EVENT),
    ("Schedule meeting on Google Calendar", IntentType.CALENDAR_CREATE_EVENT),
    ("Add event to calendar for tomorrow 10 AM", IntentType.CALENDAR_CREATE_EVENT),
    ("Create calendar event for sprint review", IntentType.CALENDAR_CREATE_EVENT),
    ("Schedule meeting on calendar", IntentType.CALENDAR_CREATE_EVENT),

    # MULTI_STEP_WORKFLOW (102-106)
    ("Read unread emails, summarize them, and send email summary", IntentType.MULTI_STEP_WORKFLOW),
    ("Search invoices, download attachment, upload to Drive, and notify Slack", IntentType.MULTI_STEP_WORKFLOW),
    ("Fetch unread emails, summarize using Gemini, and post to Slack", IntentType.MULTI_STEP_WORKFLOW),
    ("Download invoice, save to Drive, then send Slack alert", IntentType.MULTI_STEP_WORKFLOW),
    ("Read latest email and summarize and notify Slack", IntentType.MULTI_STEP_WORKFLOW),
]


def test_enterprise_intent_classifier_100_plus_prompts():
    assert len(PROMPT_TEST_SUITE) >= 100, f"Expected 100+ prompt test cases, got {len(PROMPT_TEST_SUITE)}"

    passed_count = 0
    for prompt, expected_intent in PROMPT_TEST_SUITE:
        res = enterprise_intent_classifier.classify(prompt)
        assert isinstance(res, IntentClassificationResult)
        assert res.confidence >= 0.50
        assert res.intent == expected_intent, f"Prompt '{prompt}' expected {expected_intent}, got {res.intent} (Reasoning: '{res.reasoning}')"
        passed_count += 1

    assert passed_count == len(PROMPT_TEST_SUITE)


def test_intent_classifier_output_schema_validation():
    sample_prompt = "Send an email to john@example.com"
    res = enterprise_intent_classifier.classify(sample_prompt)

    # Validate Pydantic schema attributes
    res_dict = res.model_dump()
    assert "intent" in res_dict
    assert "confidence" in res_dict
    assert "reasoning" in res_dict
    assert "entities" in res_dict
    assert res.intent == IntentType.EMAIL_SEND
