from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class EndpointMetadataModel(BaseModel):
    """Enterprise metadata model representing an API Endpoint operation."""

    endpoint: str = Field(..., description="API endpoint path or URL template.")
    operation_id: str = Field(..., description="Unique operation identifier.")
    provider: str = Field(..., description="Target API Provider (e.g., Gmail, Drive, Slack, GitHub, Stripe).")
    version: str = Field(default="v1", description="API version tag.")
    http_method: str = Field(default="GET", description="HTTP Method (GET, POST, PUT, DELETE, PATCH).")
    summary: str = Field(default="", description="Short functional summary.")
    description: str = Field(default="", description="Detailed operation description.")

    # Auth & Security
    auth_type: str = Field(default="OAuth2", description="Authentication scheme (OAuth2, Bearer, API_Key, BotToken).")
    oauth_scopes: List[str] = Field(default_factory=list, description="Required OAuth2 scopes.")
    permissions: List[str] = Field(default_factory=list, description="Required role permissions.")

    # Parameters & Schemas
    required_params: List[str] = Field(default_factory=list, description="Required parameters.")
    optional_params: List[str] = Field(default_factory=list, description="Optional parameters.")
    examples: Dict[str, Any] = Field(default_factory=dict, description="Request/Response examples.")
    request_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for request body.")
    response_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for response body.")
    pagination_strategy: str = Field(default="cursor", description="Pagination strategy (cursor, offset, page, none).")

    # Resilience & Telemetry
    rate_limits: str = Field(default="100/min", description="Rate limit specification.")
    retry_policy: str = Field(default="exponential_backoff", description="Retry policy recommendation.")
    timeout_seconds: float = Field(default=30.0, description="Recommended request timeout in seconds.")
    latency_ms: float = Field(default=120.0, description="Average response latency in milliseconds.")
    availability: float = Field(default=99.9, description="Endpoint SLA availability percentage.")

    # Ranking & Analytics
    popularity_score: float = Field(default=0.85, ge=0.0, le=1.0, description="Global API usage popularity score.")
    health_score: float = Field(default=0.98, ge=0.0, le=1.0, description="Real-time endpoint health score.")
    documentation_url: str = Field(default="", description="Official documentation URL.")
    deprecation_status: bool = Field(default=False, description="Flag indicating if endpoint is deprecated.")
    estimated_cost: float = Field(default=0.001, description="Estimated USD cost per 1000 requests.")
    estimated_tokens: int = Field(default=250, description="Estimated token payload size.")
    confidence_score: float = Field(default=0.85, ge=0.0, le=1.0, description="Hybrid search confidence score.")

    # Vector Embedding
    embedding: Optional[List[float]] = Field(default=None, description="Pre-computed vector embedding.")

    model_config = ConfigDict(arbitrary_types_allowed=True)


# Backward Compatibility Alias
APIEndpointModel = EndpointMetadataModel


class APICapabilityNode(BaseModel):
    """Node in Capability Graph representing an entity or capability (e.g. Gmail.Invoice)."""

    node_id: str = Field(..., description="Unique capability node identifier.")
    provider: str = Field(..., description="Provider name.")
    entity_type: str = Field(..., description="Entity type (e.g. Email, Document, Invoice, Notification).")
    input_types: List[str] = Field(default_factory=list, description="Accepted input data types.")
    output_types: List[str] = Field(default_factory=list, description="Produced output data types.")
    operations: List[str] = Field(default_factory=list, description="Associated operation IDs.")


class APIRecommendationModel(BaseModel):
    """Recommendation object for alternative, cheaper, or faster APIs."""

    target_operation_id: str = Field(..., description="Original operation identifier.")
    recommended_operation_id: str = Field(..., description="Recommended alternative operation.")
    recommendation_type: str = Field(..., description="Type: 'cheaper', 'faster', 'more_reliable', 'alternative'.")
    savings_percentage: float = Field(default=0.0, description="Estimated cost or latency savings %.")
    rationale: str = Field(default="", description="Human-readable recommendation rationale.")


class APIQueryFilter(BaseModel):
    """Query filter parameters."""

    query: str
    target_providers: Optional[List[str]] = None
    min_confidence: float = 0.50
    max_latency_ms: Optional[float] = None
    max_cost: Optional[float] = None
    required_auth_type: Optional[str] = None
