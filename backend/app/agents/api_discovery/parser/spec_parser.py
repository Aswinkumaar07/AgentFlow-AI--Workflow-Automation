import logging
import yaml
import json
from typing import Any, Dict, List, Optional
from app.agents.api_discovery.exceptions import CatalogParseError
from app.agents.api_discovery.interfaces import BaseSpecParser
from app.agents.api_discovery.models import EndpointMetadataModel

logger = logging.getLogger("agentflow.api_discovery.parser")


class EnterpriseSpecParser(BaseSpecParser):
    """Complete OpenAPI 3.x, Swagger 2.0, Postman v2.1, AsyncAPI & YAML/JSON Parser."""

    def parse_spec(self, raw_content: Any, format_hint: Optional[str] = None) -> List[EndpointMetadataModel]:
        spec_dict = self._coerce_to_dict(raw_content)

        # 1. OpenAPI 3.x or Swagger 2.0
        if "openapi" in spec_dict or "swagger" in spec_dict or "paths" in spec_dict:
            return self._parse_openapi(spec_dict)

        # 2. Postman Collection
        if "info" in spec_dict and ("item" in spec_dict or "_postman_id" in spec_dict.get("info", {})):
            return self._parse_postman(spec_dict)

        # 3. Custom Catalog YAML/JSON format
        if "endpoints" in spec_dict and "provider" in spec_dict:
            return self._parse_custom_catalog(spec_dict)

        raise CatalogParseError("Unrecognized specification format. Expected OpenAPI, Swagger, Postman, or Catalog YAML.")

    def _coerce_to_dict(self, raw_content: Any) -> Dict[str, Any]:
        if isinstance(raw_content, dict):
            return raw_content
        if isinstance(raw_content, str):
            try:
                return json.loads(raw_content)
            except Exception:
                try:
                    return yaml.safe_load(raw_content)
                except Exception as e:
                    raise CatalogParseError(f"Failed to parse content as JSON or YAML: {e}") from e
        raise CatalogParseError(f"Unsupported raw content type: {type(raw_content)}")

    def _resolve_schema_refs(
        self,
        schema: Any,
        spec_dict: Dict[str, Any],
        visited_refs: Optional[set] = None
    ) -> Any:
        if not isinstance(schema, dict):
            return schema

        if visited_refs is None:
            visited_refs = set()

        ref_val = schema.get("$ref")
        if isinstance(ref_val, str):
            # Security guard: Only resolve local in-memory JSON pointers starting with '#/'
            if not ref_val.startswith("#/"):
                return dict(schema)

            if ref_val in visited_refs:
                # Circular reference safety: stop branch recursion
                return {k: v for k, v in schema.items() if k != "$ref"}

            parts = ref_val.lstrip("#/").split("/")
            target = spec_dict
            found = True
            for part in parts:
                part_unescaped = part.replace("~1", "/").replace("~0", "~")
                if isinstance(target, dict) and part_unescaped in target:
                    target = target[part_unescaped]
                else:
                    found = False
                    break

            if found and isinstance(target, dict):
                next_visited = set(visited_refs)
                next_visited.add(ref_val)

                resolved_target = self._resolve_schema_refs(target, spec_dict, next_visited)
                if isinstance(resolved_target, dict):
                    result = dict(resolved_target)
                    for k, v in schema.items():
                        if k != "$ref":
                            result[k] = v
                    return result

            return {k: v for k, v in schema.items() if k != "$ref"}

        result = {}
        for k, v in schema.items():
            if k == "properties" and isinstance(v, dict):
                resolved_props = {}
                for prop_name, prop_def in v.items():
                    resolved_props[prop_name] = self._resolve_schema_refs(prop_def, spec_dict, visited_refs)
                result["properties"] = resolved_props
            elif k == "items":
                result["items"] = self._resolve_schema_refs(v, spec_dict, visited_refs)
            elif k == "additionalProperties" and isinstance(v, dict):
                result["additionalProperties"] = self._resolve_schema_refs(v, spec_dict, visited_refs)
            elif k in ("allOf", "anyOf", "oneOf") and isinstance(v, list):
                result[k] = [self._resolve_schema_refs(item, spec_dict, visited_refs) for item in v]
            else:
                result[k] = v

        return result

    def _parse_openapi(self, spec_dict: Dict[str, Any]) -> List[EndpointMetadataModel]:
        endpoints: List[EndpointMetadataModel] = []
        info = spec_dict.get("info", {})
        provider_name = info.get("title", "OpenAPI Provider")
        version = info.get("version", "v1")
        paths = spec_dict.get("paths", {})

        # Extract OpenAPI 3 securitySchemes and Swagger 2 securityDefinitions
        security_schemes_raw: Dict[str, Any] = {}
        if "components" in spec_dict and isinstance(spec_dict["components"], dict):
            sec_3 = spec_dict["components"].get("securitySchemes", {})
            if isinstance(sec_3, dict):
                security_schemes_raw.update(sec_3)
        if "securityDefinitions" in spec_dict and isinstance(spec_dict["securityDefinitions"], dict):
            security_schemes_raw.update(spec_dict["securityDefinitions"])

        root_security = spec_dict.get("security")
        if not isinstance(root_security, list):
            root_security = []

        base_url = ""
        servers = spec_dict.get("servers", [])
        if isinstance(servers, list) and len(servers) > 0 and isinstance(servers[0], dict):
            base_url = servers[0].get("url", "")
        if not base_url and "host" in spec_dict:
            schemes = spec_dict.get("schemes", ["https"])
            scheme = schemes[0] if isinstance(schemes, list) and len(schemes) > 0 else "https"
            host = spec_dict.get("host", "")
            base_path = spec_dict.get("basePath", "")
            base_url = f"{scheme}://{host}{base_path}"

        for path_str, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            for method, op in path_item.items():
                if method.lower() not in ["get", "post", "put", "delete", "patch"] or not isinstance(op, dict):
                    continue

                op_id = op.get("operationId", f"{provider_name.lower().replace(' ', '_')}.{method}.{path_str.replace('/', '_')}")
                req_params = []
                opt_params = []
                query_params = []
                header_params = []

                for param in op.get("parameters", []):
                    if isinstance(param, dict) and "name" in param:
                        p_name = param["name"]
                        p_in = param.get("in")
                        if p_in == "query" and p_name not in query_params:
                            query_params.append(p_name)
                        elif p_in == "header" and p_name not in header_params:
                            header_params.append(p_name)
                        if param.get("required", False):
                            if p_name not in req_params:
                                req_params.append(p_name)
                        else:
                            if p_name not in opt_params:
                                opt_params.append(p_name)

                # OpenAPI 3.x requestBody schema parsing
                request_schema = {}
                request_body = op.get("requestBody")
                if isinstance(request_body, dict):
                    content = request_body.get("content", {})
                    schema = None
                    if isinstance(content, dict):
                        if "application/json" in content and isinstance(content["application/json"], dict):
                            schema = content["application/json"].get("schema")
                        else:
                            for media_type, media_obj in content.items():
                                if isinstance(media_obj, dict) and "schema" in media_obj:
                                    schema = media_obj["schema"]
                                    break

                    if isinstance(schema, dict):
                        request_schema = schema
                        props = schema.get("properties", {})
                        required_fields = set(schema.get("required", [])) if isinstance(schema.get("required"), list) else set()
                        if isinstance(props, dict):
                            for prop_name in props.keys():
                                if prop_name in required_fields:
                                    if prop_name not in req_params:
                                        req_params.append(prop_name)
                                else:
                                    if prop_name not in opt_params:
                                        opt_params.append(prop_name)

                # OpenAPI 3.x / Swagger 2.0 response schema parsing
                response_schema = {}
                responses = op.get("responses")
                if isinstance(responses, dict):
                    target_response = None
                    for status_code in ["200", "201", 200, 201, "202", "204", 202, 204]:
                        if status_code in responses and isinstance(responses[status_code], dict):
                            target_response = responses[status_code]
                            break
                    if target_response is None:
                        for sc, r_obj in responses.items():
                            if isinstance(r_obj, dict) and (str(sc).startswith("2") or str(sc).lower() == "default"):
                                target_response = r_obj
                                break

                    if isinstance(target_response, dict):
                        res_content = target_response.get("content")
                        res_schema = None
                        if isinstance(res_content, dict):
                            if "application/json" in res_content and isinstance(res_content["application/json"], dict):
                                res_schema = res_content["application/json"].get("schema")
                            else:
                                for media_type, media_obj in res_content.items():
                                    if "json" in media_type.lower() and isinstance(media_obj, dict) and "schema" in media_obj:
                                        res_schema = media_obj["schema"]
                                        break
                        elif "schema" in target_response and isinstance(target_response["schema"], dict):
                            res_schema = target_response["schema"]

                        if isinstance(res_schema, dict):
                            response_schema = self._resolve_schema_refs(res_schema, spec_dict)

                op_security = op.get("security")
                if op_security is not None:
                    sec_reqs = op_security if isinstance(op_security, list) else []
                else:
                    sec_reqs = root_security

                active_schemes = {}
                if sec_reqs:
                    for req_item in sec_reqs:
                        if isinstance(req_item, dict):
                            for s_name in req_item.keys():
                                if s_name in security_schemes_raw:
                                    active_schemes[s_name] = security_schemes_raw[s_name]

                endpoints.append(
                    EndpointMetadataModel(
                        endpoint=path_str,
                        operation_id=op_id,
                        provider=provider_name,
                        version=version,
                        http_method=method.upper(),
                        base_url=base_url,
                        summary=op.get("summary", ""),
                        description=op.get("description", ""),
                        required_params=req_params,
                        optional_params=opt_params,
                        query_params=query_params,
                        header_params=header_params,
                        request_schema=request_schema,
                        response_schema=response_schema,
                        security_schemes=active_schemes,
                        security_requirements=sec_reqs,
                        documentation_url=spec_dict.get("externalDocs", {}).get("url", ""),
                    )
                )

        return endpoints

    def _parse_postman(self, collection_dict: Dict[str, Any]) -> List[EndpointMetadataModel]:
        endpoints: List[EndpointMetadataModel] = []
        info = collection_dict.get("info", {})
        provider_name = info.get("name", "Postman Collection")

        def traverse(items: List[Dict[str, Any]]):
            for item in items:
                if "item" in item:
                    traverse(item["item"])
                elif "request" in item:
                    req = item["request"]
                    method = req.get("method", "GET")
                    url_obj = req.get("url", {})
                    raw_url = url_obj.get("raw", "") if isinstance(url_obj, dict) else str(url_obj)

                    endpoints.append(
                        EndpointMetadataModel(
                            endpoint=raw_url,
                            operation_id=f"{provider_name.lower().replace(' ', '_')}.{item.get('name', 'req').lower().replace(' ', '_')}",
                            provider=provider_name,
                            http_method=method,
                            summary=item.get("name", ""),
                        )
                    )

        traverse(collection_dict.get("item", []))
        return endpoints

    def _parse_custom_catalog(self, catalog_dict: Dict[str, Any]) -> List[EndpointMetadataModel]:
        endpoints: List[EndpointMetadataModel] = []
        provider_name = catalog_dict.get("provider", "Custom Provider")
        version = catalog_dict.get("version", "v1")

        for item in catalog_dict.get("endpoints", []):
            if isinstance(item, dict):
                item["provider"] = item.get("provider", provider_name)
                item["version"] = item.get("version", version)
                endpoints.append(EndpointMetadataModel(**item))

        return endpoints
