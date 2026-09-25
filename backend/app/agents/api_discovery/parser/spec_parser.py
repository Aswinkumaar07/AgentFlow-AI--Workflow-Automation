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

    def _parse_openapi(self, spec_dict: Dict[str, Any]) -> List[EndpointMetadataModel]:
        endpoints: List[EndpointMetadataModel] = []
        info = spec_dict.get("info", {})
        provider_name = info.get("title", "OpenAPI Provider")
        version = info.get("version", "v1")
        paths = spec_dict.get("paths", {})

        for path_str, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            for method, op in path_item.items():
                if method.lower() not in ["get", "post", "put", "delete", "patch"] or not isinstance(op, dict):
                    continue

                op_id = op.get("operationId", f"{provider_name.lower().replace(' ', '_')}.{method}.{path_str.replace('/', '_')}")
                req_params = []
                opt_params = []

                for param in op.get("parameters", []):
                    if isinstance(param, dict) and "name" in param:
                        if param.get("required", False):
                            req_params.append(param["name"])
                        else:
                            opt_params.append(param["name"])

                endpoints.append(
                    EndpointMetadataModel(
                        endpoint=path_str,
                        operation_id=op_id,
                        provider=provider_name,
                        version=version,
                        http_method=method.upper(),
                        summary=op.get("summary", ""),
                        description=op.get("description", ""),
                        required_params=req_params,
                        optional_params=opt_params,
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
