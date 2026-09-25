import pytest
from app.connectors.security.secret_manager import secret_manager
from app.connectors.models import ConnectorCredentialModel
from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_secret_manager_aes256_encryption_decryption():
    tenant_id = "tenant_test_123"
    provider = "stripe"
    
    cred = ConnectorCredentialModel(
        tenant_id=tenant_id,
        provider=provider,
        auth_type="API_Key",
        api_key="sk_test_51Nx...secret_key",
        scopes=["read", "write"],
    )

    # Save secret
    saved = await secret_manager.set_secret(tenant_id, provider, cred)
    assert saved is True, "Failed to encrypt and store secret."

    # Retrieve and decrypt secret
    retrieved = await secret_manager.get_secret(tenant_id, provider)
    assert retrieved is not None, "Failed to retrieve decrypted secret."
    assert retrieved.provider == provider
    assert retrieved.auth_type == "API_Key"
    assert retrieved.api_key == "sk_test_51Nx...secret_key"
    assert "read" in retrieved.scopes


@pytest.mark.asyncio
async def test_all_9_providers_credential_support():
    providers = ["google", "slack", "github", "notion", "discord", "stripe", "openai", "anthropic", "generic_rest"]
    auth_schemes = ["OAuth2", "OAuth2", "Bearer", "API_Key", "Webhook_Secret", "API_Key", "API_Key", "API_Key", "Basic"]

    for p, scheme in zip(providers, auth_schemes):
        cred = ConnectorCredentialModel(
            tenant_id="usr_1",
            provider=p,
            auth_type=scheme,
            access_token=f"token_{p}",
            api_key=f"key_{p}",
        )
        saved = await secret_manager.set_secret("usr_1", p, cred)
        assert saved is True
        fetched = await secret_manager.get_secret("usr_1", p)
        assert fetched is not None
        assert fetched.auth_type == scheme


@pytest.mark.asyncio
async def test_credentials_api_list(async_client):
    token = create_access_token("usr_1")
    headers = {"Authorization": f"Bearer {token}"}

    cred = ConnectorCredentialModel(
        tenant_id="usr_1", provider="Google", auth_type="OAuth2", access_token="token_google",
    )
    await secret_manager.set_secret("usr_1", "Google", cred)
    from app.agents.oauth_ai import oauth_ai_service
    oauth_ai_service.connect_account("Google", "aswinkumaar07@gmail.com")

    res = await async_client.get("/api/v1/credentials", headers=headers)
    assert res.status_code == 200
    payload = res.json()
    assert payload["success"] is True
    data = payload["data"]
    assert isinstance(data, list)
    assert len(data) >= 1
    first = data[0]
    assert "provider" in first
    assert "status" in first
    assert "auth_type" in first
    assert "access_token" not in first  # Raw secrets must be masked


@pytest.mark.asyncio
async def test_credentials_api_save(async_client):
    token = create_access_token("usr_1")
    headers = {"Authorization": f"Bearer {token}"}

    save_payload = {
        "provider": "Anthropic",
        "auth_type": "API_Key",
        "api_key": "sk-ant-api03-secretkey...",
        "account_label": "Anthropic Production Account",
        "scopes": ["messages.create"],
    }
    res = await async_client.post("/api/v1/credentials/save", json=save_payload, headers=headers)
    assert res.status_code == 200
    payload = res.json()
    assert payload["success"] is True
    assert payload["data"]["provider"] == "Anthropic"
    assert payload["data"]["status"] == "CONNECTED"


@pytest.mark.asyncio
async def test_credentials_api_test_connection(async_client):
    token = create_access_token("usr_1")
    headers = {"Authorization": f"Bearer {token}"}

    test_payload = {"provider": "Slack", "auth_type": "OAuth2"}
    res = await async_client.post("/api/v1/credentials/test", json=test_payload, headers=headers)
    assert res.status_code == 200
    payload = res.json()
    assert payload["success"] is True


@pytest.mark.asyncio
async def test_credentials_api_rotate_and_delete(async_client):
    token = create_access_token("usr_1")
    headers = {"Authorization": f"Bearer {token}"}

    cred = ConnectorCredentialModel(
        tenant_id="usr_1", provider="Google", auth_type="OAuth2", access_token="token_google",
    )
    await secret_manager.set_secret("usr_1", "Google", cred)

    # Test Rotate
    rotate_res = await async_client.post("/api/v1/credentials/rotate", json={"provider": "Google"}, headers=headers)
    assert rotate_res.status_code == 200
    assert rotate_res.json()["success"] is True

    # Test Delete
    del_res = await async_client.delete("/api/v1/credentials/Google", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True
