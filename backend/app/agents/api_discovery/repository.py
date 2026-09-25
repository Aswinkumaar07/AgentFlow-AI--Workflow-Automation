import logging
from typing import Any, Dict, List, Optional
from app.agents.api_discovery.interfaces import BaseAPIDiscoveryRepository
from app.agents.api_discovery.models import APIEndpointModel

logger = logging.getLogger("agentflow.api_discovery.repository")


class APIDiscoveryRepository(BaseAPIDiscoveryRepository):
    """Enterprise Repository for storing, loading, and parsing API specifications across 10+ providers."""

    def __init__(self) -> None:
        self._endpoints: List[APIEndpointModel] = []
        self._initialize_default_catalog()

    def _initialize_default_catalog(self) -> None:
        """Pre-populates enterprise API endpoint catalog for Google, GitHub, Slack, Notion, Discord, Stripe, OpenAI, HubSpot, Dropbox, and Generic REST APIs."""
        default_specs = [
            # 1. Google (Gmail)
            APIEndpointModel(
                endpoint="https://gmail.googleapis.com/gmail/v1/users/me/messages",
                operation_id="gmail.messages.list",
                provider="Gmail",
                version="v1",
                http_method="GET",
                summary="List unread emails or search messages in inbox.",
                description="Fetches list of email messages matching query parameters from Gmail inbox.",
                auth_type="OAuth2",
                required_params=["q"],
                optional_params=["maxResults", "pageToken"],
                documentation_url="https://developers.google.com/gmail/api/reference/rest/v1/users.messages/list",
                rate_limits="250/sec",
            ),
            APIEndpointModel(
                endpoint="https://gmail.googleapis.com/gmail/v1/users/me/messages/{id}/attachments/{attachmentId}",
                operation_id="gmail.attachments.get",
                provider="Gmail",
                version="v1",
                http_method="GET",
                summary="Download email invoice or attachment file.",
                description="Downloads message attachment payload from specified Gmail message ID.",
                auth_type="OAuth2",
                required_params=["id", "attachmentId"],
                optional_params=[],
                documentation_url="https://developers.google.com/gmail/api/reference/rest/v1/users.messages.attachments/get",
                rate_limits="250/sec",
            ),
            # 2. Google Drive
            APIEndpointModel(
                endpoint="https://www.googleapis.com/upload/drive/v3/files",
                operation_id="drive.files.create",
                provider="Google Drive",
                version="v3",
                http_method="POST",
                summary="Upload invoice or document file to Google Drive.",
                description="Uploads file content and creates metadata entry in Google Drive storage.",
                auth_type="OAuth2",
                required_params=["uploadType"],
                optional_params=["folderId"],
                documentation_url="https://developers.google.com/drive/api/v3/reference/files/create",
                rate_limits="1000/min",
            ),
            # 3. Slack
            APIEndpointModel(
                endpoint="https://slack.com/api/chat.postMessage",
                operation_id="slack.chat.postMessage",
                provider="Slack",
                version="v1",
                http_method="POST",
                summary="Post alert notification or message to Slack channel.",
                description="Sends formatted message text or block payload to specified Slack channel.",
                auth_type="Bearer",
                required_params=["channel", "text"],
                optional_params=["blocks", "thread_ts"],
                documentation_url="https://api.slack.com/methods/chat.postMessage",
                rate_limits="1/sec",
            ),
            # 4. GitHub
            APIEndpointModel(
                endpoint="https://api.github.com/repos/{owner}/{repo}/issues",
                operation_id="github.issues.create",
                provider="GitHub",
                version="v3",
                http_method="POST",
                summary="Create issue ticket in GitHub repository.",
                description="Creates new issue in specified GitHub owner and repository.",
                auth_type="Bearer",
                required_params=["owner", "repo", "title"],
                optional_params=["body", "labels", "assignees"],
                documentation_url="https://docs.github.com/rest/issues/issues#create-an-issue",
                rate_limits="5000/hour",
            ),
            # 5. Notion
            APIEndpointModel(
                endpoint="https://api.notion.com/v1/pages",
                operation_id="notion.pages.create",
                provider="Notion",
                version="2022-06-28",
                http_method="POST",
                summary="Create database entry or wiki page in Notion workspace.",
                description="Creates page object inside specified parent database in Notion workspace.",
                auth_type="Bearer",
                required_params=["parent", "properties"],
                optional_params=["children", "icon", "cover"],
                documentation_url="https://developers.notion.com/reference/post-page",
                rate_limits="3/sec",
            ),
            # 6. Discord
            APIEndpointModel(
                endpoint="https://discord.com/api/v10/channels/{channel_id}/messages",
                operation_id="discord.messages.create",
                provider="Discord",
                version="v10",
                http_method="POST",
                summary="Send message or webhook alert to Discord channel.",
                description="Posts text message or embed object into Discord text channel.",
                auth_type="BotToken",
                required_params=["channel_id", "content"],
                optional_params=["embeds", "tts"],
                documentation_url="https://discord.com/developers/docs/resources/channel#create-message",
                rate_limits="5/sec",
            ),
            # 7. Stripe
            APIEndpointModel(
                endpoint="https://api.stripe.com/v1/charges",
                operation_id="stripe.charges.create",
                provider="Stripe",
                version="2023-10-16",
                http_method="POST",
                summary="Create payment charge or process invoice in Stripe.",
                description="Creates payment charge object in Stripe merchant account.",
                auth_type="Bearer",
                required_params=["amount", "currency", "source"],
                optional_params=["description", "customer"],
                documentation_url="https://stripe.com/docs/api/charges/create",
                rate_limits="100/sec",
            ),
            # 8. OpenAI
            APIEndpointModel(
                endpoint="https://api.openai.com/v1/chat/completions",
                operation_id="openai.chat.completions",
                provider="OpenAI",
                version="v1",
                http_method="POST",
                summary="Generate text response or chat completions using OpenAI models.",
                description="Calls OpenAI Chat Completion endpoint with messages array.",
                auth_type="Bearer",
                required_params=["model", "messages"],
                optional_params=["temperature", "max_tokens"],
                documentation_url="https://platform.openai.com/docs/api-reference/chat/create",
                rate_limits="3500/min",
            ),
            # 9. HubSpot
            APIEndpointModel(
                endpoint="https://api.hubapi.com/crm/v3/objects/contacts",
                operation_id="hubspot.contacts.create",
                provider="HubSpot",
                version="v3",
                http_method="POST",
                summary="Create CRM lead or contact in HubSpot.",
                description="Creates new contact object with email, name, and properties in HubSpot CRM.",
                auth_type="Bearer",
                required_params=["properties"],
                optional_params=[],
                documentation_url="https://developers.hubspot.com/docs/api/crm/contacts",
                rate_limits="150/10sec",
            ),
            # 10. Dropbox
            APIEndpointModel(
                endpoint="https://content.dropboxapi.com/2/files/upload",
                operation_id="dropbox.files.upload",
                provider="Dropbox",
                version="v2",
                http_method="POST",
                summary="Upload document file to Dropbox cloud storage.",
                description="Uploads binary content to specified file path in Dropbox folder.",
                auth_type="Bearer",
                required_params=["Dropbox-API-Arg"],
                optional_params=["autorename", "mute"],
                documentation_url="https://www.dropbox.com/developers/documentation/http/documentation#files-upload",
                rate_limits="120/min",
            ),
            # 11. Generic REST API
            APIEndpointModel(
                endpoint="https://api.example.com/v1/webhooks",
                operation_id="generic.webhook.send",
                provider="Generic REST API",
                version="v1",
                http_method="POST",
                summary="Dispatch HTTP POST JSON webhook payload to custom REST endpoint.",
                description="Sends HTTP POST request with arbitrary JSON body to configured URL.",
                auth_type="API_Key",
                required_params=["url", "payload"],
                optional_params=["headers"],
                documentation_url="https://swagger.io/docs/specification/about/",
                rate_limits="unlimited",
            ),
        ]
        self._endpoints.extend(default_specs)
        logger.info(f"Loaded {len(self._endpoints)} default enterprise API endpoints into repository catalog.")

    def get_all_endpoints(self) -> List[APIEndpointModel]:
        return list(self._endpoints)

    def load_from_openapi(self, spec_dict: Dict[str, Any]) -> List[APIEndpointModel]:
        """Parses an OpenAPI 3.0 or Swagger 2.0 specification dictionary."""
        new_endpoints: List[APIEndpointModel] = []
        paths = spec_dict.get("paths", {})
        info = spec_dict.get("info", {})
        provider_name = info.get("title", "OpenAPI Service")
        version = info.get("version", "v1")

        for path_str, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            for method, op_info in path_item.items():
                if method.lower() not in ["get", "post", "put", "delete", "patch"] or not isinstance(op_info, dict):
                    continue

                op_id = op_info.get("operationId", f"{provider_name.lower().replace(' ', '_')}.{method}.{path_str.replace('/', '_')}")
                summary = op_info.get("summary", "")
                description = op_info.get("description", summary)
                req_params = []
                opt_params = []

                for param in op_info.get("parameters", []):
                    if isinstance(param, dict) and "name" in param:
                        if param.get("required", False):
                            req_params.append(param["name"])
                        else:
                            opt_params.append(param["name"])

                endpoint_obj = APIEndpointModel(
                    endpoint=path_str,
                    operation_id=op_id,
                    provider=provider_name,
                    version=version,
                    http_method=method.upper(),
                    summary=summary,
                    description=description,
                    auth_type="OAuth2",
                    required_params=req_params,
                    optional_params=opt_params,
                    documentation_url="",
                    rate_limits="100/min",
                )
                new_endpoints.append(endpoint_obj)

        self._endpoints.extend(new_endpoints)
        logger.info(f"Parsed and added {len(new_endpoints)} endpoints from OpenAPI specification.")
        return new_endpoints

    def load_from_postman(self, collection_dict: Dict[str, Any]) -> List[APIEndpointModel]:
        """Parses a Postman v2.1 collection dictionary."""
        new_endpoints: List[APIEndpointModel] = []
        info = collection_dict.get("info", {})
        provider_name = info.get("name", "Postman Collection")

        def traverse_items(items: List[Dict[str, Any]]):
            for item in items:
                if "item" in item:
                    traverse_items(item["item"])
                elif "request" in item:
                    req = item["request"]
                    method = req.get("method", "GET")
                    url_obj = req.get("url", {})
                    raw_url = url_obj.get("raw", "") if isinstance(url_obj, dict) else str(url_obj)

                    new_endpoints.append(
                        APIEndpointModel(
                            endpoint=raw_url,
                            operation_id=f"{provider_name.lower().replace(' ', '_')}.{item.get('name', 'request').lower().replace(' ', '_')}",
                            provider=provider_name,
                            version="v1",
                            http_method=method,
                            summary=item.get("name", ""),
                            description="",
                            auth_type="Bearer",
                        )
                    )

        traverse_items(collection_dict.get("item", []))
        self._endpoints.extend(new_endpoints)
        logger.info(f"Parsed and added {len(new_endpoints)} endpoints from Postman collection.")
        return new_endpoints

    def load_from_custom_json(self, custom_dict: Dict[str, Any]) -> List[APIEndpointModel]:
        """Parses a custom JSON API specification catalog."""
        new_endpoints: List[APIEndpointModel] = []
        for item in custom_dict.get("endpoints", []):
            if isinstance(item, dict):
                model = APIEndpointModel(**item)
                new_endpoints.append(model)
        self._endpoints.extend(new_endpoints)
        logger.info(f"Parsed and added {len(new_endpoints)} endpoints from custom JSON catalog.")
        return new_endpoints
