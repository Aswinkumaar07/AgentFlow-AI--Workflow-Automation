"""
AgentFlow AI — Enterprise Dynamic Connector Schema Registry
Provides standardized, n8n-parity operation definitions and parameter schemas for all 16 core connectors.
"""

from typing import Dict, List
from app.connectors.models import (
    ConnectorMetadataModel,
    OperationSchemaModel,
    ParameterSchemaModel,
)

# ─────────────────────────────────────────────────────────────────────────────
# 1. GMAIL
# ─────────────────────────────────────────────────────────────────────────────
GMAIL_METADATA = ConnectorMetadataModel(
    provider="Gmail",
    display_name="Google Gmail",
    icon="gmail",
    auth_type="OAuth2",
    supported_operations=[
        "gmail.messages.send",
        "gmail.messages.list",
        "gmail.messages.get",
        "gmail.messages.search",
        "gmail.messages.reply",
        "gmail.messages.forward",
        "gmail.messages.delete",
        "gmail.messages.mark_read",
        "gmail.messages.mark_unread",
        "gmail.labels.list",
        "gmail.labels.modify",
        "gmail.drafts.create",
        "gmail.drafts.send",
        "gmail.attachments.download",
    ],
    categories=["Communication", "Email"],
    version="1.0.0",
    documentation_url="https://developers.google.com/gmail/api",
    operation_schemas={
        "gmail.messages.send": OperationSchemaModel(
            id="gmail.messages.send",
            display_name="Send Email",
            description="Sends an email message with recipient, subject, body, CC, BCC, and attachment parameters.",
            required_parameters=[
                ParameterSchemaModel(name="to", display_name="To Recipient", type="email", required=True, description="Recipient email address"),
                ParameterSchemaModel(name="subject", display_name="Subject", type="text", required=True, description="Email subject line"),
                ParameterSchemaModel(name="body", display_name="Message Body", type="textarea", required=True, description="Email content in plain text or HTML"),
            ],
            optional_parameters=[
                ParameterSchemaModel(name="cc", display_name="CC Recipient", type="email", required=False, description="Carbon copy recipient email"),
                ParameterSchemaModel(name="bcc", display_name="BCC Recipient", type="email", required=False, description="Blind carbon copy recipient email"),
                ParameterSchemaModel(name="reply_to", display_name="Reply-To", type="email", required=False, description="Reply-To email address"),
                ParameterSchemaModel(name="html", display_name="HTML Body", type="textarea", required=False, description="Rich HTML email body content"),
                ParameterSchemaModel(name="attachments", display_name="Attachments", type="file", required=False, description="File attachment or URL"),
            ],
            default_values={"to": "user@example.com"},
        ),
        "gmail.messages.list": OperationSchemaModel(
            id="gmail.messages.list",
            display_name="List Messages",
            description="Retrieves a list of messages matching a Gmail query.",
            required_parameters=[],
            optional_parameters=[
                ParameterSchemaModel(name="q", display_name="Search Query", type="string", required=False, description="Gmail search query", default_value="is:unread"),
                ParameterSchemaModel(name="max_results", display_name="Max Results", type="number", required=False, description="Maximum messages to fetch", default_value=10),
            ],
            default_values={"q": "is:unread", "max_results": 10},
        ),
        "gmail.messages.get": OperationSchemaModel(
            id="gmail.messages.get",
            display_name="Get Message Details",
            description="Fetches full payload and headers for a specific Gmail message ID.",
            required_parameters=[
                ParameterSchemaModel(name="message_id", display_name="Message ID", type="string", required=True, description="Gmail message unique ID"),
            ],
            optional_parameters=[],
            default_values={"message_id": "{{step_1.id}}"},
        ),
        "gmail.messages.search": OperationSchemaModel(
            id="gmail.messages.search",
            display_name="Search Emails",
            description="Searches Gmail messages using natural language queries and filters.",
            required_parameters=[
                ParameterSchemaModel(name="q", display_name="Search Query", type="string", required=True, description="Search query string"),
            ],
            optional_parameters=[],
            default_values={"q": "invoice"},
        ),
        "gmail.messages.reply": OperationSchemaModel(
            id="gmail.messages.reply",
            display_name="Reply to Email",
            description="Sends a threaded reply to an existing email message.",
            required_parameters=[
                ParameterSchemaModel(name="message_id", display_name="Message ID", type="string", required=True, description="Target message ID"),
                ParameterSchemaModel(name="body", display_name="Reply Body", type="textarea", required=True, description="Reply body text"),
            ],
            optional_parameters=[],
            default_values={"body": "Thank you for your message."},
        ),
        "gmail.messages.forward": OperationSchemaModel(
            id="gmail.messages.forward",
            display_name="Forward Email",
            description="Forwards an existing email message to a new recipient.",
            required_parameters=[
                ParameterSchemaModel(name="message_id", display_name="Message ID", type="string", required=True, description="Target message ID"),
                ParameterSchemaModel(name="to", display_name="Forward To", type="email", required=True, description="Recipient email address"),
            ],
            optional_parameters=[],
            default_values={"to": "recipient@example.com"},
        ),
        "gmail.messages.delete": OperationSchemaModel(
            id="gmail.messages.delete",
            display_name="Delete Email",
            description="Permanently deletes or trashes a Gmail message.",
            required_parameters=[
                ParameterSchemaModel(name="message_id", display_name="Message ID", type="string", required=True, description="Target message ID"),
            ],
            optional_parameters=[],
            default_values={"message_id": "{{step_1.id}}"},
        ),
        "gmail.messages.mark_read": OperationSchemaModel(
            id="gmail.messages.mark_read",
            display_name="Mark as Read",
            description="Marks a message as read by removing UNREAD label.",
            required_parameters=[
                ParameterSchemaModel(name="message_id", display_name="Message ID", type="string", required=True, description="Target message ID"),
            ],
            optional_parameters=[],
            default_values={"message_id": "{{step_1.id}}"},
        ),
        "gmail.messages.mark_unread": OperationSchemaModel(
            id="gmail.messages.mark_unread",
            display_name="Mark as Unread",
            description="Marks a message as unread by adding UNREAD label.",
            required_parameters=[
                ParameterSchemaModel(name="message_id", display_name="Message ID", type="string", required=True, description="Target message ID"),
            ],
            optional_parameters=[],
            default_values={"message_id": "{{step_1.id}}"},
        ),
        "gmail.labels.list": OperationSchemaModel(
            id="gmail.labels.list",
            display_name="List Labels",
            description="Lists all user and system labels in Gmail account.",
            required_parameters=[],
            optional_parameters=[],
            default_values={},
        ),
        "gmail.labels.modify": OperationSchemaModel(
            id="gmail.labels.modify",
            display_name="Modify Labels",
            description="Adds or removes labels from a Gmail message.",
            required_parameters=[
                ParameterSchemaModel(name="message_id", display_name="Message ID", type="string", required=True, description="Target message ID"),
            ],
            optional_parameters=[],
            default_values={"message_id": "{{step_1.id}}"},
        ),
        "gmail.drafts.create": OperationSchemaModel(
            id="gmail.drafts.create",
            display_name="Create Draft",
            description="Creates a new draft email message without sending.",
            required_parameters=[
                ParameterSchemaModel(name="subject", display_name="Subject", type="string", required=True, description="Draft subject"),
                ParameterSchemaModel(name="body", display_name="Body", type="textarea", required=True, description="Draft body content"),
            ],
            optional_parameters=[],
            default_values={"subject": "Draft Subject", "body": "Draft Body"},
        ),
        "gmail.drafts.send": OperationSchemaModel(
            id="gmail.drafts.send",
            display_name="Send Draft",
            description="Dispatches a previously created draft email.",
            required_parameters=[
                ParameterSchemaModel(name="draft_id", display_name="Draft ID", type="string", required=True, description="Target draft ID"),
            ],
            optional_parameters=[],
            default_values={"draft_id": "draft_123"},
        ),
        "gmail.attachments.download": OperationSchemaModel(
            id="gmail.attachments.download",
            display_name="Download Attachment",
            description="Downloads an email attachment to local disk.",
            required_parameters=[
                ParameterSchemaModel(name="message_id", display_name="Message ID", type="string", required=True, description="Target message ID"),
                ParameterSchemaModel(name="attachment_id", display_name="Attachment ID", type="string", required=True, description="Attachment ID"),
            ],
            optional_parameters=[],
            default_values={"filename": "attachment.pdf"},
        ),
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. GOOGLE DRIVE
# ─────────────────────────────────────────────────────────────────────────────
DRIVE_METADATA = ConnectorMetadataModel(
    provider="Google Drive",
    display_name="Google Drive",
    icon="drive",
    auth_type="OAuth2",
    supported_operations=["drive.files.list", "drive.files.get", "drive.files.create"],
    categories=["Storage", "Files"],
    version="1.0.0",
    documentation_url="https://developers.google.com/drive/api",
    operation_schemas={
        "drive.files.list": OperationSchemaModel(
            id="drive.files.list",
            display_name="List / Search Files",
            description="Queries files in Google Drive folder.",
            required_parameters=[],
            optional_parameters=[
                ParameterSchemaModel(name="q", display_name="Query Filter", type="string", required=False, description="Drive query string (e.g. mimeType='application/pdf')", default_value="trashed = false"),
                ParameterSchemaModel(name="page_size", display_name="Page Size", type="number", required=False, description="Maximum files returned", default_value=20),
            ],
            default_values={"q": "trashed = false", "page_size": 20},
        ),
        "drive.files.get": OperationSchemaModel(
            id="drive.files.get",
            display_name="Get File Details",
            description="Fetches file metadata for a specific Google Drive file ID.",
            required_parameters=[
                ParameterSchemaModel(name="file_id", display_name="File ID", type="string", required=True, description="Google Drive file ID"),
            ],
            optional_parameters=[],
            default_values={"file_id": "file_drive_001"},
        ),
        "drive.files.create": OperationSchemaModel(
            id="drive.files.create",
            display_name="Upload / Create File",
            description="Uploads a new file or creates a document in Google Drive.",
            required_parameters=[
                ParameterSchemaModel(name="name", display_name="File Name", type="string", required=True, description="Target filename (e.g. Invoice_2026.pdf)"),
            ],
            optional_parameters=[
                ParameterSchemaModel(name="folder_id", display_name="Folder ID", type="string", required=False, description="Google Drive target folder ID", default_value="root"),
                ParameterSchemaModel(name="mime_type", display_name="MIME Type", type="string", required=False, description="File MIME type (e.g. application/pdf)", default_value="application/pdf"),
                ParameterSchemaModel(name="content", display_name="File Content", type="text", required=False, description="Base64 encoded content or URL"),
            ],
            default_values={"name": "Report_{{$now}}.pdf", "folder_id": "root", "mime_type": "application/pdf"},
        ),
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# 3. GOOGLE SHEETS
# ─────────────────────────────────────────────────────────────────────────────
SHEETS_METADATA = ConnectorMetadataModel(
    provider="Google Sheets",
    display_name="Google Sheets",
    icon="sheets",
    auth_type="OAuth2",
    supported_operations=["sheets.values.get", "sheets.values.append", "sheets.values.update"],
    categories=["Productivity", "Spreadsheet"],
    version="1.0.0",
    documentation_url="https://developers.google.com/sheets/api",
    operation_schemas={
        "sheets.values.get": OperationSchemaModel(
            id="sheets.values.get",
            display_name="Read Spreadsheet Rows",
            description="Reads cell values from a specific Google Sheet range.",
            required_parameters=[
                ParameterSchemaModel(name="spreadsheet_id", display_name="Spreadsheet ID", type="string", required=True, description="ID found in Google Sheet URL"),
                ParameterSchemaModel(name="range", display_name="Cell Range", type="string", required=True, description="A1 notation range (e.g. Sheet1!A1:Z100)"),
            ],
            optional_parameters=[],
            default_values={"spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms", "range": "Sheet1!A1:Z100"},
        ),
        "sheets.values.append": OperationSchemaModel(
            id="sheets.values.append",
            display_name="Append Row",
            description="Appends new row data to the bottom of a Google Sheet.",
            required_parameters=[
                ParameterSchemaModel(name="spreadsheet_id", display_name="Spreadsheet ID", type="string", required=True, description="ID found in Google Sheet URL"),
                ParameterSchemaModel(name="range", display_name="Sheet Name / Range", type="string", required=True, description="Target sheet name (e.g. Sheet1)"),
                ParameterSchemaModel(name="values", display_name="Row Values", type="json", required=True, description="Array of cell values for the row"),
            ],
            optional_parameters=[],
            default_values={"spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms", "range": "Sheet1", "values": ["{{$now}}", "{{$json.name}}", "{{$json.email}}"]},
        ),
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# 4. SLACK
# ─────────────────────────────────────────────────────────────────────────────
SLACK_METADATA = ConnectorMetadataModel(
    provider="Slack",
    display_name="Slack API",
    icon="slack",
    auth_type="OAuth2",
    supported_operations=["slack.chat.postMessage", "slack.channels.list", "slack.users.list"],
    categories=["Communication", "Chat"],
    version="1.0.0",
    documentation_url="https://api.slack.com/methods",
    operation_schemas={
        "slack.chat.postMessage": OperationSchemaModel(
            id="slack.chat.postMessage",
            display_name="Post Message to Channel",
            description="Posts a rich text or markdown message to a Slack channel or direct user.",
            required_parameters=[
                ParameterSchemaModel(name="channel", display_name="Channel Name / ID", type="string", required=True, description="Slack channel (e.g. #dev-alerts, #general)"),
                ParameterSchemaModel(name="text", display_name="Message Text", type="text", required=True, description="Message content in Slack markdown format"),
            ],
            optional_parameters=[
                ParameterSchemaModel(name="bot_name", display_name="Bot Display Name", type="string", required=False, description="Custom bot sender name"),
                ParameterSchemaModel(name="icon_emoji", display_name="Bot Emoji Icon", type="string", required=False, description="Emoji icon (e.g. :robot_face:)"),
            ],
            default_values={"channel": "#dev-alerts", "text": "⚡ *AgentFlow Alert*: Workflow execution completed successfully.", "icon_emoji": ":robot_face:"},
        ),
        "slack.channels.list": OperationSchemaModel(
            id="slack.channels.list",
            display_name="List Channels",
            description="Returns all public and private channels in the Slack workspace.",
            required_parameters=[],
            optional_parameters=[
                ParameterSchemaModel(name="types", display_name="Channel Types", type="string", required=False, description="Comma-separated channel types", default_value="public_channel,private_channel"),
            ],
            default_values={"types": "public_channel,private_channel"},
        ),
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# 5. GITHUB
# ─────────────────────────────────────────────────────────────────────────────
GITHUB_METADATA = ConnectorMetadataModel(
    provider="GitHub",
    display_name="GitHub API v3",
    icon="github",
    auth_type="OAuth2",
    supported_operations=["github.issues.search", "github.issues.get", "github.issues.create"],
    categories=["Developer Tools", "Version Control"],
    version="1.0.0",
    documentation_url="https://docs.github.com/en/rest",
    operation_schemas={
        "github.issues.search": OperationSchemaModel(
            id="github.issues.search",
            display_name="Search Issues / PRs",
            description="Searches GitHub issues and pull requests matching a query.",
            required_parameters=[
                ParameterSchemaModel(name="q", display_name="Search Query", type="string", required=True, description="GitHub search query string (e.g. repo:AgentFlow-AI/TERRAWATCH is:issue state:open)"),
            ],
            optional_parameters=[],
            default_values={"q": "repo:AgentFlow-AI/TERRAWATCH is:issue state:open"},
        ),
        "github.issues.get": OperationSchemaModel(
            id="github.issues.get",
            display_name="Get Issue Details",
            description="Retrieves full details for a single issue in a GitHub repository.",
            required_parameters=[
                ParameterSchemaModel(name="repo", display_name="Repository (owner/repo)", type="string", required=True, description="Full repository identifier (e.g. AgentFlow-AI/TERRAWATCH)"),
                ParameterSchemaModel(name="issue_number", display_name="Issue Number", type="number", required=True, description="Target issue number"),
            ],
            optional_parameters=[],
            default_values={"repo": "AgentFlow-AI/TERRAWATCH", "issue_number": 1},
        ),
        "github.issues.create": OperationSchemaModel(
            id="github.issues.create",
            display_name="Create Issue",
            description="Creates a new issue in a GitHub repository.",
            required_parameters=[
                ParameterSchemaModel(name="repo", display_name="Repository (owner/repo)", type="string", required=True, description="Full repository identifier (e.g. AgentFlow-AI/TERRAWATCH)"),
                ParameterSchemaModel(name="title", display_name="Issue Title", type="string", required=True, description="Title of the issue"),
            ],
            optional_parameters=[
                ParameterSchemaModel(name="body", display_name="Issue Description", type="text", required=False, description="Markdown body content"),
                ParameterSchemaModel(name="labels", display_name="Labels", type="array", required=False, description="List of label strings"),
                ParameterSchemaModel(name="assignees", display_name="Assignees", type="array", required=False, description="List of GitHub usernames"),
            ],
            default_values={"repo": "AgentFlow-AI/TERRAWATCH", "title": "Automated Alert: Bug detected in pipeline", "body": "Reported via AgentFlow AI Engine."},
        ),
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# 6. NOTION
# ─────────────────────────────────────────────────────────────────────────────
NOTION_METADATA = ConnectorMetadataModel(
    provider="Notion",
    display_name="Notion API",
    icon="notion",
    auth_type="OAuth2",
    supported_operations=["notion.databases.query", "notion.pages.get", "notion.pages.create"],
    categories=["Productivity", "Documentation"],
    version="1.0.0",
    documentation_url="https://developers.notion.com/",
    operation_schemas={
        "notion.databases.query": OperationSchemaModel(
            id="notion.databases.query",
            display_name="Query Database",
            description="Queries items from a Notion database with filters.",
            required_parameters=[
                ParameterSchemaModel(name="database_id", display_name="Database ID", type="string", required=True, description="Notion target database ID"),
            ],
            optional_parameters=[
                ParameterSchemaModel(name="filter", display_name="Filter Rules", type="json", required=False, description="Notion API filter JSON object"),
            ],
            default_values={"database_id": "db_notion_demo_101"},
        ),
        "notion.pages.get": OperationSchemaModel(
            id="notion.pages.get",
            display_name="Get Page Details",
            description="Retrieves metadata and page properties for a specific Notion page ID.",
            required_parameters=[
                ParameterSchemaModel(name="page_id", display_name="Page ID", type="string", required=True, description="Notion target page ID"),
            ],
            optional_parameters=[],
            default_values={"page_id": "page_notion_demo_001"},
        ),
        "notion.pages.create": OperationSchemaModel(
            id="notion.pages.create",
            display_name="Create Page in Database",
            description="Creates a new page item inside a Notion database.",
            required_parameters=[
                ParameterSchemaModel(name="database_id", display_name="Database ID", type="string", required=True, description="Notion target database ID"),
                ParameterSchemaModel(name="title", display_name="Page Title", type="string", required=True, description="Title property value"),
            ],
            optional_parameters=[
                ParameterSchemaModel(name="properties", display_name="Database Properties", type="json", required=False, description="Custom database column properties JSON"),
                ParameterSchemaModel(name="content", display_name="Page Body Content", type="text", required=False, description="Page body text or markdown"),
            ],
            default_values={"database_id": "db_notion_demo_101", "title": "New Task: {{$json.title}}"},
        ),
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# 7. DISCORD
# ─────────────────────────────────────────────────────────────────────────────
DISCORD_METADATA = ConnectorMetadataModel(
    provider="Discord",
    display_name="Discord Webhook & API",
    icon="discord",
    auth_type="Webhook",
    supported_operations=["discord.webhook.send", "discord.messages.post"],
    categories=["Communication", "Chat"],
    version="1.0.0",
    documentation_url="https://discord.com/developers/docs/resources/webhook",
    operation_schemas={
        "discord.webhook.send": OperationSchemaModel(
            id="discord.webhook.send",
            display_name="Send Webhook Message",
            description="Posts a message to a Discord channel via Webhook URL.",
            required_parameters=[
                ParameterSchemaModel(name="webhook_url", display_name="Discord Webhook URL", type="string", required=True, description="Full Discord Webhook endpoint URL"),
                ParameterSchemaModel(name="content", display_name="Message Content", type="text", required=True, description="Message text content (max 2000 chars)"),
            ],
            optional_parameters=[
                ParameterSchemaModel(name="username", display_name="Custom Username", type="string", required=False, description="Sender display name override"),
                ParameterSchemaModel(name="avatar_url", display_name="Avatar Image URL", type="string", required=False, description="Sender avatar icon URL"),
            ],
            default_values={"webhook_url": "https://discord.com/api/webhooks/demo", "content": "🤖 **AgentFlow Notification**: Workflow triggered successfully."},
        ),
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# 8. STRIPE
# ─────────────────────────────────────────────────────────────────────────────
STRIPE_METADATA = ConnectorMetadataModel(
    provider="Stripe",
    display_name="Stripe Connect",
    icon="stripe",
    auth_type="APIKey",
    supported_operations=["stripe.charges.get", "stripe.customers.create", "stripe.payment_intents.create"],
    categories=["Finance", "Payments"],
    version="1.0.0",
    documentation_url="https://stripe.com/docs/api",
    operation_schemas={
        "stripe.charges.get": OperationSchemaModel(
            id="stripe.charges.get",
            display_name="Get Charge Details",
            description="Retrieves transaction details for a Stripe charge ID.",
            required_parameters=[
                ParameterSchemaModel(name="charge_id", display_name="Charge ID", type="string", required=True, description="Stripe charge ID (e.g. ch_3Mv...)"),
            ],
            optional_parameters=[],
            default_values={"charge_id": "ch_3Mv101Demo"},
        ),
        "stripe.customers.create": OperationSchemaModel(
            id="stripe.customers.create",
            display_name="Create Customer",
            description="Creates a new customer profile in Stripe.",
            required_parameters=[
                ParameterSchemaModel(name="email", display_name="Customer Email", type="string", required=True, description="Customer email address"),
            ],
            optional_parameters=[
                ParameterSchemaModel(name="name", display_name="Customer Name", type="string", required=False, description="Full name of customer"),
                ParameterSchemaModel(name="metadata", display_name="Metadata JSON", type="json", required=False, description="Custom key-value metadata"),
            ],
            default_values={"email": "{{$json.email}}", "name": "{{$json.name}}"},
        ),
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# 9. OPENAI
# ─────────────────────────────────────────────────────────────────────────────
OPENAI_METADATA = ConnectorMetadataModel(
    provider="OpenAI",
    display_name="OpenAI Platform",
    icon="openai",
    auth_type="APIKey",
    supported_operations=["openai.chat.completions", "openai.embeddings.create"],
    categories=["AI & ML", "LLM"],
    version="1.0.0",
    documentation_url="https://platform.openai.com/docs/api-reference",
    operation_schemas={
        "openai.chat.completions": OperationSchemaModel(
            id="openai.chat.completions",
            display_name="Chat Completion / LLM Prompt",
            description="Generates text response using GPT-4o or GPT-3.5 models.",
            required_parameters=[
                ParameterSchemaModel(name="prompt", display_name="User Prompt", type="text", required=True, description="Input prompt or instructions for model"),
            ],
            optional_parameters=[
                ParameterSchemaModel(
                    name="model", display_name="Model Selection", type="select", required=False,
                    description="OpenAI model identifier", default_value="gpt-4o",
                    options=[
                        {"label": "GPT-4o (Recommended)", "value": "gpt-4o"},
                        {"label": "GPT-4 Turbo", "value": "gpt-4-turbo"},
                        {"label": "GPT-3.5 Turbo", "value": "gpt-3.5-turbo"},
                    ]
                ),
                ParameterSchemaModel(name="temperature", display_name="Temperature", type="number", required=False, description="Creativity level (0.0 to 1.0)", default_value=0.7),
                ParameterSchemaModel(name="max_tokens", display_name="Max Tokens", type="number", required=False, description="Maximum token generation length", default_value=1000),
            ],
            default_values={"prompt": "Summarize the following text: {{$json.text}}", "model": "gpt-4o", "temperature": 0.7, "max_tokens": 1000},
        ),
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# 10. GENERIC REST
# ─────────────────────────────────────────────────────────────────────────────
GENERIC_REST_METADATA = ConnectorMetadataModel(
    provider="Generic REST API",
    display_name="Generic REST Engine",
    icon="globe",
    auth_type="None",
    supported_operations=["generic.http.request"],
    categories=["Core", "HTTP"],
    version="1.0.0",
    documentation_url="https://developer.mozilla.org/en-US/docs/Web/HTTP",
    operation_schemas={
        "generic.http.request": OperationSchemaModel(
            id="generic.http.request",
            display_name="HTTP Request",
            description="Executes arbitrary HTTP request (GET, POST, PUT, DELETE, PATCH).",
            required_parameters=[
                ParameterSchemaModel(
                    name="method", display_name="HTTP Method", type="select", required=True, description="HTTP verb",
                    default_value="GET",
                    options=[
                        {"label": "GET", "value": "GET"},
                        {"label": "POST", "value": "POST"},
                        {"label": "PUT", "value": "PUT"},
                        {"label": "DELETE", "value": "DELETE"},
                        {"label": "PATCH", "value": "PATCH"},
                    ]
                ),
                ParameterSchemaModel(name="url", display_name="Request URL", type="string", required=True, description="Target HTTP/HTTPS endpoint URL"),
            ],
            optional_parameters=[
                ParameterSchemaModel(name="headers", display_name="HTTP Headers", type="json", required=False, description="Request headers JSON object"),
                ParameterSchemaModel(name="body", display_name="Request Body", type="text", required=False, description="Request payload body"),
            ],
            default_values={"method": "GET", "url": "https://api.github.com/zen", "headers": {"Content-Type": "application/json"}},
        ),
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# 11. WEBHOOK
# ─────────────────────────────────────────────────────────────────────────────
WEBHOOK_METADATA = ConnectorMetadataModel(
    provider="Webhook",
    display_name="Webhook Trigger",
    icon="webhook",
    auth_type="None",
    supported_operations=["webhook.trigger"],
    categories=["Triggers", "Core"],
    version="1.0.0",
    documentation_url="https://agentflow.ai/docs/triggers/webhook",
    operation_schemas={
        "webhook.trigger": OperationSchemaModel(
            id="webhook.trigger",
            display_name="Incoming Webhook Listener",
            description="Receives external HTTP POST webhooks and starts workflow execution.",
            required_parameters=[
                ParameterSchemaModel(name="endpoint", display_name="Webhook Path", type="string", required=True, description="Unique URL endpoint path"),
            ],
            optional_parameters=[
                ParameterSchemaModel(name="secret", display_name="HMAC Verification Secret", type="string", required=False, description="Optional secret key for signature verification"),
            ],
            default_values={"endpoint": "/api/v1/triggers/webhooks/default"},
        ),
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# 12. SCHEDULE
# ─────────────────────────────────────────────────────────────────────────────
SCHEDULE_METADATA = ConnectorMetadataModel(
    provider="Schedule",
    display_name="Cron & Timer Schedule",
    icon="clock",
    auth_type="None",
    supported_operations=["schedule.cron"],
    categories=["Triggers", "Core"],
    version="1.0.0",
    documentation_url="https://agentflow.ai/docs/triggers/schedule",
    operation_schemas={
        "schedule.cron": OperationSchemaModel(
            id="schedule.cron",
            display_name="Cron Expression Trigger",
            description="Triggers workflow on a recurring timer or cron schedule.",
            required_parameters=[
                ParameterSchemaModel(name="cron", display_name="Cron Expression", type="string", required=True, description="Standard 5-part cron syntax (e.g. 0 8 * * 1-5)", default_value="0 8 * * 1-5"),
            ],
            optional_parameters=[
                ParameterSchemaModel(name="timezone", display_name="Timezone", type="string", required=False, description="Target timezone", default_value="UTC"),
            ],
            default_values={"cron": "0 8 * * 1-5", "timezone": "UTC"},
        ),
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# 13. CONDITION
# ─────────────────────────────────────────────────────────────────────────────
CONDITION_METADATA = ConnectorMetadataModel(
    provider="Condition",
    display_name="Conditional Branching (IF/ELSE)",
    icon="git-branch",
    auth_type="None",
    supported_operations=["condition.if", "condition.evaluate"],
    categories=["Logic", "Control Flow"],
    version="1.0.0",
    documentation_url="https://agentflow.ai/docs/nodes/condition",
    operation_schemas={
        "condition.if": OperationSchemaModel(
            id="condition.if",
            display_name="Evaluate IF Condition",
            description="Evaluates logical comparison and branches execution into true_branch or false_branch.",
            required_parameters=[
                ParameterSchemaModel(name="left", display_name="Left Operand", type="string", required=True, description="First expression or variable", default_value="{{step_2.snippet}}"),
                ParameterSchemaModel(
                    name="operator", display_name="Operator", type="select", required=True, description="Logical operator",
                    default_value="contains",
                    options=[
                        {"label": "Contains", "value": "contains"},
                        {"label": "Equals (==)", "value": "equals"},
                        {"label": "Not Equals (!=)", "value": "not_equals"},
                        {"label": "Exists", "value": "exists"},
                        {"label": "Not Exists", "value": "not_exists"},
                        {"label": "Starts With", "value": "starts_with"},
                        {"label": "Ends With", "value": "ends_with"},
                        {"label": "Greater Than (>)", "value": "greater_than"},
                        {"label": "Less Than (<)", "value": "less_than"},
                    ]
                ),
                ParameterSchemaModel(name="right", display_name="Right Operand", type="string", required=True, description="Second comparison value", default_value="urgent"),
            ],
            optional_parameters=[
                ParameterSchemaModel(name="true_branch", display_name="True Branch Target", type="string", required=False, description="Node ID to execute if condition is True"),
                ParameterSchemaModel(name="false_branch", display_name="False Branch Target", type="string", required=False, description="Node ID to execute if condition is False"),
            ],
            default_values={"left": "{{step_2.snippet}}", "operator": "contains", "right": "urgent"},
        ),
        "condition.evaluate": OperationSchemaModel(
            id="condition.evaluate",
            display_name="Evaluate Expression",
            description="Evaluates logical comparison and branches execution into true_branch or false_branch.",
            required_parameters=[
                ParameterSchemaModel(name="left_value", display_name="Left Operand", type="string", required=True, description="First expression or variable"),
                ParameterSchemaModel(
                    name="operator", display_name="Operator", type="select", required=True, description="Logical operator",
                    default_value="contains",
                    options=[
                        {"label": "Contains", "value": "contains"},
                        {"label": "Equals (==)", "value": "equals"},
                        {"label": "Not Equals (!=)", "value": "not_equals"},
                        {"label": "Exists", "value": "exists"},
                        {"label": "Not Exists", "value": "not_exists"},
                        {"label": "Starts With", "value": "starts_with"},
                        {"label": "Ends With", "value": "ends_with"},
                        {"label": "Greater Than (>)", "value": "greater_than"},
                        {"label": "Less Than (<)", "value": "less_than"},
                    ]
                ),
                ParameterSchemaModel(name="right_value", display_name="Right Operand", type="string", required=True, description="Second comparison value"),
            ],
            optional_parameters=[],
            default_values={"left_value": "{{step_2.snippet}}", "operator": "contains", "right_value": "urgent"},
        ),
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# 14. LOOP
# ─────────────────────────────────────────────────────────────────────────────
LOOP_METADATA = ConnectorMetadataModel(
    provider="Loop",
    display_name="Loop Iterator",
    icon="repeat",
    auth_type="None",
    supported_operations=["loop.forEach", "loop.iterator", "loop.process"],
    categories=["Logic", "Control Flow"],
    version="1.0.0",
    documentation_url="https://agentflow.ai/docs/nodes/loop",
    operation_schemas={
        "loop.forEach": OperationSchemaModel(
            id="loop.forEach",
            display_name="For Each Item",
            description="Iterates over an array list, running body nodes for each item.",
            required_parameters=[
                ParameterSchemaModel(name="items", display_name="Input Array", type="string", required=True, description="Array variable to iterate (e.g. {{step_1.messages}})"),
            ],
            optional_parameters=[
                ParameterSchemaModel(name="item_variable", display_name="Item Variable Name", type="string", required=False, description="Variable name for current item in context", default_value="item"),
                ParameterSchemaModel(name="index_variable", display_name="Index Variable Name", type="string", required=False, description="Variable name for current index in context", default_value="index"),
            ],
            default_values={"items": "{{step_1.messages}}", "item_variable": "item", "index_variable": "index"},
        ),
        "loop.iterator": OperationSchemaModel(
            id="loop.iterator",
            display_name="Loop Iterator",
            description="Iterates over an array list, running body nodes for each item.",
            required_parameters=[
                ParameterSchemaModel(name="items", display_name="Input Array", type="string", required=True, description="Array variable to iterate"),
            ],
            optional_parameters=[
                ParameterSchemaModel(name="item_variable", display_name="Item Variable Name", type="string", required=False, description="Variable name for current item in context", default_value="item"),
                ParameterSchemaModel(name="index_variable", display_name="Index Variable Name", type="string", required=False, description="Variable name for current index in context", default_value="index"),
            ],
            default_values={"items": "{{step_1.messages}}", "item_variable": "item", "index_variable": "index"},
        ),
        "loop.process": OperationSchemaModel(
            id="loop.process",
            display_name="Iterate Array",
            description="Iterates over an array list, running downstream nodes for each item.",
            required_parameters=[
                ParameterSchemaModel(name="input_array", display_name="Input Array Expression", type="string", required=True, description="Array variable to iterate (e.g. {{$json.items}})")
            ],
            optional_parameters=[
                ParameterSchemaModel(name="batch_size", display_name="Batch Size", type="number", required=False, description="Number of items per batch", default_value=1)
            ],
            default_values={"input_array": "{{step_1.items}}", "batch_size": 1},
        ),
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# 15. MERGE
# ─────────────────────────────────────────────────────────────────────────────
MERGE_METADATA = ConnectorMetadataModel(
    provider="Merge",
    display_name="Merge Parallel Branches",
    icon="git-merge",
    auth_type="None",
    supported_operations=["merge.process"],
    categories=["Logic", "Control Flow"],
    version="1.0.0",
    documentation_url="https://agentflow.ai/docs/nodes/merge",
    operation_schemas={
        "merge.process": OperationSchemaModel(
            id="merge.process",
            display_name="Combine Parallel Branches",
            description="Waits for parallel branches to complete and merges their outputs.",
            required_parameters=[
                ParameterSchemaModel(
                    name="mode", display_name="Merge Mode", type="select", required=True, description="Merge strategy",
                    default_value="Wait for All",
                    options=[
                        {"label": "Wait for All Branches", "value": "Wait for All"},
                        {"label": "First Branch Completed", "value": "First Completed"},
                        {"label": "Combine Objects", "value": "Combine Objects"},
                    ]
                ),
            ],
            optional_parameters=[],
            default_values={"mode": "Wait for All"},
        ),
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# 16. APPROVAL
# ─────────────────────────────────────────────────────────────────────────────
APPROVAL_METADATA = ConnectorMetadataModel(
    provider="Approval",
    display_name="Human in the Loop Approval",
    icon="user-check",
    auth_type="None",
    supported_operations=["approval.request"],
    categories=["Human-in-the-Loop", "Core"],
    version="1.0.0",
    documentation_url="https://agentflow.ai/docs/nodes/approval",
    operation_schemas={
        "approval.request": OperationSchemaModel(
            id="approval.request",
            display_name="Request Human Approval",
            description="Pauses workflow execution and sends an approval request via Email/Slack.",
            required_parameters=[
                ParameterSchemaModel(name="approver_email", display_name="Approver Email", type="string", required=True, description="Email address of designated approver"),
                ParameterSchemaModel(name="title", display_name="Approval Request Title", type="string", required=True, description="Title shown to approver"),
            ],
            optional_parameters=[
                ParameterSchemaModel(name="timeout_hours", display_name="Timeout (Hours)", type="number", required=False, description="Hours before automatic rejection", default_value=24),
            ],
            default_values={"approver_email": "manager@company.com", "title": "Approval Required: Large Transfer Request", "timeout_hours": 24},
        ),
    },
)

# ─────────────────────────────────────────────────────────────────────────────
# 17. AI & LLM SERVICES
# ─────────────────────────────────────────────────────────────────────────────
AI_METADATA = ConnectorMetadataModel(
    provider="AI",
    display_name="AI & LLM Services",
    icon="brain",
    auth_type="None",
    supported_operations=["ai.summarize", "ai.email_writer", "ai.classify", "ai.extract"],
    categories=["AI & ML"],
    version="1.0.0",
    documentation_url="https://agentflow.ai/docs/nodes/ai",
    operation_schemas={
        "ai.summarize": OperationSchemaModel(
            id="ai.summarize",
            display_name="AI Summarization",
            description="Summarizes input text using AI LLM models.",
            required_parameters=[
                ParameterSchemaModel(name="text", display_name="Input Text", type="text", required=True, description="Text to summarize"),
            ],
            optional_parameters=[],
            default_values={"text": "{{step_2.snippet}}"},
        ),
        "ai.email_writer": OperationSchemaModel(
            id="ai.email_writer",
            display_name="AI Email Writer",
            description="Generates an email subject and body from instructions.",
            required_parameters=[
                ParameterSchemaModel(name="instruction", display_name="Instruction", type="text", required=True, description="Prompt instruction"),
            ],
            optional_parameters=[],
            default_values={"instruction": "Write a professional update"},
        ),
    },
)

# ── Global Metadata Map containing all connectors ───────────────────────
ALL_CONNECTOR_METADATA: Dict[str, ConnectorMetadataModel] = {
    "gmail": GMAIL_METADATA,
    "drive": DRIVE_METADATA,
    "sheets": SHEETS_METADATA,
    "slack": SLACK_METADATA,
    "github": GITHUB_METADATA,
    "notion": NOTION_METADATA,
    "discord": DISCORD_METADATA,
    "stripe": STRIPE_METADATA,
    "openai": OPENAI_METADATA,
    "ai": AI_METADATA,
    "generic_rest": GENERIC_REST_METADATA,
    "webhook": WEBHOOK_METADATA,
    "schedule": SCHEDULE_METADATA,
    "condition": CONDITION_METADATA,
    "loop": LOOP_METADATA,
    "merge": MERGE_METADATA,
    "approval": APPROVAL_METADATA,
}
