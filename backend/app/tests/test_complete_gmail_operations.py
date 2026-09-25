import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.connectors.providers.gmail.adapter import GmailAdapter
from app.connectors.models import ConnectorRequestModel, ConnectorCredentialModel
from app.agents.planner.planner_v4 import intelligent_planner_v4


@pytest.fixture
def gmail_adapter():
    return GmailAdapter()


@pytest.fixture
def dummy_credential():
    return ConnectorCredentialModel(
        provider="Gmail",
        account_label="aswinkumaar07@gmail.com",
        access_token="ya29.mock_token_complete_ops",
        refresh_token="mock_refresh_token",
        expires_at=9999999999,
        status="active",
        metadata={"email": "aswinkumaar07@gmail.com"},
    )


def test_gmail_adapter_metadata_all_operations(gmail_adapter):
    metadata = gmail_adapter.get_metadata()
    assert metadata.provider == "Gmail"
    assert len(metadata.supported_operations) == 14
    expected_ops = [
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
    ]
    for op in expected_ops:
        assert op in metadata.supported_operations
        assert op in metadata.operation_schemas


@pytest.mark.asyncio
async def test_op_send(gmail_adapter, dummy_credential):
    req = ConnectorRequestModel(
        operation_id="gmail.messages.send",
        parameters={"to": "john@example.com", "subject": "Test Subject", "body": "Test Body"},
        tenant_id="usr_1",
    )
    with patch("httpx.AsyncClient.get") as mock_get, patch("httpx.AsyncClient.post") as mock_post:
        mock_get.return_value = MagicMock(status_code=200, is_success=True, json=lambda: {"emailAddress": "aswinkumaar07@gmail.com"})
        mock_post.return_value = MagicMock(status_code=200, is_success=True, json=lambda: {"id": "msg_123", "threadId": "th_123"})

        res = await gmail_adapter.execute_operation(req, credentials=dummy_credential)
        assert res.success is True
        assert res.data["messageId"] == "msg_123"


@pytest.mark.asyncio
async def test_op_list(gmail_adapter, dummy_credential):
    req = ConnectorRequestModel(
        operation_id="gmail.messages.list",
        parameters={"q": "is:unread", "max_results": 5},
        tenant_id="usr_1",
    )
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = [
            MagicMock(status_code=200, is_success=True, json=lambda: {"emailAddress": "aswinkumaar07@gmail.com"}),
            MagicMock(status_code=200, is_success=True, headers={}, json=lambda: {"messages": [{"id": "msg_1"}, {"id": "msg_2"}]}),
        ]
        res = await gmail_adapter.execute_operation(req, credentials=dummy_credential)
        assert res.success is True
        assert len(res.data["messages"]) == 2


@pytest.mark.asyncio
async def test_op_get(gmail_adapter, dummy_credential):
    req = ConnectorRequestModel(
        operation_id="gmail.messages.get",
        parameters={"message_id": "msg_123"},
        tenant_id="usr_1",
    )
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = [
            MagicMock(status_code=200, is_success=True, json=lambda: {"emailAddress": "aswinkumaar07@gmail.com"}),
            MagicMock(status_code=200, is_success=True, headers={}, json=lambda: {"id": "msg_123", "snippet": "Hello World"}),
        ]
        res = await gmail_adapter.execute_operation(req, credentials=dummy_credential)
        assert res.success is True
        assert res.data["messageId"] == "msg_123"
        assert res.data["snippet"] == "Hello World"


@pytest.mark.asyncio
async def test_op_search(gmail_adapter, dummy_credential):
    req = ConnectorRequestModel(
        operation_id="gmail.messages.search",
        parameters={"query": "from:boss@company.com"},
        tenant_id="usr_1",
    )
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = [
            MagicMock(status_code=200, is_success=True, json=lambda: {"emailAddress": "aswinkumaar07@gmail.com"}),
            MagicMock(status_code=200, is_success=True, json=lambda: {"messages": [{"id": "msg_s1"}]}),
        ]
        res = await gmail_adapter.execute_operation(req, credentials=dummy_credential)
        assert res.success is True
        assert len(res.data["messages"]) == 1


@pytest.mark.asyncio
async def test_op_reply(gmail_adapter, dummy_credential):
    req = ConnectorRequestModel(
        operation_id="gmail.messages.reply",
        parameters={"message_id": "msg_123", "to": "sender@example.com", "body": "Understood."},
        tenant_id="usr_1",
    )
    with patch("httpx.AsyncClient.get") as mock_get, patch("httpx.AsyncClient.post") as mock_post:
        mock_get.return_value = MagicMock(status_code=200, is_success=True, json=lambda: {"emailAddress": "aswinkumaar07@gmail.com"})
        mock_post.return_value = MagicMock(status_code=200, is_success=True, json=lambda: {"id": "msg_reply_1", "threadId": "msg_123"})

        res = await gmail_adapter.execute_operation(req, credentials=dummy_credential)
        assert res.success is True
        assert res.data["messageId"] == "msg_reply_1"


@pytest.mark.asyncio
async def test_op_forward(gmail_adapter, dummy_credential):
    req = ConnectorRequestModel(
        operation_id="gmail.messages.forward",
        parameters={"to": "colleague@example.com", "subject": "Important Report", "body": "FYI"},
        tenant_id="usr_1",
    )
    with patch("httpx.AsyncClient.get") as mock_get, patch("httpx.AsyncClient.post") as mock_post:
        mock_get.return_value = MagicMock(status_code=200, is_success=True, json=lambda: {"emailAddress": "aswinkumaar07@gmail.com"})
        mock_post.return_value = MagicMock(status_code=200, is_success=True, json=lambda: {"id": "msg_fwd_1"})

        res = await gmail_adapter.execute_operation(req, credentials=dummy_credential)
        assert res.success is True
        assert res.data["messageId"] == "msg_fwd_1"


@pytest.mark.asyncio
async def test_op_delete(gmail_adapter, dummy_credential):
    req = ConnectorRequestModel(
        operation_id="gmail.messages.delete",
        parameters={"message_id": "msg_del_1"},
        tenant_id="usr_1",
    )
    with patch("httpx.AsyncClient.get") as mock_get, patch("httpx.AsyncClient.post") as mock_post:
        mock_get.return_value = MagicMock(status_code=200, is_success=True, json=lambda: {"emailAddress": "aswinkumaar07@gmail.com"})
        mock_post.return_value = MagicMock(status_code=200, is_success=True, json=lambda: {"id": "msg_del_1"})

        res = await gmail_adapter.execute_operation(req, credentials=dummy_credential)
        assert res.success is True
        assert res.data["status"] == "TRASHED"


@pytest.mark.asyncio
async def test_op_mark_read_and_unread(gmail_adapter, dummy_credential):
    req_read = ConnectorRequestModel(
        operation_id="gmail.messages.mark_read",
        parameters={"message_id": "msg_mrk_1"},
        tenant_id="usr_1",
    )
    req_unread = ConnectorRequestModel(
        operation_id="gmail.messages.mark_unread",
        parameters={"message_id": "msg_mrk_1"},
        tenant_id="usr_1",
    )
    with patch("httpx.AsyncClient.get") as mock_get, patch("httpx.AsyncClient.post") as mock_post:
        mock_get.return_value = MagicMock(status_code=200, is_success=True, json=lambda: {"emailAddress": "aswinkumaar07@gmail.com"})
        mock_post.return_value = MagicMock(status_code=200, is_success=True, json=lambda: {"id": "msg_mrk_1"})

        res_read = await gmail_adapter.execute_operation(req_read, credentials=dummy_credential)
        assert res_read.success is True
        assert res_read.data["status"] == "READ"

        res_unread = await gmail_adapter.execute_operation(req_unread, credentials=dummy_credential)
        assert res_unread.success is True
        assert res_unread.data["status"] == "UNREAD"


@pytest.mark.asyncio
async def test_op_labels_list_and_modify(gmail_adapter, dummy_credential):
    req_list = ConnectorRequestModel(operation_id="gmail.labels.list", tenant_id="usr_1")
    req_mod = ConnectorRequestModel(
        operation_id="gmail.labels.modify",
        parameters={"message_id": "msg_lbl_1", "add_labels": ["STARRED"]},
        tenant_id="usr_1",
    )
    with patch("httpx.AsyncClient.get") as mock_get, patch("httpx.AsyncClient.post") as mock_post:
        mock_get.side_effect = [
            MagicMock(status_code=200, is_success=True, json=lambda: {"emailAddress": "aswinkumaar07@gmail.com"}),
            MagicMock(status_code=200, is_success=True, json=lambda: {"labels": [{"id": "INBOX"}, {"id": "STARRED"}]}),
            MagicMock(status_code=200, is_success=True, json=lambda: {"emailAddress": "aswinkumaar07@gmail.com"}),
        ]
        mock_post.return_value = MagicMock(status_code=200, is_success=True, json=lambda: {"labelIds": ["STARRED"]})

        res_l = await gmail_adapter.execute_operation(req_list, credentials=dummy_credential)
        assert res_l.success is True
        assert len(res_l.data["labels"]) == 2

        res_m = await gmail_adapter.execute_operation(req_mod, credentials=dummy_credential)
        assert res_m.success is True
        assert "STARRED" in res_m.data["labelIds"]


@pytest.mark.asyncio
async def test_op_drafts_create_and_send(gmail_adapter, dummy_credential):
    req_create = ConnectorRequestModel(
        operation_id="gmail.drafts.create",
        parameters={"to": "draft@example.com", "subject": "Draft Subject", "body": "Draft Content"},
        tenant_id="usr_1",
    )
    req_send = ConnectorRequestModel(
        operation_id="gmail.drafts.send",
        parameters={"draft_id": "draft_999"},
        tenant_id="usr_1",
    )
    with patch("httpx.AsyncClient.get") as mock_get, patch("httpx.AsyncClient.post") as mock_post:
        mock_get.return_value = MagicMock(status_code=200, is_success=True, json=lambda: {"emailAddress": "aswinkumaar07@gmail.com"})
        mock_post.side_effect = [
            MagicMock(status_code=200, is_success=True, json=lambda: {"id": "draft_999"}),
            MagicMock(status_code=200, is_success=True, json=lambda: {"id": "msg_sent_draft"}),
        ]

        res_c = await gmail_adapter.execute_operation(req_create, credentials=dummy_credential)
        assert res_c.success is True
        assert res_c.data["draftId"] == "draft_999"

        res_s = await gmail_adapter.execute_operation(req_send, credentials=dummy_credential)
        assert res_s.success is True
        assert res_s.data["messageId"] == "msg_sent_draft"


@pytest.mark.asyncio
async def test_op_attachment_download(gmail_adapter, dummy_credential):
    req = ConnectorRequestModel(
        operation_id="gmail.attachments.download",
        parameters={"message_id": "msg_att_1", "attachment_id": "att_777"},
        tenant_id="usr_1",
    )
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = [
            MagicMock(status_code=200, is_success=True, json=lambda: {"emailAddress": "aswinkumaar07@gmail.com"}),
            MagicMock(status_code=200, is_success=True, json=lambda: {"size": 1024, "data": "base64_encoded_bytes"}),
        ]
        res = await gmail_adapter.execute_operation(req, credentials=dummy_credential)
        assert res.success is True
        assert res.data["attachmentId"] == "att_777"
        assert res.data["size"] == 1024


def test_planner_intent_mapping_all_operations():
    prompts_expected = [
        ("Send email to test@domain.com Subject: Hello Body: Hi", "gmail.messages.send"),
        ("List messages in my inbox", "gmail.messages.list"),
        ("Get message details for msg_123", "gmail.messages.get"),
        ("Search email from:invoice@corp.com", "gmail.messages.search"),
        ("Send reply to msg_123 Body: Thank you", "gmail.messages.reply"),
        ("Forward message to friend@domain.com", "gmail.messages.forward"),
        ("Delete email msg_123", "gmail.messages.delete"),
        ("Mark as read msg_123", "gmail.messages.mark_read"),
        ("Mark as unread msg_123", "gmail.messages.mark_unread"),
        ("List labels in gmail", "gmail.labels.list"),
        ("Modify label for msg_123", "gmail.labels.modify"),
        ("Create draft for client@domain.com", "gmail.drafts.create"),
        ("Send draft draft_123", "gmail.drafts.send"),
        ("Download attachment att_123", "gmail.attachments.download"),
    ]

    for prompt, expected_op in prompts_expected:
        plan = intelligent_planner_v4.plan(prompt)
        nodes = [n for n in plan.workflow_graph["nodes"] if n.get("provider") in ["gmail", "google_gmail"]]
        assert len(nodes) > 0, f"No Gmail node created for prompt: {prompt}"
        actual_op = nodes[0].get("operation_id") or nodes[0].get("operation")
        assert actual_op == expected_op, f"Prompt '{prompt}' mapped to '{actual_op}' instead of '{expected_op}'"
