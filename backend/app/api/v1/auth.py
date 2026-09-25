import logging
import urllib.parse
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_db_session
from app.services.auth_service import AuthService
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    RefreshTokenRequest,
    SSOExchangeRequest,
    ForgotPasswordRequest,

    ResetPasswordRequest,
)
from app.core.response import success_response
from app.core.config import settings

logger = logging.getLogger("agentflow.api.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])



@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    req: UserRegisterRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Register a new AgentFlow AI user account.
    """
    service = AuthService(db)
    user_data = await service.register(req)

    return success_response(
        data=user_data.model_dump(),
        message="User registered successfully",
    )


@router.post("/login", status_code=status.HTTP_200_OK)
async def login_user(
    req: UserLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Authenticate user credentials and issue JWT access and refresh tokens.
    """
    service = AuthService(db)

    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None

    tokens = await service.login(
        req,
        user_agent=user_agent,
        ip_address=ip_address,
    )

    return success_response(
        data=tokens.model_dump(),
        message="Signed in successfully",
    )


@router.post("/token")
async def oauth2_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session),
):
    """
    OAuth2 endpoint used by Swagger Authorize.
    Accepts form-data (username/password) and returns OAuth2 compatible tokens.
    """

    service = AuthService(db)

    login_request = UserLoginRequest(
        email=form_data.username,
        password=form_data.password,
    )

    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None

    tokens = await service.login(
        login_request,
        user_agent=user_agent,
        ip_address=ip_address,
    )

    return {
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout_user():
    """
    Logout current user session.
    """
    return success_response(
        data=None,
        message="Logged out successfully",
    )


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_access_token(
    req: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Obtain a new access token using a valid refresh token.
    """
    service = AuthService(db)

    tokens = await service.refresh_token(req.refresh_token)

    return success_response(
        data=tokens.model_dump(),
        message="Token refreshed successfully",
    )


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(req: ForgotPasswordRequest):
    """
    Send password reset instructions.
    (Placeholder)
    """
    return success_response(
        data=None,
        message="If the email exists, password reset instructions have been sent.",
    )


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(req: ResetPasswordRequest):
    """
    Reset password.
    (Placeholder)
    """
    return success_response(
        data=None,
        message="Password reset successfully.",
    )


@router.get("/google/login", status_code=status.HTTP_200_OK)
async def google_login(db: AsyncSession = Depends(get_db_session)):
    """
    Returns Google SSO login authorization URL for AgentFlow user application authentication.
    """
    service = AuthService(db)
    url = service.get_google_sso_url()
    logger.info("[AUTH-SSO] Generated Google application SSO authorization URL")
    return success_response(
        data={"provider": "google", "url": url},
        message="Google login URL generated successfully.",
    )


@router.get("/google/callback")
async def google_callback(
    code: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Handles Google OAuth SSO callback for AgentFlow user application authentication.
    Exchanges code for Google profile, generates a short-lived single-use handoff code, and redirects to frontend /oauth/result.
    Strictly zero access tokens or JWTs in the redirect URL.
    """
    frontend_base = settings.FRONTEND_URL.rstrip("/")

    if error or not code:
        logger.error(f"[AUTH-SSO] Google SSO callback error or missing code: error={error}")
        return RedirectResponse(
            url=f"{frontend_base}/oauth/result?mode=auth&status=error&message={error or 'missing_code'}",
            status_code=302,
        )

    try:
        service = AuthService(db)
        redirect_uri = f"http://127.0.0.1:8000{settings.API_V1_STR}/auth/google/callback"
        tokens, user_resp = await service.handle_google_sso_callback(code=code, redirect_uri=redirect_uri)

        # Generate short-lived, single-use exchange code (NO JWT in URL)
        sso_code = service.create_sso_one_time_code(tokens, user_resp, ttl_seconds=60)

        logger.info(f"[AUTH-SSO] User authenticated via Google SSO: email={user_resp.email} sso_code={sso_code}")

        params = {
            "mode": "auth",
            "status": "success",
            "code": sso_code,
        }
        query_str = urllib.parse.urlencode(params)
        return RedirectResponse(
            url=f"{frontend_base}/oauth/result?{query_str}",
            status_code=302,
        )
    except Exception as exc:
        logger.error(f"[AUTH-SSO] Google SSO callback exception: {exc}")
        return RedirectResponse(
            url=f"{frontend_base}/oauth/result?mode=auth&status=error&message=authentication_failed",
            status_code=302,
        )


@router.post("/google/exchange", status_code=status.HTTP_200_OK)
async def google_exchange(
    req: SSOExchangeRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Exchanges a short-lived single-use SSO authorization handoff code for JWT tokens and user profile.
    Single-use enforced: code is invalidated immediately upon exchange.
    """
    service = AuthService(db)
    tokens, user_resp = service.exchange_sso_one_time_code(req.code)

    logger.info(f"[AUTH-SSO] Successfully exchanged SSO one-time code for user {user_resp.email}")

    return success_response(
        data={
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "token_type": tokens.token_type,
            "expires_in": tokens.expires_in,
            "user": user_resp.model_dump(),
        },
        message="SSO code exchanged successfully.",
    )