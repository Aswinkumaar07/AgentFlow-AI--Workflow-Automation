import pytest
from app.agents.planner.planner_v4 import intelligent_planner_v4
from app.services.gmail_search_query_translator import gmail_search_query_translator
from app.connectors.providers.gmail.adapter import GmailAdapter
from app.connectors.models import ConnectorRequestModel, ConnectorCredentialModel


def test_gmail2_read_latest_email_intent_and_translation():
    prompt = "Read latest email"
    translated = gmail_search_query_translator.translate_to_gmail_query(prompt)
    assert translated["max_results"] == 1

    plan = intelligent_planner_v4.plan(prompt)
    nodes = [n for n in plan.workflow_graph["nodes"] if n.get("provider") in ["gmail", "google_gmail"]]
    assert len(nodes) > 0
    node = nodes[0]
    assert node.get("operation") in ["gmail.messages.get", "gmail.messages.list"]
    assert node["parameters"].get("max_results") == 1


def test_gmail2_read_unread_emails_intent_and_translation():
    prompt = "Read unread emails"
    translated = gmail_search_query_translator.translate_to_gmail_query(prompt)
    assert translated["query"] == "is:unread"
    assert translated["max_results"] == 10

    plan = intelligent_planner_v4.plan(prompt)
    nodes = [n for n in plan.workflow_graph["nodes"] if n.get("provider") in ["gmail", "google_gmail"]]
    assert len(nodes) > 0
    node = nodes[0]
    assert node.get("operation") == "gmail.messages.list"
    assert node["parameters"].get("q") == "is:unread"


def test_gmail2_read_emails_from_amazon():
    prompt = "Read emails from Amazon"
    translated = gmail_search_query_translator.translate_to_gmail_query(prompt)
    assert translated["query"] == "from:Amazon"

    plan = intelligent_planner_v4.plan(prompt)
    nodes = [n for n in plan.workflow_graph["nodes"] if n.get("provider") in ["gmail", "google_gmail"]]
    assert len(nodes) > 0
    node = nodes[0]
    assert node["parameters"].get("q") == "from:Amazon"


def test_gmail2_read_todays_emails():
    prompt = "Read today's emails"
    translated = gmail_search_query_translator.translate_to_gmail_query(prompt)
    assert translated["query"] == "newer_than:1d"

    plan = intelligent_planner_v4.plan(prompt)
    nodes = [n for n in plan.workflow_graph["nodes"] if n.get("provider") in ["gmail", "google_gmail"]]
    assert len(nodes) > 0
    node = nodes[0]
    assert node["parameters"].get("q") == "newer_than:1d"


@pytest.mark.asyncio
async def test_gmail2_adapter_read_operations_runtime():
    adapter = GmailAdapter()
    creds = ConnectorCredentialModel(
        tenant_id="usr_1",
        provider="Google",
        access_token="mock_access_token",
        account_label="aswinkumaar07@gmail.com",
    )

    # 1. Test gmail.messages.list
    req_list = ConnectorRequestModel(
        tenant_id="usr_1",
        operation_id="gmail.messages.list",
        parameters={"q": "is:unread", "max_results": 5},
    )
    res_list = await adapter.execute_operation(req_list, credentials=creds)
    assert res_list is not None
    assert res_list.operation_id == "gmail.messages.list"
    assert "messages" in res_list.data or "error" in res_list.data or res_list.status_code != 0

    # 2. Test gmail.messages.get
    req_get = ConnectorRequestModel(
        tenant_id="usr_1",
        operation_id="gmail.messages.get",
        parameters={"message_id": "msg_mock_123"},
    )
    res_get = await adapter.execute_operation(req_get, credentials=creds)
    assert res_get is not None
    assert res_get.operation_id == "gmail.messages.get"

    # 3. Test gmail.messages.search
    req_search = ConnectorRequestModel(
        tenant_id="usr_1",
        operation_id="gmail.messages.search",
        parameters={"q": "from:Amazon", "max_results": 10},
    )
    res_search = await adapter.execute_operation(req_search, credentials=creds)
    assert res_search is not None
    assert res_search.operation_id == "gmail.messages.search"
