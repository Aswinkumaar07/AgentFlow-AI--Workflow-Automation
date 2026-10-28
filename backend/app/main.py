import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AgentFlowException
from app.core.response import error_response
from app.database.session import dispose_engine
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.security_middleware import SecurityHeadersMiddleware
from app.api.v1.router import api_v1_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("agentflow")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    logger.info("Initializing AgentFlow AI Enterprise Backend...")

    # ── SPRINT AUTH-7: Startup Validation for Google OAuth Configuration ──────
    missing_oauth = []
    if not settings.GOOGLE_CLIENT_ID:
        missing_oauth.append("GOOGLE_CLIENT_ID")
    if not settings.GOOGLE_CLIENT_SECRET:
        missing_oauth.append("GOOGLE_CLIENT_SECRET")
    if not settings.GOOGLE_REDIRECT_URI:
        missing_oauth.append("GOOGLE_REDIRECT_URI")

    if missing_oauth:
        logger.warning(f"[AUTH-7] Google OAuth configuration INVALID. Missing: {', '.join(missing_oauth)}")
    else:
        logger.info(f"[AUTH-7] Google OAuth configuration loaded: client_id_present=True redirect_uri={settings.GOOGLE_REDIRECT_URI} provider=Google")

    missing_slack_oauth = []
    if not settings.SLACK_CLIENT_ID:
        missing_slack_oauth.append("SLACK_CLIENT_ID")
    if not settings.SLACK_CLIENT_SECRET:
        missing_slack_oauth.append("SLACK_CLIENT_SECRET")
    if not settings.SLACK_REDIRECT_URI:
        missing_slack_oauth.append("SLACK_REDIRECT_URI")

    if missing_slack_oauth:
        logger.warning(f"[AUTH-7] Slack OAuth configuration INVALID/incomplete. Missing: {', '.join(missing_slack_oauth)}")
    else:
        logger.info(f"[AUTH-7] Slack OAuth configuration loaded: client_id_present=True redirect_uri={settings.SLACK_REDIRECT_URI} provider=Slack")

    logger.warning(f"[AUTH-8] Startup GOOGLE_CLIENT_ID={settings.GOOGLE_CLIENT_ID}")

    from app.services.workflow_scheduler import workflow_scheduler_service
    logger.info("[SCHEDULER_STARTUP] Starting background workflow scheduler tick loop...")
    workflow_scheduler_service.start_background_tick(interval_seconds=5)

    yield
    logger.info("[SCHEDULER_SHUTDOWN] Cancelling background workflow scheduler tick loop...")
    if workflow_scheduler_service._tick_task and not workflow_scheduler_service._tick_task.done():
        workflow_scheduler_service._tick_task.cancel()
    logger.info("Shutting down database connection pools...")
    await dispose_engine()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    description="Enterprise API Workflow Automation Backend built with FastAPI, SQLAlchemy 2.0, PostgreSQL & Redis.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── 1. Security Headers Middleware (OWASP Enforced) ──────────────────────────
app.add_middleware(SecurityHeadersMiddleware)

# ── 2. CORS Middleware ───────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 3. Custom Logging & Telemetry Middleware ─────────────────────────────────
app.add_middleware(LoggingMiddleware)

# ── Centralized Exception Handlers ───────────────────────────────────────────
@app.exception_handler(AgentFlowException)
async def agentflow_exception_handler(request: Request, exc: AgentFlowException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            message=exc.message,
            error_code=exc.error_code,
            details=exc.details,
        ),
    )

@app.exception_handler(Exception)
async def global_unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Server Error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            message="Internal server error",
            error_code="INTERNAL_SERVER_ERROR_500",
        ),
    )

# ── Include V1 API Routers ───────────────────────────────────────────────────
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Root"])
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
    }
