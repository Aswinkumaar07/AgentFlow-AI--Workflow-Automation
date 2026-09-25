import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator


class ConnectorCredentialModel(BaseModel):
    """Encapsulated Tenant Credential Object supporting all authentication schemes."""

    tenant_id: str = Field(default="default", description="Multi-tenant identifier.")
    provider: str = Field(..., description="Provider name (e.g. Gmail, Slack, Stripe).")
    auth_type: str = Field(default="OAuth2", description="Authentication scheme (OAuth2, PKCE, API_Key, Bearer, JWT, Basic).")
    access_token: Optional[str] = Field(default=None, description="OAuth2 or Bearer access token.")
    refresh_token: Optional[str] = Field(default=None, description="OAuth2 refresh token.")
    api_key: Optional[str] = Field(default=None, description="API Key string.")
    client_id: Optional[str] = Field(default=None, description="OAuth2 Client ID.")
    client_secret: Optional[str] = Field(default=None, description="OAuth2 Client Secret.")
    token_expires_at: Optional[float] = Field(default=None, description="Token expiration epoch timestamp.")
    scopes: List[str] = Field(default_factory=list, description="Authorized OAuth scopes.")
    account_label: Optional[str] = Field(default=None, description="Account email or display label.")
    additional_headers: Dict[str, str] = Field(default_factory=dict, description="Additional HTTP headers.")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def is_token_expired(self) -> bool:
        if not self.token_expires_at:
            return False
        return time.time() >= (self.token_expires_at - 60.0)  # 60s safety buffer


class ConnectorRequestModel(BaseModel):
    """Payload model for invoking a connector operation."""

    operation_id: str = Field(..., description="Target operation ID (e.g., gmail.messages.list).")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation request parameters.")
    body: Optional[Any] = Field(default=None, description="Request JSON payload body.")
    tenant_id: str = Field(default="default", description="Invoking tenant ID.")
    timeout_seconds: float = Field(default=30.0, description="Execution timeout limit.")
    retry_attempts: int = Field(default=3, description="Maximum execution retries.")


class ConnectorResponseModel(BaseModel):
    """Standardized response container from connector operation execution."""

    success: bool = Field(..., description="Execution status boolean.")
    operation_id: str = Field(..., description="Executed operation ID.")
    status_code: int = Field(default=200, description="HTTP or status code.")
    data: Dict[str, Any] = Field(default_factory=dict, description="Response payload data.")
    error_message: Optional[str] = Field(default=None, description="Error message if execution failed.")
    latency_ms: float = Field(default=0.0, description="Execution latency in milliseconds.")
    retries_used: int = Field(default=0, description="Number of retries attempted.")


class ParameterSchemaModel(BaseModel):
    """Schema definition for an individual operation parameter."""
    name: str = Field(..., description="Parameter name (e.g. to, subject, body).")
    display_name: str = Field(default="", description="Human readable field name.")
    type: str = Field(default="string", description="Parameter type: string, text, number, boolean, select, json, array, kv_pairs.")
    required: bool = Field(default=False, description="Whether parameter is required.")
    description: Optional[str] = Field(default=None, description="Field help text or description.")
    default_value: Optional[Any] = Field(default=None, description="Default parameter value.")
    options: List[Dict[str, str]] = Field(default_factory=list, description="Dropdown options for select type.")
    validation_rule: Optional[str] = Field(default=None, description="Validation rule or regex constraint.")

    @model_validator(mode="after")
    def populate_display_name(self):
        if not self.display_name:
            self.display_name = self.name.replace("_", " ").title()
        return self


class OperationSchemaModel(BaseModel):
    """Schema definition for a single operation exposed by a connector."""
    id: str = Field(..., description="Operation ID (e.g. gmail.messages.send).")
    display_name: str = Field(default="", description="Human readable operation title.")
    description: str = Field(default="", description="Operation description.")
    required_parameters: List[ParameterSchemaModel] = Field(default_factory=list, description="List of required parameters.")
    optional_parameters: List[ParameterSchemaModel] = Field(default_factory=list, description="List of optional parameters.")
    default_values: Dict[str, Any] = Field(default_factory=dict, description="Default values map.")

    @model_validator(mode="after")
    def populate_display_name(self):
        if not self.display_name:
            self.display_name = self.id.split(".")[-1].replace("_", " ").title()
        return self


class ConnectorMetadataModel(BaseModel):
    """Dynamic Connector metadata definition compliant with enterprise registry specs."""
    provider: str = Field(..., description="Provider identifier (e.g. gmail, drive, slack).")
    display_name: str = Field(default="", description="Display title.")
    icon: str = Field(default="plug", description="Icon identifier or name.")
    auth_type: str = Field(default="OAuth2", description="Authentication type: OAuth2, APIKey, Webhook, None.")
    supported_operations: List[str] = Field(default_factory=list, description="List of supported operation IDs.")
    operation_schemas: Dict[str, OperationSchemaModel] = Field(default_factory=dict, description="Detailed schema for each operation.")
    categories: List[str] = Field(default_factory=list, description="Connector category tags.")
    version: str = Field(default="1.0.0", description="Connector version string.")
    documentation_url: str = Field(default="", description="Documentation URL.")

    @model_validator(mode="after")
    def populate_display_name(self):
        if not self.display_name:
            self.display_name = self.provider
        return self
