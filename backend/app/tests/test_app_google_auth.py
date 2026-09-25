import urllib.parse
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_google_app_auth_login_url(async_client: AsyncClient):
    """Verifies GET /api/v1/auth/google/login generates valid application SSO URL."""
    response = await async_client.get("/api/v1/auth/google/login")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["provider"] == "google"
    assert "accounts.google.com" in data["data"]["url"]
    assert "auth%2Fgoogle%2Fcallback" in data["data"]["url"] or "auth/google/callback" in data["data"]["url"]


@pytest.mark.asyncio
async def test_google_app_auth_callback_secure_handshake(async_client: AsyncClient):
    """
    1. Verifies GET /api/v1/auth/google/callback does NOT place JWT in redirect URL.
    2. Verifies redirect contains one-time exchange 'code'.
    """
    response = await async_client.get(
        "/api/v1/auth/google/callback?code=test_auth_code_123",
        follow_redirects=False,
    )
    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "/oauth/result" in location
    assert "mode=auth" in location
    assert "status=success" in location
    assert "code=" in location

    # Security assertion: Access tokens and JWTs MUST NOT be exposed in URL query parameters
    assert "token=" not in location
    assert "refresh_token=" not in location
    assert "access_token=" not in location


@pytest.mark.asyncio
async def test_google_app_auth_code_exchange_and_single_use(async_client: AsyncClient):
    """
    2. Valid one-time code exchanges successfully.
    3. Same code cannot be reused (second attempt fails with 401).
    5. Successful exchange returns normal application auth response.
    """
    # Step 1: Initiate callback to generate a valid one-time code
    cb_resp = await async_client.get(
        "/api/v1/auth/google/callback?code=test_auth_code_123",
        follow_redirects=False,
    )
    location = cb_resp.headers.get("location", "")
    parsed_url = urllib.parse.urlparse(location)
    query_params = urllib.parse.parse_qs(parsed_url.query)

    sso_code = query_params["code"][0]
    assert sso_code.startswith("sso_code_")

    # Step 2: Exchange valid one-time code at POST /api/v1/auth/google/exchange
    exch_resp = await async_client.post(
        "/api/v1/auth/google/exchange",
        json={"code": sso_code},
    )
    assert exch_resp.status_code == 200
    exch_data = exch_resp.json()
    assert exch_data["success"] is True
    data_payload = exch_data["data"]

    # Verify standard auth response structure
    assert "access_token" in data_payload
    assert "refresh_token" in data_payload
    assert "user" in data_payload
    assert data_payload["user"]["email"] == "aswin@agentflow.ai"

    # Step 3: Attempt to reuse the SAME code — MUST be rejected with HTTP 401
    reuse_resp = await async_client.post(
        "/api/v1/auth/google/exchange",
        json={"code": sso_code},
    )
    assert reuse_resp.status_code == 401
    reuse_data = reuse_resp.json()
    err_msg = str(reuse_data.get("detail") or reuse_data.get("message") or reuse_data)
    assert "already been used" in err_msg or "Invalid" in err_msg or "Unauthorized" in err_msg


@pytest.mark.asyncio
async def test_google_app_auth_invalid_or_expired_code(async_client: AsyncClient):
    """
    4. Expired/invalid code is rejected with HTTP 401.
    """
    response = await async_client.post(
        "/api/v1/auth/google/exchange",
        json={"code": "sso_code_invalid_fake_code_999"},
    )
    assert response.status_code == 401
    data = response.json()
    err_msg = str(data.get("detail") or data.get("message") or data)
    assert "Invalid or missing" in err_msg or "Unauthorized" in err_msg



@pytest.mark.asyncio
async def test_google_app_auth_callback_error(async_client: AsyncClient):
    """Verifies GET /api/v1/auth/google/callback handles errors gracefully with 302 redirect."""
    response = await async_client.get(
        "/api/v1/auth/google/callback?error=access_denied",
        follow_redirects=False,
    )
    assert response.status_code == 302
    location = response.headers.get("location", "")
    assert "/oauth/result" in location
    assert "mode=auth" in location
    assert "status=error" in location

