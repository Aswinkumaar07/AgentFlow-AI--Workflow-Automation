from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.workflows import router as workflows_router
from app.api.v1.executions import router as executions_router
from app.api.v1.history import router as history_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.settings import router as settings_router
from app.api.v1.ai import router as ai_router
from app.api.v1.oauth import router as oauth_router
from app.api.v1.templates import router as templates_router
from app.api.v1.runtime import router as runtime_router
from app.api.v1.triggers import router as triggers_router
from app.api.v1.enterprise import router as enterprise_router
from app.api.v1.copilot import router as copilot_router
from app.api.v1.oauth_ai import router as oauth_ai_router
from app.api.v1.parameter_autofill import router as parameter_autofill_router
from app.api.v1.reasoning import router as reasoning_router
from app.api.v1.visual_runtime import router as visual_runtime_router
from app.api.v1.optimizer import router as optimizer_router
from app.api.v1.self_healing import router as self_healing_router
from app.api.v1.connector_studio import router as connector_studio_router
from app.api.v1.marketplace import router as marketplace_router
from app.api.v1.autonomous import router as autonomous_router
from app.api.v1.ws_execution import router as ws_execution_router
from app.api.v1.connectors import router as connectors_router
from app.api.v1.credentials import router as credentials_router
from app.api.v1.scheduler import router as scheduler_router
from app.api.v1.gmail_attachments import router as gmail_attachments_router
from app.api.v1.api_keys import router as api_keys_router
from app.api.v1.audit import router as audit_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(workflows_router)
api_v1_router.include_router(executions_router)
api_v1_router.include_router(history_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(settings_router)
api_v1_router.include_router(ai_router)
api_v1_router.include_router(oauth_router)
api_v1_router.include_router(templates_router)
api_v1_router.include_router(runtime_router)
api_v1_router.include_router(triggers_router)
api_v1_router.include_router(enterprise_router)
api_v1_router.include_router(copilot_router)
api_v1_router.include_router(oauth_ai_router)
api_v1_router.include_router(parameter_autofill_router)
api_v1_router.include_router(reasoning_router)
api_v1_router.include_router(visual_runtime_router)
api_v1_router.include_router(optimizer_router)
api_v1_router.include_router(self_healing_router)
api_v1_router.include_router(connector_studio_router)
api_v1_router.include_router(marketplace_router)
api_v1_router.include_router(autonomous_router)
api_v1_router.include_router(ws_execution_router)
api_v1_router.include_router(connectors_router)
api_v1_router.include_router(credentials_router)
api_v1_router.include_router(scheduler_router)
api_v1_router.include_router(gmail_attachments_router)
api_v1_router.include_router(api_keys_router)
api_v1_router.include_router(audit_router)
