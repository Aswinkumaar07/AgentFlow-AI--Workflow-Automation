from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict

class APIEndpointSpec(BaseModel):
    name: str
    method: str
    path: str
    description: str
    required_scopes: List[str]
    parameters: Dict[str, Any]

class APIProviderSpec(BaseModel):
    name: str
    display_name: str
    auth_type: str # oauth2, bearer, webhook, api_key
    base_url: str
    docs_url: str
    endpoints: List[APIEndpointSpec]

    model_config = ConfigDict(from_attributes=True)

class ProviderRegistry:
    """
    Extensible registry for API Providers & Specifications.
    Supports MVP: Gmail, Google Drive, Slack, GitHub, Google Sheets, Notion.
    """

    def __init__(self):
        self._providers: Dict[str, APIProviderSpec] = {}
        self._register_default_mvp_providers()

    def register_provider(self, provider: APIProviderSpec) -> None:
        self._providers[provider.name.lower()] = provider

    def get_provider(self, name: str) -> Optional[APIProviderSpec]:
        return self._providers.get(name.lower())

    def list_providers(self) -> List[str]:
        return list(self._providers.keys())

    def search_endpoints(self, query: str) -> List[Dict[str, Any]]:
        results = []
        q = query.lower()
        for p_name, provider in self._providers.items():
            if p_name in q or provider.display_name.lower() in q:
                for ep in provider.endpoints:
                    results.append({
                        "provider": p_name,
                        "display_name": provider.display_name,
                        "endpoint": f"{ep.method} {ep.path}",
                        "name": ep.name,
                        "description": ep.description,
                        "auth_type": provider.auth_type,
                    })
        return results

    def _register_default_mvp_providers(self) -> None:
        # 1. GitHub Provider
        self.register_provider(APIProviderSpec(
            name="github",
            display_name="GitHub REST API",
            auth_type="bearer",
            base_url="https://api.github.com",
            docs_url="https://docs.github.com/en/rest",
            endpoints=[
                APIEndpointSpec(name="list_prs", method="GET", path="/repos/{owner}/{repo}/pulls", description="List pull requests", required_scopes=["repo"], parameters={"owner": "string", "repo": "string"}),
                APIEndpointSpec(name="create_issue", method="POST", path="/repos/{owner}/{repo}/issues", description="Create an issue", required_scopes=["repo"], parameters={"owner": "string", "repo": "string", "title": "string", "body": "string"}),
            ]
        ))

        # 2. Slack Provider
        self.register_provider(APIProviderSpec(
            name="slack",
            display_name="Slack Web API",
            auth_type="bearer",
            base_url="https://slack.com/api",
            docs_url="https://api.slack.com/methods",
            endpoints=[
                APIEndpointSpec(name="post_message", method="POST", path="/chat.postMessage", description="Post a message to a channel", required_scopes=["chat:write"], parameters={"channel": "string", "text": "string"}),
            ]
        ))

        # 3. Gmail Provider
        self.register_provider(APIProviderSpec(
            name="gmail",
            display_name="Google Gmail API",
            auth_type="oauth2",
            base_url="https://gmail.googleapis.com/gmail/v1",
            docs_url="https://developers.google.com/gmail/api",
            endpoints=[
                APIEndpointSpec(name="send_email", method="POST", path="/users/me/messages/send", description="Send an email message", required_scopes=["https://mail.google.com/"], parameters={"raw": "string"}),
            ]
        ))

        # 4. Google Drive Provider
        self.register_provider(APIProviderSpec(
            name="drive",
            display_name="Google Drive API",
            auth_type="oauth2",
            base_url="https://www.googleapis.com/drive/v3",
            docs_url="https://developers.google.com/drive/api",
            endpoints=[
                APIEndpointSpec(name="list_files", method="GET", path="/files", description="List user files", required_scopes=["https://www.googleapis.com/auth/drive.readonly"], parameters={"q": "string"}),
            ]
        ))

        # 5. Google Sheets Provider
        self.register_provider(APIProviderSpec(
            name="sheets",
            display_name="Google Sheets API",
            auth_type="oauth2",
            base_url="https://sheets.googleapis.com/v4/spreadsheets",
            docs_url="https://developers.google.com/sheets/api",
            endpoints=[
                APIEndpointSpec(name="append_row", method="POST", path="/{spreadsheetId}/values/{range}:append", description="Append rows to spreadsheet", required_scopes=["https://www.googleapis.com/auth/spreadsheets"], parameters={"spreadsheetId": "string", "range": "string"}),
            ]
        ))

        # 6. Notion Provider
        self.register_provider(APIProviderSpec(
            name="notion",
            display_name="Notion API",
            auth_type="bearer",
            base_url="https://api.notion.com/v1",
            docs_url="https://developers.notion.com/",
            endpoints=[
                APIEndpointSpec(name="create_page", method="POST", path="/pages", description="Create a database page", required_scopes=["read_write"], parameters={"parent": "dict", "properties": "dict"}),
            ]
        ))

provider_registry = ProviderRegistry()
