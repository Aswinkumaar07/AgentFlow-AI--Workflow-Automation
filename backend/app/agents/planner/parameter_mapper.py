import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ParameterMappingCandidate(BaseModel):
    target_param: str
    source_path: str
    confidence: float
    reason: str
    safe_to_apply: bool = True


class ParameterMappingResult(BaseModel):
    mappings: Dict[str, str] = Field(default_factory=dict)
    candidates: List[ParameterMappingCandidate] = Field(default_factory=list)


def _normalize_name(name: str) -> str:
    """Normalizes camelCase, snake_case, kebab-case to lowercase alphanumeric without separators."""
    s = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
    return s.lower().replace('-', '').replace('_', '').strip()


def _to_snake_case(name: str) -> str:
    s = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
    return s.lower().replace('-', '_').strip()


def _flatten_response_properties(schema: Dict[str, Any], prefix: str = "") -> List[Dict[str, Any]]:
    """Recursively flattens an OpenAPI response_schema into a list of property descriptors."""
    flattened = []
    if not isinstance(schema, dict):
        return flattened

    stype = schema.get("type", "object")
    if stype == "array" and "items" in schema and isinstance(schema["items"], dict):
        # Flatten array item properties
        item_props = _flatten_response_properties(schema["items"], prefix=prefix)
        for p in item_props:
            flattened.append(p)
        return flattened

    props = schema.get("properties", {})
    if isinstance(props, dict):
        for prop_name, prop_def in props.items():
            path = f"{prefix}.{prop_name}" if prefix else prop_name
            p_type = prop_def.get("type", "string") if isinstance(prop_def, dict) else "string"
            flattened.append({
                "name": prop_name,
                "path": path,
                "type": p_type,
                "schema": prop_def if isinstance(prop_def, dict) else {}
            })
            if p_type == "object" and isinstance(prop_def, dict) and "properties" in prop_def:
                flattened.extend(_flatten_response_properties(prop_def, prefix=path))

    return flattened


def _is_type_compatible(src_type: str, tgt_type: str) -> bool:
    """Checks conservative type compatibility."""
    if not src_type or not tgt_type:
        return True  # Unknown type is not automatically rejected
    src = src_type.lower()
    tgt = tgt_type.lower()

    if src == tgt:
        return True
    if src in ["integer", "number"] and tgt in ["integer", "number", "string"]:
        return True
    if src == "string" and tgt in ["string", "integer", "number"]:
        return True
    if src in ["object", "array"] and tgt in ["integer", "number", "boolean"]:
        return False
    if src in ["object"] and tgt in ["string", "array"]:
        return False
    if src in ["array"] and tgt in ["object", "integer", "number", "boolean"]:
        return False

    return True


class ResponseToRequestParameterMapper:
    """
    Pure Planner-Side Parameter Mapping Helper Engine.
    Matches upstream operation response_schema properties against downstream required parameter inputs.
    Generates safe variable references in format: {{UpstreamNodeID.data.path}}
    """

    def map_parameters(
        self,
        upstream_node_id: str,
        upstream_response_schema: Dict[str, Any],
        downstream_required_params: List[str],
        downstream_request_schema: Optional[Dict[str, Any]] = None,
        existing_downstream_params: Optional[Dict[str, Any]] = None
    ) -> ParameterMappingResult:
        result = ParameterMappingResult()
        if not upstream_response_schema or not downstream_required_params:
            return result

        flattened_fields = _flatten_response_properties(upstream_response_schema)
        if not flattened_fields:
            return result

        existing_params = existing_downstream_params or {}
        downstream_props = (downstream_request_schema or {}).get("properties", {}) if isinstance(downstream_request_schema, dict) else {}

        for target_param in downstream_required_params:
            # Skip if target_param already has a literal value provided explicitly
            if target_param in existing_params and existing_params[target_param] is not None:
                val = existing_params[target_param]
                if not (isinstance(val, str) and (val == f"{{{{{target_param}}}}}" or val == "")):
                    continue

            tgt_norm = _normalize_name(target_param)
            tgt_snake = _to_snake_case(target_param)
            tgt_type = downstream_props.get(target_param, {}).get("type", "") if isinstance(downstream_props, dict) else ""

            matched_candidates: List[ParameterMappingCandidate] = []

            for field in flattened_fields:
                fname = field["name"]
                fpath = field["path"]
                ftype = field["type"]
                fnorm = _normalize_name(fname)
                fsnake = _to_snake_case(fname)

                if not _is_type_compatible(ftype, tgt_type):
                    continue

                # 1. Exact Field Name Match
                if fname == target_param:
                    matched_candidates.append(
                        ParameterMappingCandidate(
                            target_param=target_param,
                            source_path=fpath,
                            confidence=1.0,
                            reason=f"Exact field name match ('{fname}')"
                        )
                    )
                    continue

                # 2. Normalized Name Match (camelCase -> snake_case)
                if fnorm == tgt_norm or fsnake == tgt_snake:
                    matched_candidates.append(
                        ParameterMappingCandidate(
                            target_param=target_param,
                            source_path=fpath,
                            confidence=0.95,
                            reason=f"Normalized name match ('{fname}' -> '{target_param}')"
                        )
                    )
                    continue

                # 3. Identifier Suffix Match (id -> user_id, id -> customer_id, customer.id -> customer_id)
                if tgt_snake.endswith("_id") or target_param.endswith("Id"):
                    prefix_part = tgt_snake[:-3] if tgt_snake.endswith("_id") else target_param[:-2]
                    prefix_norm = _normalize_name(prefix_part)

                    # Case A: Response root field is "id"
                    if fname.lower() == "id":
                        matched_candidates.append(
                            ParameterMappingCandidate(
                                target_param=target_param,
                                source_path=fpath,
                                confidence=0.85,
                                reason=f"Identifier suffix match ('id' -> '{target_param}')"
                            )
                        )
                        continue

                    # Case B: Nested field "customer.id" -> "customer_id"
                    if fpath.endswith(".id"):
                        parent_part = fpath.split(".")[0]
                        if _normalize_name(parent_part) == prefix_norm:
                            matched_candidates.append(
                                ParameterMappingCandidate(
                                    target_param=target_param,
                                    source_path=fpath,
                                    confidence=0.90,
                                    reason=f"Nested identifier match ('{fpath}' -> '{target_param}')"
                                )
                            )
                            continue

            # Evaluate ambiguity & select safest candidate
            if len(matched_candidates) == 1:
                cand = matched_candidates[0]
                result.candidates.append(cand)
                result.mappings[target_param] = f"{{{{{upstream_node_id}.data.{cand.source_path}}}}}"
            elif len(matched_candidates) > 1:
                max_conf = max(c.confidence for c in matched_candidates)
                top_cands = [c for c in matched_candidates if c.confidence == max_conf]
                if len(top_cands) == 1:
                    cand = top_cands[0]
                    result.candidates.append(cand)
                    result.mappings[target_param] = f"{{{{{upstream_node_id}.data.{cand.source_path}}}}}"
                else:
                    # AMBIGUOUS: Multiple equally plausible candidates -> REJECT (NO_SAFE_MAPPING)
                    for c in matched_candidates:
                        c.safe_to_apply = False
                        c.reason += " [REJECTED: Ambiguous multiple candidate matches]"
                        result.candidates.append(c)

        return result


parameter_mapper = ResponseToRequestParameterMapper()
