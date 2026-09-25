import pytest
import time
from app.connectors import (
    AdaptiveRateLimiter,
    ConnectorCredentialModel,
    ConnectorFactory,
    ConnectorManager,
    ConnectorRegistry,
    DistributedSagaOrchestrator,
    GraphQLClient,
    OAuth2Engine,
    WebhookPlatform,
    connector_builder,
    connector_manager,
    connector_registry,
    graphql_client,
    oauth2_engine,
    plugin_loader,
    webhook_platform,
)
from app.connectors.security.secret_manager import secret_manager


@pytest.mark.asyncio
async def test_oauth2_engine_pkce():
    pkce = oauth2_engine.generate_pkce_pair()
    assert "code_verifier" in pkce
    assert "code_challenge" in pkce
    assert pkce["code_challenge_method"] == "S256"


@pytest.mark.asyncio
async def test_saga_orchestrator_rollback():
    saga = DistributedSagaOrchestrator()
    step1 = saga.add_step("Gmail", "gmail.messages.list", None)
    step1.response = type("Res", (), {"success": True})()

    step2 = saga.add_step("Drive", "drive.files.create", None)
    success = await saga.execute_rollback(step2, "Upload failure")

    assert success is True
    assert step1.compensated is True


@pytest.mark.asyncio
async def test_webhook_verification():
    secret = "my_webhook_secret_key"
    body = '{"event": "invoice.paid"}'
    # Compute signature
    import hmac, hashlib
    signature = hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()

    is_valid = webhook_platform.verify_hmac_signature(body, signature, secret)
    assert is_valid is True

    is_replay_ok = webhook_platform.check_replay_and_deduplicate("nonce_123", time.time())
    assert is_replay_ok is True

    # Repeat nonce should be rejected
    is_duplicate_ok = webhook_platform.check_replay_and_deduplicate("nonce_123", time.time())
    assert is_duplicate_ok is False


@pytest.mark.asyncio
async def test_connector_builder_and_marketplace():
    openapi_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Dynamic CRM", "version": "v1"},
        "paths": {"/v1/leads": {"post": {"operationId": "leads.create"}}},
    }
    adapter = connector_builder.build_from_openapi(openapi_spec)
    assert adapter.provider_name == "Dynamic CRM"
    assert "leads.create" in adapter.get_metadata().supported_operations

    installed = plugin_loader.install_from_manifest({"spec": openapi_spec})
    assert installed is True
    assert connector_registry.has("Dynamic CRM")


@pytest.mark.asyncio
async def test_connector_registry_and_factory():
    assert connector_registry.has("Gmail")
    assert connector_registry.has("Slack")

    adapter = ConnectorFactory.get_adapter("Gmail")
    assert adapter.provider_name == "Gmail"
    metadata = adapter.get_metadata()
    assert "gmail.messages.list" in metadata.supported_operations


@pytest.mark.asyncio
async def test_encrypted_secret_manager():
    creds = ConnectorCredentialModel(
        tenant_id="tenant_abc",
        provider="Slack",
        auth_type="Bearer",
        access_token="xoxb-test-slack-token-12345",
    )
    success = await secret_manager.set_secret("tenant_abc", "Slack", creds)
    assert success is True

    retrieved = await secret_manager.get_secret("tenant_abc", "Slack")
    assert retrieved is not None
    assert retrieved.access_token == "xoxb-test-slack-token-12345"


@pytest.mark.asyncio
async def test_connector_manager_execution():
    res = await connector_manager.execute(
        provider="Gmail",
        operation_id="gmail.messages.list",
        parameters={"q": "invoice"},
        tenant_id="tenant_abc",
    )
    assert res.operation_id == "gmail.messages.list"
    assert res.status_code in [200, 401]
    assert res.latency_ms > 0.0


@pytest.mark.asyncio
async def test_sub_20ms_initialization_benchmark():
    start = time.perf_counter()
    adapter = ConnectorFactory.get_adapter("Stripe")
    meta = adapter.get_metadata()
    duration_ms = (time.perf_counter() - start) * 1000.0

    assert meta.provider == "Stripe"
    assert duration_ms < 20.0, f"Connector initialization was {duration_ms:.2f}ms, expected sub-20ms!"
