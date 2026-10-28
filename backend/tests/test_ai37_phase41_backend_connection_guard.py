import pytest
from app.services.connection_readiness import (
    check_step_readiness,
    check_workflow_readiness,
    is_dynamic_openapi_operation,
    is_dynamic_public_openapi_operation,
    is_internal_provider,
)
from app.runtime.workflow_executor import workflow_runtime_executor_v3


@pytest.mark.asyncio
async def test_scenario_a_native_gmail_without_oauth_blocked():
    """Scenario A: Native Gmail without OAuth remains blocked."""
    gmail_step = {
        "step_id": "step_gmail",
        "provider": "gmail",
        "operation_id": "gmail.messages.list",
    }
    readiness = await check_step_readiness([gmail_step], user_id="usr_unbound_test_a")
    assert readiness["ready"] is False
    assert "gmail" in readiness["missing_connections"]


@pytest.mark.asyncio
async def test_scenario_b_native_slack_without_oauth_blocked():
    """Scenario B: Native Slack without OAuth remains blocked."""
    slack_step = {
        "step_id": "step_slack",
        "provider": "slack",
        "operation_id": "slack.chat.postMessage",
    }
    readiness = await check_step_readiness([slack_step], user_id="usr_unbound_test_b")
    assert readiness["ready"] is False
    assert "slack" in readiness["missing_connections"]


@pytest.mark.asyncio
async def test_scenario_c_public_dynamic_openapi_operation_passes():
    """Scenario C: Public dynamic OpenAPI operation passes native OAuth readiness check."""
    petstore_public_step = {
        "step_id": "step_petstore",
        "provider": "generic_rest",
        "operation_id": "getPetById",
        "parameters": {
            "is_dynamic_api": True,
            "security_schemes": {},
            "security_requirements": [],
            "petId": 1,
        },
    }
    assert is_dynamic_openapi_operation(petstore_public_step) is True
    assert is_dynamic_public_openapi_operation(petstore_public_step) is True

    readiness = await check_step_readiness([petstore_public_step], user_id="usr_unbound_test_c")
    assert readiness["ready"] is True
    assert len(readiness["missing_connections"]) == 0


@pytest.mark.asyncio
async def test_scenario_d_authenticated_dynamic_openapi_not_misclassified():
    """Scenario D: Authenticated dynamic OpenAPI operation passes native OAuth store preflight check."""
    authenticated_api_step = {
        "step_id": "step_auth_api",
        "provider": "generic_rest",
        "operation_id": "getSecureData",
        "parameters": {
            "is_dynamic_api": True,
            "security_schemes": {"apiKeyHeader": {"type": "apiKey", "name": "X-API-KEY", "in": "header"}},
            "security_requirements": [{"apiKeyHeader": []}],
        },
    }
    assert is_dynamic_openapi_operation(authenticated_api_step) is True
    assert is_dynamic_public_openapi_operation(authenticated_api_step) is False

    readiness = await check_step_readiness([authenticated_api_step], user_id="usr_unbound_test_d")
    assert readiness["ready"] is True
    assert "generic_rest" not in readiness["missing_connections"]


@pytest.mark.asyncio
async def test_scenario_e_normal_native_connector_follows_readiness():
    """Scenario E: Normal internal or connected providers follow readiness rules."""
    ai_step = {"step_id": "step_ai", "provider": "ai", "operation_id": "ai.summarize"}
    readiness = await check_step_readiness([ai_step], user_id="usr_test_e")
    assert readiness["ready"] is True
    assert len(readiness["missing_connections"]) == 0


@pytest.mark.asyncio
async def test_scenario_f_unknown_metadata_not_bypassing_security():
    """Scenario F: Unknown custom non-dynamic provider remains blocked if not connected."""
    unknown_step = {"step_id": "step_unk", "provider": "CustomVendor", "operation_id": "vendor.doSomething"}
    assert is_dynamic_openapi_operation(unknown_step) is False

    readiness = await check_step_readiness([unknown_step], user_id="usr_unbound_test_f")
    assert readiness["ready"] is False
    assert "CustomVendor" in readiness["missing_connections"]


@pytest.mark.asyncio
async def test_scenario_g_workflow_executor_preflight_passes_for_petstore():
    """Scenario G: Workflow executor preflight allows public dynamic Petstore workflow without blocking."""
    wf_spec = {
        "workflow_id": "wf_test_phase41_petstore",
        "tenant_id": "usr_test_phase41",
        "steps": [
            {
                "step_id": "step_1",
                "provider": "generic_rest",
                "operation_id": "getOrderById",
                "parameters": {
                    "is_dynamic_api": True,
                    "security_schemes": {},
                    "security_requirements": [],
                },
            },
            {
                "step_id": "step_2",
                "provider": "generic_rest",
                "operation_id": "getPetById",
                "parameters": {
                    "is_dynamic_api": True,
                    "security_schemes": {},
                    "security_requirements": [],
                },
            },
        ],
    }

    # Preflight check should pass check_step_readiness
    readiness = await check_step_readiness(wf_spec["steps"], user_id="usr_test_phase41")
    assert readiness["ready"] is True
    assert len(readiness["missing_connections"]) == 0
