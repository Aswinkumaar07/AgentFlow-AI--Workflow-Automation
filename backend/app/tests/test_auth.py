import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_auth_login_validation_error(async_client: AsyncClient):
    response = await async_client.post("/api/v1/auth/login", json={"email": "invalid-email", "password": "short"})
    assert response.status_code == 422
