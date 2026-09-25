import pytest
from typing import Optional, Dict, List
from app.connectors.registry import connector_registry
from app.connectors.models import ConnectorMetadataModel, OperationSchemaModel, ParameterSchemaModel
from app.connectors.interfaces import BaseProviderAdapter
from app.connectors.models import ConnectorRequestModel, ConnectorResponseModel
from app.agents.planner.planner_v4 import intelligent_planner_v4


class MockHubSpotAdapter(BaseProviderAdapter):
    @property
    def provider_name(self) -> str:
        return "HubSpot"

    def get_metadata(self) -> ConnectorMetadataModel:
        return HUBSPOT_METADATA

    async def execute_operation(self, request: ConnectorRequestModel, credentials: Optional[dict] = None) -> ConnectorResponseModel:
        return ConnectorResponseModel(status_code=200, success=True, data={"id": "hubspot_deal_1001", "status": "created"})


HUBSPOT_METADATA = ConnectorMetadataModel(
    provider="HubSpot",
    display_name="HubSpot CRM",
    icon="hubspot",
    auth_type="OAuth2",
    supported_operations=["hubspot.deals.create", "hubspot.contacts.search"],
    categories=["CRM", "Sales"],
    version="1.0.0",
    documentation_url="https://developers.hubspot.com",
    operation_schemas={
        "hubspot.deals.create": OperationSchemaModel(
            id="hubspot.deals.create",
            display_name="Create Sales Deal",
            description="Creates a new sales deal in HubSpot pipeline",
            required_parameters=[
                ParameterSchemaModel(name="deal_name", display_name="Deal Name", type="string", required=True, description="Name of deal"),
            ],
            optional_parameters=[],
            default_values={"deal_name": "New Enterprise Opportunity"},
        ),
        "hubspot.contacts.search": OperationSchemaModel(
            id="hubspot.contacts.search",
            display_name="Search Contacts",
            description="Searches CRM contacts by query",
            required_parameters=[],
            optional_parameters=[
                ParameterSchemaModel(name="query", display_name="Search Query", type="string", required=False, description="Search term"),
            ],
            default_values={"query": "active"},
        ),
    },
)


def test_dynamic_operation_discovery():
    gmail_ops = connector_registry.discover_operations("Gmail")
    assert len(gmail_ops) >= 3
    op_ids = [op.id for op in gmail_ops]
    assert "gmail.messages.send" in op_ids
    assert "gmail.messages.list" in op_ids

    drive_ops = connector_registry.discover_operations("Google Drive")
    assert len(drive_ops) >= 1
    assert drive_ops[0].id == "drive.files.create"


def test_provider_agnostic_operation_matching():
    # Prompt intent matching via metadata descriptions and token scores
    op_list = connector_registry.match_operation_dynamically("Gmail", "Fetch unread messages")
    assert op_list == "gmail.messages.list"

    op_search = connector_registry.match_operation_dynamically("Gmail", "Find invoice emails")
    assert op_search == "gmail.messages.search"

    op_forward = connector_registry.match_operation_dynamically("Gmail", "Forward invoice email")
    assert op_forward == "gmail.messages.forward"


def test_pluggable_new_provider_addition_without_planner_changes():
    # Register a new provider (HubSpot) dynamically
    adapter = MockHubSpotAdapter()
    connector_registry.register(adapter)
    connector_registry._metadata_map["hubspot"] = HUBSPOT_METADATA

    assert connector_registry.has("HubSpot")
    ops = connector_registry.discover_operations("HubSpot")
    assert len(ops) == 2

    matched_op = connector_registry.match_operation_dynamically("HubSpot", "Create sales deal")
    assert matched_op == "hubspot.deals.create"

    # Plan a workflow using the new provider without touching planner code
    plan = intelligent_planner_v4.plan("Create sales deal in HubSpot")
    assert plan is not None
    graph = plan.workflow_graph
    assert len(graph["nodes"]) >= 1
    assert graph["nodes"][0]["operation"] == "hubspot.deals.create"
    assert graph["nodes"][0]["provider"] in ["hubspot", "hubspot_crm"]
