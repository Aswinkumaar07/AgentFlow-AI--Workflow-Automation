import re
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("agentflow.agents.variables")


class VariableItem(BaseModel):
    name: str
    expression: str
    category: str
    description: str
    sample_value: Optional[str] = None


class VariableDiscoveryResult(BaseModel):
    node_outputs: List[VariableItem] = Field(default_factory=list)
    loop_variables: List[VariableItem] = Field(default_factory=list)
    system_variables: List[VariableItem] = Field(default_factory=list)
    trigger_variables: List[VariableItem] = Field(default_factory=list)


class VariableResolver:
    """
    Intelligent Variable Discovery & Expression Resolver Engine
    Discovers node output schemas, loop item properties, trigger payloads, and system runtime tokens dynamically.
    """

    SYSTEM_VARIABLES: List[VariableItem] = [
        VariableItem(
            name="Current Date",
            expression="{{$today}}",
            category="System",
            description="ISO Formatted Current Date (YYYY-MM-DD)",
            sample_value="2026-08-04",
        ),
        VariableItem(
            name="Current Timestamp",
            expression="{{$now}}",
            category="System",
            description="Full UTC ISO Timestamp",
            sample_value="2026-08-04T14:24:00Z",
        ),
        VariableItem(
            name="UUID Generator",
            expression="{{$uuid}}",
            category="System",
            description="Generates a unique v4 UUID string",
            sample_value="a75e26ad-42a5-4f57-9355-23093b2d5175",
        ),
        VariableItem(
            name="Execution ID",
            expression="{{$execution.id}}",
            category="System",
            description="Active workflow runtime execution ID",
            sample_value="exec_99812736",
        ),
        VariableItem(
            name="Workflow ID",
            expression="{{$workflow.id}}",
            category="System",
            description="Current workflow identifier",
            sample_value="wf_00192837",
        ),
    ]

    LOOP_VARIABLES: List[VariableItem] = [
        VariableItem(
            name="Loop Item",
            expression="{{$loop.item}}",
            category="Loop",
            description="Current item object in iteration",
            sample_value='{"name": "Alice", "email": "alice@example.com"}',
        ),
        VariableItem(
            name="Loop Item Email",
            expression="{{$loop.item.email}}",
            category="Loop",
            description="Extracted email field from current loop item",
            sample_value="alice@example.com",
        ),
        VariableItem(
            name="Loop Item Name",
            expression="{{$loop.item.name}}",
            category="Loop",
            description="Extracted name field from current loop item",
            sample_value="Alice Smith",
        ),
        VariableItem(
            name="Loop Index",
            expression="{{$loop.index}}",
            category="Loop",
            description="Zero-based current loop index",
            sample_value="0",
        ),
        VariableItem(
            name="Loop Total Count",
            expression="{{$loop.total}}",
            category="Loop",
            description="Total item count in iteration collection",
            sample_value="10",
        ),
    ]

    PROVIDER_OUTPUT_SCHEMAS: Dict[str, List[Dict[str, str]]] = {
        "Gmail": [
            {"field": "subject", "desc": "Email Subject Line", "sample": "Quarterly Invoice"},
            {"field": "body", "desc": "Email Body Text Content", "sample": "Please find attached document."},
            {"field": "sender", "desc": "Sender Email Address", "sample": "billing@company.com"},
            {"field": "attachments", "desc": "List of attached file objects", "sample": "[{...}]"},
        ],
        "Google Sheets": [
            {"field": "values", "desc": "Matrix of spreadsheet row values", "sample": "[['Name', 'Email']]"},
            {"field": "total_rows", "desc": "Total row count", "sample": "42"},
        ],
        "Slack": [
            {"field": "ts", "desc": "Slack message timestamp token", "sample": "1698273615.000100"},
            {"field": "channel", "desc": "Slack target channel ID", "sample": "C012345678"},
        ],
        "Google Drive": [
            {"field": "file_id", "desc": "Uploaded Drive File ID", "sample": "1B2c3D4e5F6g7H8i9J0k"},
            {"field": "web_link", "desc": "Sharable web view link", "sample": "https://drive.google.com/file/d/1B2c.../view"},
        ],
        "GitHub": [
            {"field": "title", "desc": "Pull Request or Issue Title", "sample": "Fix authentication bug"},
            {"field": "number", "desc": "PR or Issue Number", "sample": "142"},
            {"field": "state", "desc": "PR State (open/closed)", "sample": "open"},
        ],
        "AI": [
            {"field": "summary", "desc": "AI Generated Text Summary", "sample": "Summary of document..."},
            {"field": "sentiment", "desc": "Analyzed text sentiment", "sample": "positive"},
        ],
    }

    def discover_variables(self, workflow_graph: Dict[str, Any]) -> VariableDiscoveryResult:
        """Discovers all available variable tokens for a workflow graph dynamically."""
        nodes = workflow_graph.get("nodes", [])
        trigger = workflow_graph.get("trigger", {})

        node_outputs: List[VariableItem] = []
        trigger_variables: List[VariableItem] = []

        # Trigger Variables Discovery
        t_type = trigger.get("type", "Manual")
        if t_type == "Webhook":
            trigger_variables.append(
                VariableItem(
                    name="Webhook Payload Body",
                    expression="{{trigger_payload.body}}",
                    category="Trigger",
                    description="Raw text or JSON payload body received from HTTP Webhook",
                    sample_value='{"event": "user.signup", "user_id": 42}',
                )
            )
        elif t_type == "GitHub":
            trigger_variables.append(
                VariableItem(
                    name="GitHub Event PR Title",
                    expression="{{trigger.pull_request.title}}",
                    category="Trigger",
                    description="Title of triggering GitHub Pull Request",
                    sample_value="Update dependencies",
                )
            )

        # Node Outputs Discovery
        for node in nodes:
            nid = node.get("id", "step_1")
            provider = node.get("provider", "Generic")
            schema_fields = self.PROVIDER_OUTPUT_SCHEMAS.get(provider, [
                {"field": "output", "desc": "Generic node output payload", "sample": "result"}
            ])

            for field_info in schema_fields:
                field_name = field_info["field"]
                expr1 = f"{{{{$node.{provider}.{field_name}}}}}"
                expr2 = f"{{{{{nid}.{field_name}}}}}"

                node_outputs.append(
                    VariableItem(
                        name=f"{provider} {field_name.capitalize()} ({nid})",
                        expression=expr1,
                        category=f"Node ({provider})",
                        description=f"{field_info['desc']} from step '{nid}'",
                        sample_value=field_info["sample"],
                    )
                )

        return VariableDiscoveryResult(
            node_outputs=node_outputs,
            loop_variables=self.LOOP_VARIABLES,
            system_variables=self.SYSTEM_VARIABLES,
            trigger_variables=trigger_variables,
        )


variable_resolver = VariableResolver()
