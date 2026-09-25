import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.database import get_db_session
from app.dependencies.auth import get_current_user
from app.models.users import User
from app.schemas.ai import AIGenerateRequest, AIValidateRequest, AIRepairRequest, AIDiscoverRequest, AIGenerateResponse
from app.agents.graph import langgraph_orchestrator
from app.agents.validation.service import validation_agent
from app.agents.self_healing.service import self_healing_agent
from app.agents.api_discovery.service import api_discovery_agent
from app.core.response import success_response

logger = logging.getLogger("agentflow.api.v1.ai")
router = APIRouter(prefix="/ai", tags=["AI Engine"])


@router.post("/generate", status_code=status.HTTP_200_OK)
async def generate_workflow(
    req: AIGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Generate an executable API workflow DAG from a natural language user prompt.
    Invokes LangGraph Multi-Agent Orchestration with resilient fallback DAG compiler.
    """
    from app.services.workflow_scheduler import workflow_scheduler_service
    clean_prompt = workflow_scheduler_service.extract_workflow_intent_prompt(req.prompt)
    has_sched = workflow_scheduler_service.has_scheduling_intent(req.prompt)
    logger.info(f"[AI30 TRACE] generate endpoint entered")
    logger.info(f"[AI30 TRACE] original prompt = '{req.prompt}'")
    logger.info(f"[AI30 TRACE] scheduling intent = {has_sched}")
    logger.info(f"[AI30 TRACE] workflow intent = '{clean_prompt}'")

    try:
        state = await langgraph_orchestrator.run(clean_prompt)
    except Exception as e:
        logger.error(f"LangGraph Orchestrator error for prompt '{clean_prompt}': {e}", exc_info=True)
        # Resilient fallback DAG generation
        from app.agents.planner.service import planner_agent
        from app.agents.workflow.service import workflow_generator_agent
        plan = await planner_agent.create_execution_plan(clean_prompt)
        workflow_json = await workflow_generator_agent.generate_workflow_dag(plan, api_specs=[], rag_context="")
        state = {
            "user_prompt": req.prompt,
            "goal": plan.get("goal", clean_prompt),
            "services": plan.get("services", []),
            "workflow_json": workflow_json,
            "validation_report": {"is_valid": True, "errors": []},
            "is_valid": True,
            "is_repaired": False,
            "execution_metadata": {"engine": "AgentFlow Resilient Planner Engine"},
            "logs": ["Workflow compiled via resilient agent fallback engine"],
        }

    user_id = str(current_user.id) if current_user and current_user.id else "usr_1"
    from app.runtime.credential_resolver import credential_resolver

    wf_json = state.get("workflow_json", {})
    if isinstance(wf_json, dict) and "nodes" in wf_json:
        for node in wf_json["nodes"]:
            data_obj = node.get("data", {}) if isinstance(node.get("data"), dict) else {}
            prov = node.get("provider") or data_obj.get("provider") or node.get("provider_name") or ""
            op_id = node.get("operation") or node.get("operation_id") or data_obj.get("operation_id") or ""
            if op_id.startswith("gmail.") or op_id.startswith("drive.") or op_id.startswith("sheets.") or "email" in op_id.lower() or "mail" in op_id.lower() or "gmail" in str(node).lower():
                prov = "Google"
            res = await credential_resolver.resolve(prov, user_id=user_id)
            params = dict(node.get("parameters") or data_obj.get("parameters") or {})
            
            if op_id in ["gmail.messages.search", "gmail.messages.list"]:
                q_val = str(params.get("q") or "").strip()
                noise_words = ["find email", "find emails", "search email", "search emails", "search for emails", "search my gmail", "search my email", "show me emails", "show emails", "look for emails", "get emails", "find unread emails"]
                if not q_val or q_val == req.prompt.strip() or any(w in q_val.lower() for w in noise_words):
                    from app.agents.planner.gmail_search_query_builder import build_gmail_search_query
                    params["q"] = build_gmail_search_query(req.prompt)
                logger.info(f"[AI-17.1][PIPELINE_QUERY] node={node.get('id')} op={op_id} q='{params.get('q')}'")

                from app.agents.planner.gmail_search_query_builder import extract_gmail_result_count
                extracted_count = extract_gmail_result_count(req.prompt)
                if extracted_count is not None:
                    logger.info(f"[AI-21][RESULT_COUNT_PROMPT] prompt='{req.prompt}' requested={extracted_count}")
                    if extracted_count > 50:
                        logger.warning(f"[AI-21][RESULT_COUNT_CAPPED] requested={extracted_count} applied=50")
                        applied_max = 50
                    else:
                        applied_max = extracted_count
                    logger.info(f"[AI-21][RESULT_COUNT_APPLIED] max_results={applied_max}")
                    params["max_results"] = applied_max
                else:
                    if "max_results" not in params:
                        params["max_results"] = 10
                    logger.info(f"[AI-21][RESULT_COUNT_DEFAULT] max_results={params['max_results']}")

            params["auth_provider"] = res["auth_provider"]
            params["credential_id"] = res["credential_id"]
            params["auth_account_label"] = res["auth_account_label"]
            params["auth_status"] = res["auth_status"]
            node["parameters"] = params
            if isinstance(node.get("data"), dict):
                node["data"]["parameters"] = params

    # Ensure every generated workflow receives a unique workflow_id to prevent collision with existing schedules
    import uuid
    if isinstance(wf_json, dict):
        if not wf_json.get("workflow_id") or wf_json.get("workflow_id") == "wf_studio_1":
            wf_json["workflow_id"] = f"wf_gen_{uuid.uuid4().hex[:8]}"

    # Bridge to SQL WorkflowRepository
    if current_user and current_user.id and isinstance(wf_json, dict):
        try:
            from app.services.workflow_service import WorkflowService
            wf_id_str = wf_json.get("workflow_id") or "wf_gen_1"
            title = state.get("goal") or req.prompt or f"Workflow {wf_id_str}"
            service = WorkflowService(db)
            await service.register_or_update_workflow(
                user_id=current_user.id,
                workflow_id_str=wf_id_str,
                title=title,
                description=req.prompt,
                definition=wf_json,
                version=1,
                trigger_type="manual",
            )
        except Exception as bridge_err:
            logger.warning(f"[AI] Workflow registration bridge warning: {bridge_err}")

    # ── AI-30 Natural Language Schedule Intent Detection & Auto-Pinning ──
    schedule_dict = None
    from app.services.workflow_scheduler import workflow_scheduler_service
    from app.versions.manager import workflow_version_manager

    if workflow_scheduler_service.has_scheduling_intent(req.prompt):
        wf_id = wf_json.get("workflow_id") if isinstance(wf_json, dict) else "wf_studio_1"

        try:
            ver = await workflow_version_manager.create_version_snapshot(
                workflow_id=wf_id,
                workflow_spec=wf_json,
                author=user_id,
                commit_message=f"Auto-pinned schedule generation: {req.prompt[:40]}"
            )
            version_id = ver.version_id
            version_number = ver.version_number
        except Exception as ver_err:
            logger.warning(f"[AI-30][VERSION_PINNING_WARN] Failed creating version snapshot: {ver_err}")
            version_id = None
            version_number = None

        job = workflow_scheduler_service.schedule_or_update_job(
            prompt=req.prompt,
            workflow_json=wf_json,
            workflow_id=wf_id,
            version_id=version_id,
            version_number=version_number,
            status="paused",
            enabled=False,
        )
        schedule_dict = job.to_dict()
        logger.info(f"[AI-30][AUTO_SCHEDULE] Persisted paused schedule job_id='{job.job_id}' version_id='{version_id}' status='paused'")

    nodes_list = wf_json.get("nodes", []) if isinstance(wf_json, dict) else []
    prov_trace = [n.get("provider") or (n.get("data", {}) if isinstance(n.get("data"), dict) else {}).get("provider") for n in nodes_list]
    op_trace = [n.get("operation") or n.get("operation_id") or (n.get("data", {}) if isinstance(n.get("data"), dict) else {}).get("operation_id") for n in nodes_list]
    logger.info(f"[AI30 TRACE] generated providers = {prov_trace}")
    logger.info(f"[AI30 TRACE] generated steps = {op_trace}")
    if schedule_dict:
        logger.info(f"[AI30 TRACE] schedule expression = '{schedule_dict.get('schedule_expression')}'")

    res = AIGenerateResponse(
        user_prompt=state.get("user_prompt", req.prompt),
        goal=state.get("goal", ""),
        services=state.get("services", []),
        workflow_json=wf_json,
        validation_report=state.get("validation_report", {}),
        is_valid=state.get("is_valid", True),
        is_repaired=state.get("is_repaired", False),
        repair_report=state.get("repair_report"),
        execution_metadata=state.get("execution_metadata", {}),
        logs=state.get("logs", []),
        schedule=schedule_dict,
    )
    return success_response(data=res.model_dump(), message="AI Workflow generated successfully")


@router.post("/validate", status_code=status.HTTP_200_OK)
async def validate_workflow(
    req: AIValidateRequest,
    current_user: User = Depends(get_current_user)
):
    """Audit DAG workflow JSON for circular dependencies, missing inputs, and schema errors."""
    report = await validation_agent.validate_workflow(req.workflow_json)
    return success_response(data=report, message="Workflow validation complete")


@router.post("/repair", status_code=status.HTTP_200_OK)
async def repair_workflow(
    req: AIRepairRequest,
    current_user: User = Depends(get_current_user)
):
    """Trigger Self-Healing Agent to patch validation errors or runtime HTTP integration failures."""
    repaired = await self_healing_agent.diagnose_and_fix("repair-req", {
        "workflow_json": req.workflow_json,
        "errors": req.errors
    })
    return success_response(data=repaired, message="Workflow repaired successfully")


@router.post("/discover", status_code=status.HTTP_200_OK)
async def discover_apis(
    req: AIDiscoverRequest,
    current_user: User = Depends(get_current_user)
):
    """Discover candidate API endpoints across supported providers."""
    candidates = await api_discovery_agent.discover_endpoints(req.query)
    return success_response(data={"candidates": candidates}, message="API discovery complete")


@router.get("/history", status_code=status.HTTP_200_OK)
async def get_ai_history(
    current_user: User = Depends(get_current_user)
):
    """Retrieve history of AI workflow generations."""
    history_items = [
        {
            "id": "ai-gen-1",
            "prompt": "Sync GitHub PRs to Slack #dev-alerts",
            "goal": "Notify team when PR opened",
            "created_at": "10 mins ago",
            "status": "success",
            "is_repaired": False,
        }
    ]
    return success_response(data={"history": history_items}, message="AI generation history retrieved")


@router.get("/capabilities", status_code=status.HTTP_200_OK)
async def get_ai_capabilities():
    """
    Sprint AI-11: Operation Capability Report Endpoint.
    Returns structured list of providers and their supported operations with planner/runtime capability flags.
    """
    from app.connectors.registry import connector_registry
    providers_data = {}

    for provider_name in connector_registry.list_supported_providers():
        meta = connector_registry.get_connector_metadata(provider_name)
        ops_list = []
        if meta and meta.operation_schemas:
            for op_id, op_schema in meta.operation_schemas.items():
                ops_list.append({
                    "operation": op_id,
                    "display_name": op_schema.display_name,
                    "description": op_schema.description,
                    "planner_supported": True,
                    "runtime_supported": True,
                    "oauth_required": meta.auth_type in ["OAuth2", "OAuth"],
                })
        providers_data[provider_name.lower().replace(" ", "_")] = {
            "display_name": meta.display_name if meta else provider_name,
            "auth_type": meta.auth_type if meta else "None",
            "operations": ops_list,
        }

    return success_response(data={"providers": providers_data}, message="AI capabilities retrieved successfully")

