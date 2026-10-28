import logging
import re
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.response import success_response
from app.dependencies.auth import get_current_user
from app.models.users import User
from app.connectors.registry import connector_registry
from app.connectors.models import OperationSchemaModel, ParameterSchemaModel

logger = logging.getLogger("agentflow.api.v1.connectors")
router = APIRouter(prefix="/connectors", tags=["Dynamic Connector Registry"])


def _get_dynamic_openapi_operation_schema(provider_name: str, operation_id: str) -> Optional[OperationSchemaModel]:
    """
    Phase 35: Resolves dynamically discovered OpenAPI operation schemas from in-memory catalog
    when static native connector lookup produces a miss.
    """
    from app.agents.connector_ai.operation_ranker import operation_ranker

    prov_clean = (provider_name or "").strip().lower()
    op_clean = (operation_id or "").strip()

    target_op = None
    for item in operation_ranker.OPERATION_CATALOG:
        c_op = item.get("operation") or item.get("operation_id") or ""
        if c_op == op_clean:
            c_prov = (item.get("provider") or "").strip().lower()
            if prov_clean in ["generic", "generic_rest", "generic rest", ""] or c_prov == prov_clean or prov_clean in c_prov or c_prov in prov_clean:
                target_op = item
                break

    if not target_op:
        return None

    summary = target_op.get("summary") or op_clean
    params_dict = target_op.get("parameters", {})
    raw_url = params_dict.get("url", "") if isinstance(params_dict, dict) else ""
    path_params = re.findall(r"\{([a-zA-Z0-9_]+)\}", raw_url) if raw_url else []

    req_params_models: List[ParameterSchemaModel] = []
    opt_params_models: List[ParameterSchemaModel] = []
    seen_params = set()

    # 1. Path Parameters (Required)
    for p_name in path_params:
        if p_name not in seen_params:
            seen_params.add(p_name)
            p_type = "number" if ("id" in p_name.lower() or p_name.lower().endswith("id")) else "string"
            req_params_models.append(
                ParameterSchemaModel(
                    name=p_name,
                    display_name=p_name.replace("_", " ").title(),
                    type=p_type,
                    required=True,
                    description=f"Path parameter {p_name}",
                )
            )

    # 2. Required parameters from request body schema
    req_schema = target_op.get("request_schema", {})
    if isinstance(req_schema, dict):
        req_fields = req_schema.get("required", [])
        if isinstance(req_fields, list):
            for r_field in req_fields:
                if isinstance(r_field, str) and r_field not in seen_params:
                    seen_params.add(r_field)
                    req_params_models.append(
                        ParameterSchemaModel(
                            name=r_field,
                            display_name=r_field.replace("_", " ").title(),
                            type="string",
                            required=True,
                            description=f"Required parameter {r_field}",
                        )
                    )

    # 3. Query parameters (Optional)
    query_params = target_op.get("query_params", [])
    if isinstance(query_params, list):
        for q_param in query_params:
            if isinstance(q_param, str) and q_param not in seen_params:
                seen_params.add(q_param)
                opt_params_models.append(
                    ParameterSchemaModel(
                        name=q_param,
                        display_name=q_param.replace("_", " ").title(),
                        type="string",
                        required=False,
                        description=f"Query parameter {q_param}",
                    )
                )

    # 4. Header parameters
    header_params = target_op.get("header_params", [])
    if isinstance(header_params, list):
        for h_param in header_params:
            if isinstance(h_param, str) and h_param not in seen_params:
                seen_params.add(h_param)
                opt_params_models.append(
                    ParameterSchemaModel(
                        name=h_param,
                        display_name=h_param.replace("_", " ").title(),
                        type="string",
                        required=False,
                        description=f"Header parameter {h_param}",
                    )
                )

    # 5. Optional parameters
    optional_params = target_op.get("optional_params", [])
    if isinstance(optional_params, list):
        for o_param in optional_params:
            if isinstance(o_param, str) and o_param not in seen_params:
                seen_params.add(o_param)
                opt_params_models.append(
                    ParameterSchemaModel(
                        name=o_param,
                        display_name=o_param.replace("_", " ").title(),
                        type="string",
                        required=False,
                        description=f"Optional parameter {o_param}",
                    )
                )

    return OperationSchemaModel(
        id=op_clean,
        display_name=summary,
        description=summary,
        required_parameters=req_params_models,
        optional_parameters=opt_params_models,
        default_values={},
    )


@router.get("", status_code=status.HTTP_200_OK)
async def list_connectors(
    current_user: User = Depends(get_current_user),
):
    """Retrieve metadata for all 16 supported SaaS & Logic connectors."""
    connectors = connector_registry.get_all_metadata()
    return success_response(data=connectors, message="Dynamic connector metadata retrieved successfully.")


@router.get("/{provider}", status_code=status.HTTP_200_OK)
async def get_connector_definition(
    provider: str,
    current_user: User = Depends(get_current_user),
):
    """Retrieve full metadata and operation schemas for a specific connector provider."""
    meta = connector_registry.get_connector_metadata(provider)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector provider '{provider}' not found in registry."
        )
    return success_response(data=meta.model_dump(), message=f"Metadata for provider '{provider}' retrieved.")


@router.get("/{provider}/{operation}", status_code=status.HTTP_200_OK)
async def get_operation_schema(
    provider: str,
    operation: str,
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve specific operation schema detailing required & optional parameters,
    field types, validation rules, and default values.
    Prioritizes native connector registry, falling back to dynamic OpenAPI discovery catalog.
    """
    # 1. Native connector lookup (Highest Priority)
    schema = connector_registry.get_operation_schema(provider, operation)
    if not schema:
        # Fallback search if provider prefix mismatch in native registry
        meta = connector_registry.get_connector_metadata(provider)
        if meta and meta.operation_schemas and operation in meta.operation_schemas:
            schema = meta.operation_schemas[operation]

    # 2. Dynamic OpenAPI discovery catalog lookup (Phase 35 Bridge)
    if not schema:
        schema = _get_dynamic_openapi_operation_schema(provider, operation)

    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operation schema '{operation}' for provider '{provider}' not found."
        )

    data = schema.model_dump() if hasattr(schema, "model_dump") else schema
    return success_response(data=data, message=f"Operation schema for '{operation}' retrieved.")
