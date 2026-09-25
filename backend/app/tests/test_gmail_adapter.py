import base64
import pytest
from app.connectors.providers.gmail.adapter import GmailAdapter
from app.connectors.models import ConnectorRequestModel, ConnectorCredentialModel


@pytest.mark.asyncio
async def test_gmail_adapter_metadata():
    adapter = GmailAdapter()
    meta = adapter.get_metadata()
    assert meta.provider == "Gmail"
    assert "gmail.messages.send" in meta.supported_operations
    assert "gmail.messages.list" in meta.supported_operations
    assert "gmail.messages.get" in meta.supported_operations


def test_gmail_adapter_mime_building():
    adapter = GmailAdapter()
    encoded = adapter._build_mime_message(
        to_addr="test@example.com",
        subject="Test Subject",
        body="Hello World",
        cc="cc@example.com",
    )
    assert isinstance(encoded, str)
    decoded_bytes = base64.urlsafe_b64decode(encoded)
    decoded_text = decoded_bytes.decode("utf-8")
    assert "To: test@example.com" in decoded_text
    assert "Subject: Test Subject" in decoded_text
    assert "Cc: cc@example.com" in decoded_text
    assert "Hello World" in decoded_text


@pytest.mark.asyncio
async def test_gmail_adapter_execute_send_api_failure_handling():
    adapter = GmailAdapter()
    request = ConnectorRequestModel(
        provider="Gmail",
        operation_id="gmail.messages.send",
        tenant_id="usr_test",
        parameters={
            "to": "invalid@recipient.com",
            "subject": "Test Mail",
            "body": "Test content",
        },
    )
    # Invalid token to force real Google API error or network response
    creds = ConnectorCredentialModel(
        tenant_id="usr_test",
        provider="Gmail",
        auth_type="OAuth2",
        access_token="invalid_oauth_token_123",
    )

    response = await adapter.execute_operation(request, credentials=creds)

    # Must return success=False on HTTP 401 Unauthorized from Google API
    assert response.success is False
    assert response.status_code in [401, 403, 400]
    assert response.error_message is not None
    assert "Google Gmail API returned error" in response.error_message or "exception" in response.error_message
    assert "HTTP_status" in response.data
