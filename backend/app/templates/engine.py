import logging
import uuid
import copy
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.agents.validator.workflow_validator import WorkflowValidator
from app.versions.manager import workflow_version_manager

logger = logging.getLogger("agentflow.templates.engine")


class TemplateParameterModel(BaseModel):
    key: str = Field(description="Parameter key identifier")
    label: str = Field(description="Human readable label")
    type: str = Field(default="string", description="Parameter data type: string, number, boolean, select")
    default: Any = Field(default=None, description="Default parameter value")
    required: bool = Field(default=True, description="Whether parameter is required")
    description: str = Field(default="", description="Helpful description for UI")
    options: Optional[List[str]] = Field(default=None, description="Select options if type is select")


class TemplateMetadataModel(BaseModel):
    id: str
    title: str
    description: str
    category: str
    icon: str = "LayoutTemplate"
    connectors: List[str]
    required_providers: List[str]
    estimated_time_ms: float = 45.0
    difficulty: str = "Beginner"  # Beginner, Intermediate, Advanced
    featured: bool = False
    tags: List[str] = []
    use_case: str = ""
    estimated_steps: int = 2
    configurable_parameters: List[TemplateParameterModel] = Field(default_factory=list)
    workflow_spec: Dict[str, Any]


class TemplateEngine:
    """Enterprise Workflow Template Engine serving pre-built workflow templates, parameter customization, and instant DAG instantiation."""

    def __init__(self) -> None:
        self._templates: Dict[str, TemplateMetadataModel] = {}
        self._validator = WorkflowValidator()
        self._seed_templates()

    def _seed_templates(self) -> None:
        templates = [
            TemplateMetadataModel(
                id="tpl_email_summarizer",
                title="Email Summary",
                description="Find recent emails, extract email content, and summarize key insights using AI.",
                category="Email",
                icon="Mail",
                connectors=["gmail", "ai"],
                required_providers=["gmail", "ai"],
                estimated_time_ms=50.0,
                difficulty="Beginner",
                featured=True,
                tags=["email", "gmail", "ai", "summarize"],
                use_case="Quick daily overview of incoming unread inbox messages.",
                estimated_steps=2,
                configurable_parameters=[
                    TemplateParameterModel(
                        key="email_query",
                        label="Email Search Query",
                        type="string",
                        default="is:unread",
                        required=True,
                        description="Filter query for Gmail message retrieval",
                    ),
                    TemplateParameterModel(
                        key="max_emails",
                        label="Max Emails to Fetch",
                        type="number",
                        default=5,
                        required=True,
                        description="Maximum number of emails to include in summary",
                    ),
                    TemplateParameterModel(
                        key="ai_prompt",
                        label="AI Summarization Instruction",
                        type="string",
                        default="Summarize the key points of these emails in clear bullet points.",
                        required=True,
                        description="Instruction guiding the AI summarizer",
                    ),
                ],
                workflow_spec={
                    "workflow_id": "wf_tpl_email_summarizer",
                    "title": "Email Summary Workflow",
                    "description": "Find recent emails, extract content, and summarize using AI.",
                    "trigger": {"type": "Manual", "description": "Instant manual trigger"},
                    "nodes": [
                        {
                            "id": "step_1",
                            "step_id": "step_1",
                            "label": "Search Gmail Messages",
                            "type": "custom",
                            "provider": "gmail",
                            "operation": "gmail.messages.list",
                            "parameters": {"q": "{{email_query}}", "max_results": "{{max_emails}}"},
                            "position": {"x": 250, "y": 100},
                            "data": {
                                "label": "Search Gmail Messages",
                                "provider": "gmail",
                                "operation_id": "gmail.messages.list",
                                "parameters": {"q": "{{email_query}}", "max_results": "{{max_emails}}"},
                                "step_id": "step_1",
                            },
                        },
                        {
                            "id": "step_2",
                            "step_id": "step_2",
                            "label": "AI Summarize Content",
                            "type": "custom",
                            "provider": "ai",
                            "operation": "ai.summarize",
                            "parameters": {"prompt": "{{ai_prompt}}", "input": "{{step_1.messages}}"},
                            "position": {"x": 250, "y": 260},
                            "data": {
                                "label": "AI Summarize Content",
                                "provider": "ai",
                                "operation_id": "ai.summarize",
                                "parameters": {"prompt": "{{ai_prompt}}", "input": "{{step_1.messages}}"},
                                "step_id": "step_2",
                            },
                        },
                    ],
                    "edges": [
                        {"id": "e_step_1-step_2", "source": "step_1", "target": "step_2"}
                    ],
                },
            ),
            TemplateMetadataModel(
                id="tpl_email_slack_summary",
                title="Email → Slack Summary",
                description="Find recent emails, summarize with AI, and dispatch the summary to a designated Slack channel.",
                category="Communication",
                icon="MessageSquare",
                connectors=["gmail", "ai", "slack"],
                required_providers=["gmail", "ai", "slack"],
                estimated_time_ms=65.0,
                difficulty="Intermediate",
                featured=True,
                tags=["email", "gmail", "slack", "ai", "notification"],
                use_case="Keep your team updated on important customer emails automatically on Slack.",
                estimated_steps=3,
                configurable_parameters=[
                    TemplateParameterModel(
                        key="email_query",
                        label="Email Search Query",
                        type="string",
                        default="is:unread",
                        required=True,
                        description="Gmail query filter",
                    ),
                    TemplateParameterModel(
                        key="slack_channel",
                        label="Slack Target Channel",
                        type="string",
                        default=None,
                        required=True,
                        description="Target Slack channel (e.g. #all-agentflow-ai)",
                    ),
                    TemplateParameterModel(
                        key="ai_prompt",
                        label="AI Summary Prompt",
                        type="string",
                        default="Summarize the email content concisely for team Slack alert.",
                        required=True,
                        description="Prompt instruction for AI summary",
                    ),
                ],
                workflow_spec={
                    "workflow_id": "wf_tpl_email_slack_summary",
                    "title": "Email to Slack Summary Workflow",
                    "description": "Summarize inbox emails and post summary to Slack.",
                    "trigger": {"type": "Manual", "description": "Instant manual trigger"},
                    "nodes": [
                        {
                            "id": "step_1",
                            "step_id": "step_1",
                            "label": "Search Gmail Messages",
                            "type": "custom",
                            "provider": "gmail",
                            "operation": "gmail.messages.list",
                            "parameters": {"q": "{{email_query}}"},
                            "position": {"x": 250, "y": 100},
                            "data": {
                                "label": "Search Gmail Messages",
                                "provider": "gmail",
                                "operation_id": "gmail.messages.list",
                                "parameters": {"q": "{{email_query}}"},
                                "step_id": "step_1",
                            },
                        },
                        {
                            "id": "step_2",
                            "step_id": "step_2",
                            "label": "AI Summarize Content",
                            "type": "custom",
                            "provider": "ai",
                            "operation": "ai.summarize",
                            "parameters": {"prompt": "{{ai_prompt}}", "input": "{{step_1.messages}}"},
                            "position": {"x": 250, "y": 260},
                            "data": {
                                "label": "AI Summarize Content",
                                "provider": "ai",
                                "operation_id": "ai.summarize",
                                "parameters": {"prompt": "{{ai_prompt}}", "input": "{{step_1.messages}}"},
                                "step_id": "step_2",
                            },
                        },
                        {
                            "id": "step_3",
                            "step_id": "step_3",
                            "label": "Send Summary to Slack",
                            "type": "custom",
                            "provider": "slack",
                            "operation": "slack.chat.postMessage",
                            "parameters": {"channel": "{{slack_channel}}", "text": "Email Summary Report:\n{{step_2.summary}}"},
                            "position": {"x": 250, "y": 420},
                            "data": {
                                "label": "Send Summary to Slack",
                                "provider": "slack",
                                "operation_id": "slack.chat.postMessage",
                                "parameters": {"channel": "{{slack_channel}}", "text": "Email Summary Report:\n{{step_2.summary}}"},
                                "step_id": "step_3",
                            },
                        },
                    ],
                    "edges": [
                        {"id": "e_step_1-step_2", "source": "step_1", "target": "step_2"},
                        {"id": "e_step_2-step_3", "source": "step_2", "target": "step_3"},
                    ],
                },
            ),
            TemplateMetadataModel(
                id="tpl_invoice_email_processing",
                title="Invoice Email Processing",
                description="Find invoice emails, extract billing and vendor details using AI, and post finance alerts to Slack.",
                category="Finance & Invoicing",
                icon="Receipt",
                connectors=["gmail", "ai", "slack"],
                required_providers=["gmail", "ai", "slack"],
                estimated_time_ms=75.0,
                difficulty="Intermediate",
                featured=True,
                tags=["invoice", "finance", "gmail", "ai", "slack"],
                use_case="Automate financial invoice extraction and team notifications.",
                estimated_steps=3,
                configurable_parameters=[
                    TemplateParameterModel(
                        key="email_query",
                        label="Invoice Search Criteria",
                        type="string",
                        default="label:invoices OR subject:invoice",
                        required=True,
                        description="Gmail search query for invoices",
                    ),
                    TemplateParameterModel(
                        key="slack_channel",
                        label="Finance Slack Channel",
                        type="string",
                        default=None,
                        required=True,
                        description="Target Slack channel to dispatch invoice alerts (e.g. #all-agentflow-ai)",
                    ),
                ],
                workflow_spec={
                    "workflow_id": "wf_tpl_invoice_processing",
                    "title": "Invoice Email Processing Workflow",
                    "description": "Extract invoice information and post to Slack.",
                    "trigger": {"type": "Manual", "description": "Instant manual trigger"},
                    "nodes": [
                        {
                            "id": "step_1",
                            "step_id": "step_1",
                            "label": "Find Invoice Emails",
                            "type": "custom",
                            "provider": "gmail",
                            "operation": "gmail.messages.list",
                            "parameters": {"q": "{{email_query}}"},
                            "position": {"x": 250, "y": 100},
                            "data": {
                                "label": "Find Invoice Emails",
                                "provider": "gmail",
                                "operation_id": "gmail.messages.list",
                                "parameters": {"q": "{{email_query}}"},
                                "step_id": "step_1",
                            },
                        },
                        {
                            "id": "step_2",
                            "step_id": "step_2",
                            "label": "AI Extract Invoice Data",
                            "type": "custom",
                            "provider": "ai",
                            "operation": "ai.extract",
                            "parameters": {
                                "prompt": "Extract invoice number, total amount, vendor name, and payment due date.",
                                "input": "{{step_1.messages}}",
                            },
                            "position": {"x": 250, "y": 260},
                            "data": {
                                "label": "AI Extract Invoice Data",
                                "provider": "ai",
                                "operation_id": "ai.extract",
                                "parameters": {
                                    "prompt": "Extract invoice number, total amount, vendor name, and payment due date.",
                                    "input": "{{step_1.messages}}",
                                },
                                "step_id": "step_2",
                            },
                        },
                        {
                            "id": "step_3",
                            "step_id": "step_3",
                            "label": "Post Invoice Alert to Slack",
                            "type": "custom",
                            "provider": "slack",
                            "operation": "slack.chat.postMessage",
                            "parameters": {
                                "channel": "{{slack_channel}}",
                                "text": "Invoice Processed:\n{{step_2.extracted_data}}",
                            },
                            "position": {"x": 250, "y": 420},
                            "data": {
                                "label": "Post Invoice Alert to Slack",
                                "provider": "slack",
                                "operation_id": "slack.chat.postMessage",
                                "parameters": {
                                    "channel": "{{slack_channel}}",
                                    "text": "Invoice Processed:\n{{step_2.extracted_data}}",
                                },
                                "step_id": "step_3",
                            },
                        },
                    ],
                    "edges": [
                        {"id": "e_step_1-step_2", "source": "step_1", "target": "step_2"},
                        {"id": "e_step_2-step_3", "source": "step_2", "target": "step_3"},
                    ],
                },
            ),
            TemplateMetadataModel(
                id="tpl_daily_email_digest",
                title="Daily Email Digest",
                description="Scheduled daily workflow that retrieves recent emails and generates an organized AI summary digest.",
                category="Scheduled Automation",
                icon="Calendar",
                connectors=["schedule", "gmail", "ai"],
                required_providers=["schedule", "gmail", "ai"],
                estimated_time_ms=55.0,
                difficulty="Intermediate",
                featured=True,
                tags=["schedule", "gmail", "ai", "digest", "daily"],
                use_case="Receive a daily scheduled briefing of your inbox priorities.",
                estimated_steps=3,
                configurable_parameters=[
                    TemplateParameterModel(
                        key="schedule_expression",
                        label="Schedule Recurrence",
                        type="string",
                        default="Every day at 9 AM",
                        required=True,
                        description="Recurrence pattern or schedule prompt",
                    ),
                    TemplateParameterModel(
                        key="email_query",
                        label="Digest Email Query",
                        type="string",
                        default="newer_than:1d",
                        required=True,
                        description="Gmail query filter for daily digest",
                    ),
                ],
                workflow_spec={
                    "workflow_id": "wf_tpl_daily_email_digest",
                    "title": "Daily Email Digest Workflow",
                    "description": "Daily scheduled digest of emails.",
                    "trigger": {"type": "Schedule", "description": "Scheduled daily trigger"},
                    "nodes": [
                        {
                            "id": "step_1",
                            "step_id": "step_1",
                            "label": "Schedule Trigger",
                            "type": "custom",
                            "provider": "schedule",
                            "operation": "schedule.trigger",
                            "parameters": {"expression": "{{schedule_expression}}"},
                            "position": {"x": 250, "y": 100},
                            "data": {
                                "label": "Schedule Trigger",
                                "provider": "schedule",
                                "operation_id": "schedule.trigger",
                                "parameters": {"expression": "{{schedule_expression}}"},
                                "step_id": "step_1",
                            },
                        },
                        {
                            "id": "step_2",
                            "step_id": "step_2",
                            "label": "Retrieve Daily Emails",
                            "type": "custom",
                            "provider": "gmail",
                            "operation": "gmail.messages.list",
                            "parameters": {"q": "{{email_query}}"},
                            "position": {"x": 250, "y": 260},
                            "data": {
                                "label": "Retrieve Daily Emails",
                                "provider": "gmail",
                                "operation_id": "gmail.messages.list",
                                "parameters": {"q": "{{email_query}}"},
                                "step_id": "step_2",
                            },
                        },
                        {
                            "id": "step_3",
                            "step_id": "step_3",
                            "label": "Generate Daily Digest",
                            "type": "custom",
                            "provider": "ai",
                            "operation": "ai.summarize",
                            "parameters": {
                                "prompt": "Create a comprehensive daily digest of these emails grouped by priority.",
                                "input": "{{step_2.messages}}",
                            },
                            "position": {"x": 250, "y": 420},
                            "data": {
                                "label": "Generate Daily Digest",
                                "provider": "ai",
                                "operation_id": "ai.summarize",
                                "parameters": {
                                    "prompt": "Create a comprehensive daily digest of these emails grouped by priority.",
                                    "input": "{{step_2.messages}}",
                                },
                                "step_id": "step_3",
                            },
                        },
                    ],
                    "edges": [
                        {"id": "e_step_1-step_2", "source": "step_1", "target": "step_2"},
                        {"id": "e_step_2-step_3", "source": "step_2", "target": "step_3"},
                    ],
                },
            ),
            TemplateMetadataModel(
                id="tpl_scheduled_slack_report",
                title="Scheduled Slack Report",
                description="Scheduled trigger gathers relevant workflow data, generates an executive AI summary, and posts to Slack.",
                category="Reports",
                icon="BarChart",
                connectors=["schedule", "gmail", "ai", "slack"],
                required_providers=["schedule", "gmail", "ai", "slack"],
                estimated_time_ms=70.0,
                difficulty="Advanced",
                featured=True,
                tags=["schedule", "slack", "report", "ai", "automation"],
                use_case="Automated executive team updates delivered directly to Slack on schedule.",
                estimated_steps=4,
                configurable_parameters=[
                    TemplateParameterModel(
                        key="schedule_expression",
                        label="Schedule Recurrence",
                        type="string",
                        default="Every day at 9 AM",
                        required=True,
                        description="Recurrence schedule",
                    ),
                    TemplateParameterModel(
                        key="slack_channel",
                        label="Target Slack Channel",
                        type="string",
                        default=None,
                        required=True,
                        description="Slack channel for report posting (e.g. #all-agentflow-ai)",
                    ),
                    TemplateParameterModel(
                        key="search_query",
                        label="Report Source Query",
                        type="string",
                        default="label:reports OR subject:update",
                        required=True,
                        description="Filter query to collect report input messages",
                    ),
                ],
                workflow_spec={
                    "workflow_id": "wf_tpl_scheduled_slack_report",
                    "title": "Scheduled Slack Report Workflow",
                    "description": "Generate and post scheduled AI summary reports to Slack.",
                    "trigger": {"type": "Schedule", "description": "Scheduled report trigger"},
                    "nodes": [
                        {
                            "id": "step_1",
                            "step_id": "step_1",
                            "label": "Scheduled Trigger",
                            "type": "custom",
                            "provider": "schedule",
                            "operation": "schedule.trigger",
                            "parameters": {"expression": "{{schedule_expression}}"},
                            "position": {"x": 250, "y": 100},
                            "data": {
                                "label": "Scheduled Trigger",
                                "provider": "schedule",
                                "operation_id": "schedule.trigger",
                                "parameters": {"expression": "{{schedule_expression}}"},
                                "step_id": "step_1",
                            },
                        },
                        {
                            "id": "step_2",
                            "step_id": "step_2",
                            "label": "Gather Email Data",
                            "type": "custom",
                            "provider": "gmail",
                            "operation": "gmail.messages.list",
                            "parameters": {"q": "{{search_query}}"},
                            "position": {"x": 250, "y": 260},
                            "data": {
                                "label": "Gather Email Data",
                                "provider": "gmail",
                                "operation_id": "gmail.messages.list",
                                "parameters": {"q": "{{search_query}}"},
                                "step_id": "step_2",
                            },
                        },
                        {
                            "id": "step_3",
                            "step_id": "step_3",
                            "label": "AI Generate Summary",
                            "type": "custom",
                            "provider": "ai",
                            "operation": "ai.summarize",
                            "parameters": {
                                "prompt": "Synthesize executive summary report from gathered data.",
                                "input": "{{step_2.messages}}",
                            },
                            "position": {"x": 250, "y": 420},
                            "data": {
                                "label": "AI Generate Summary",
                                "provider": "ai",
                                "operation_id": "ai.summarize",
                                "parameters": {
                                    "prompt": "Synthesize executive summary report from gathered data.",
                                    "input": "{{step_2.messages}}",
                                },
                                "step_id": "step_3",
                            },
                        },
                        {
                            "id": "step_4",
                            "step_id": "step_4",
                            "label": "Post Report to Slack",
                            "type": "custom",
                            "provider": "slack",
                            "operation": "slack.chat.postMessage",
                            "parameters": {
                                "channel": "{{slack_channel}}",
                                "text": "Daily Executive Report:\n{{step_3.summary}}",
                            },
                            "position": {"x": 250, "y": 580},
                            "data": {
                                "label": "Post Report to Slack",
                                "provider": "slack",
                                "operation_id": "slack.chat.postMessage",
                                "parameters": {
                                    "channel": "{{slack_channel}}",
                                    "text": "Daily Executive Report:\n{{step_3.summary}}",
                                },
                                "step_id": "step_4",
                            },
                        },
                    ],
                    "edges": [
                        {"id": "e_step_1-step_2", "source": "step_1", "target": "step_2"},
                        {"id": "e_step_2-step_3", "source": "step_2", "target": "step_3"},
                        {"id": "e_step_3-step_4", "source": "step_3", "target": "step_4"},
                    ],
                },
            ),
            TemplateMetadataModel(
                id="tpl_multistep_email_assistant",
                title="Multi-step Email Assistant",
                description="Search incoming customer support emails, retrieve details, and generate tailored AI response drafts.",
                category="Multi-Service",
                icon="Bot",
                connectors=["gmail", "ai"],
                required_providers=["gmail", "ai"],
                estimated_time_ms=60.0,
                difficulty="Intermediate",
                featured=False,
                tags=["gmail", "ai", "support", "assistant", "multi-step"],
                use_case="Automate support email triage and draft creation for customer service teams.",
                estimated_steps=3,
                configurable_parameters=[
                    TemplateParameterModel(
                        key="email_query",
                        label="Support Email Query",
                        type="string",
                        default="subject:support OR label:customer-service",
                        required=True,
                        description="Gmail query filter for customer support messages",
                    ),
                    TemplateParameterModel(
                        key="ai_instruction",
                        label="AI Response Instruction",
                        type="string",
                        default="Draft a helpful, polite customer support response addressing the user issue.",
                        required=True,
                        description="Instruction guiding AI draft generation",
                    ),
                ],
                workflow_spec={
                    "workflow_id": "wf_tpl_multistep_email_assistant",
                    "title": "Multi-step Email Assistant Workflow",
                    "description": "Retrieve support emails and generate AI responses.",
                    "trigger": {"type": "Manual", "description": "Instant manual trigger"},
                    "nodes": [
                        {
                            "id": "step_1",
                            "step_id": "step_1",
                            "label": "Search Support Emails",
                            "type": "custom",
                            "provider": "gmail",
                            "operation": "gmail.messages.list",
                            "parameters": {"q": "{{email_query}}"},
                            "position": {"x": 250, "y": 100},
                            "data": {
                                "label": "Search Support Emails",
                                "provider": "gmail",
                                "operation_id": "gmail.messages.list",
                                "parameters": {"q": "{{email_query}}"},
                                "step_id": "step_1",
                            },
                        },
                        {
                            "id": "step_2",
                            "step_id": "step_2",
                            "label": "Get Message Details",
                            "type": "custom",
                            "provider": "gmail",
                            "operation": "gmail.messages.get",
                            "parameters": {"message_id": "{{step_1.message_id}}"},
                            "position": {"x": 250, "y": 260},
                            "data": {
                                "label": "Get Message Details",
                                "provider": "gmail",
                                "operation_id": "gmail.messages.get",
                                "parameters": {"message_id": "{{step_1.message_id}}"},
                                "step_id": "step_2",
                            },
                        },
                        {
                            "id": "step_3",
                            "step_id": "step_3",
                            "label": "AI Draft Support Response",
                            "type": "custom",
                            "provider": "ai",
                            "operation": "ai.generate",
                            "parameters": {
                                "instruction": "{{ai_instruction}}",
                                "email_body": "{{step_2.body}}",
                            },
                            "position": {"x": 250, "y": 420},
                            "data": {
                                "label": "AI Draft Support Response",
                                "provider": "ai",
                                "operation_id": "ai.generate",
                                "parameters": {
                                    "instruction": "{{ai_instruction}}",
                                    "email_body": "{{step_2.body}}",
                                },
                                "step_id": "step_3",
                            },
                        },
                    ],
                    "edges": [
                        {"id": "e_step_1-step_2", "source": "step_1", "target": "step_2"},
                        {"id": "e_step_2-step_3", "source": "step_2", "target": "step_3"},
                    ],
                },
            ),
        ]
        for t in templates:
            self._templates[t.id] = t

    def get_templates(
        self, category: Optional[str] = None, search: Optional[str] = None, featured_only: bool = False
    ) -> List[TemplateMetadataModel]:
        results = list(self._templates.values())

        if category and category.lower() != "all":
            results = [t for t in results if t.category.lower() == category.lower()]

        if featured_only:
            results = [t for t in results if t.featured]

        if search:
            q = search.lower()
            results = [
                t
                for t in results
                if q in t.title.lower()
                or q in t.description.lower()
                or any(q in tag.lower() for tag in t.tags)
                or any(q in conn.lower() for conn in t.connectors)
            ]

        return results

    def get_template_by_id(self, template_id: str) -> Optional[TemplateMetadataModel]:
        return self._templates.get(template_id)

    def get_categories(self) -> List[str]:
        return [
            "All",
            "Email",
            "Communication",
            "Productivity",
            "Reports",
            "Scheduled Automation",
            "Multi-Service",
            "Finance & Invoicing",
        ]

    def _interpolate_value(self, val: Any, params: Dict[str, Any]) -> Any:
        """Recursively substitutes parameter placeholders in strings, dicts, and lists."""
        if isinstance(val, str):
            res_str = val
            for k, v in params.items():
                placeholder = f"{{{{{k}}}}}"
                if placeholder in res_str:
                    if res_str == placeholder:
                        return v
                    res_str = res_str.replace(placeholder, str(v))
            return res_str
        elif isinstance(val, dict):
            return {k: self._interpolate_value(v, params) for k, v in val.items()}
        elif isinstance(val, list):
            return [self._interpolate_value(item, params) for item in val]
        return val

    async def instantiate_template(
        self, template_id: str, user_parameters: Optional[Dict[str, Any]] = None, user_id: str = "usr_1"
    ) -> Dict[str, Any]:
        """
        Instantiates a canonical template into a validated AgentFlow workflow DAG
        and persists an immutable version snapshot.
        """
        tpl = self.get_template_by_id(template_id)
        if not tpl:
            raise KeyError(f"Template [{template_id}] not found.")

        # 1. Resolve and validate parameters
        effective_params: Dict[str, Any] = {}
        user_parameters = user_parameters or {}

        for p_def in tpl.configurable_parameters:
            val = user_parameters.get(p_def.key)
            if val is None or (isinstance(val, str) and not val.strip()):
                if p_def.required and p_def.default is None:
                    raise ValueError(f"Required parameter [{p_def.key}] is missing.")
                val = p_def.default

            # Type coercions
            if p_def.type == "number" and val is not None:
                try:
                    val = float(val) if "." in str(val) else int(val)
                except ValueError:
                    raise ValueError(f"Parameter [{p_def.key}] must be a valid number.")
            elif p_def.type == "boolean" and val is not None:
                val = str(val).lower() in ("true", "1", "yes")

            effective_params[p_def.key] = val

        # 2. Deep copy workflow spec and interpolate parameters
        raw_spec = copy.deepcopy(tpl.workflow_spec)
        workflow_id = f"wf_tpl_{uuid.uuid4().hex[:8]}"

        raw_nodes = raw_spec.get("nodes", [])
        raw_edges = raw_spec.get("edges", [])
        trigger = raw_spec.get("trigger", {"type": "Manual", "description": "Instant trigger"})

        interpolated_nodes = self._interpolate_value(raw_nodes, effective_params)

        wf_graph = {
            "workflow_id": workflow_id,
            "title": tpl.title,
            "name": tpl.title,
            "description": tpl.description,
            "trigger": trigger,
            "nodes": interpolated_nodes,
            "edges": raw_edges,
            "metadata": {
                "template_id": tpl.id,
                "template_name": tpl.title,
                "template_category": tpl.category,
                "parameters_applied": effective_params,
            },
        }

        # 3. Validate workflow DAG using existing WorkflowValidator
        validation_res = self._validator.validate_workflow(wf_graph)
        if not validation_res.is_valid:
            logger.error(f"Template [{template_id}] DAG validation failed: {validation_res.errors}")
            raise ValueError(f"Generated workflow DAG is invalid: {', '.join(validation_res.errors)}")

        # 4. Create immutable version snapshot via WorkflowVersionManager
        snapshot = await workflow_version_manager.create_version_snapshot(
            workflow_id=workflow_id,
            workflow_spec=wf_graph,
            name=tpl.title,
            description=tpl.description,
            commit_message=f"Instantiated from template [{tpl.title}]",
            author=user_id,
        )

        logger.info(
            f"Successfully instantiated template [{template_id}] as workflow [{workflow_id}] v{snapshot.version_number}."
        )

        return {
            "workflow_id": workflow_id,
            "name": tpl.title,
            "description": tpl.description,
            "workflow_json": wf_graph,
            "nodes": interpolated_nodes,
            "edges": raw_edges,
            "version_id": snapshot.version_id,
            "version_number": snapshot.version_number,
            "template_metadata": {
                "template_id": tpl.id,
                "template_name": tpl.title,
                "category": tpl.category,
            },
        }

    # Backward compatibility helper for clone_template
    def clone_template(self, template_id: str, user_id: str = "usr_1") -> Dict[str, Any]:
        tpl = self.get_template_by_id(template_id)
        if not tpl:
            raise KeyError(f"Template [{template_id}] not found.")

        cloned_spec = copy.deepcopy(tpl.workflow_spec)
        cloned_spec["workflow_id"] = f"wf_cloned_{uuid.uuid4().hex[:8]}"
        cloned_spec["tenant_id"] = user_id
        return cloned_spec


template_engine = TemplateEngine()

