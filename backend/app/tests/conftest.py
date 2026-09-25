import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.connectors.security.secret_manager import secret_manager


@pytest.fixture(autouse=True)
def isolate_global_secret_manager_vault(tmp_path):
    """Ensure global secret_manager singleton uses an isolated temporary vault during test runs, protecting storage/credentials/vault.json."""
    orig_vault_path = secret_manager.vault_path
    orig_store = dict(secret_manager._store)

    test_vault = str(tmp_path / "test_vault.json")
    secret_manager.vault_path = test_vault
    secret_manager._store.clear()

    yield

    secret_manager.vault_path = orig_vault_path
    with secret_manager._lock:
        secret_manager._store = orig_store


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

