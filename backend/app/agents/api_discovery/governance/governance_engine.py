import logging
from typing import Dict, List, Optional
from app.agents.api_discovery.models import EndpointMetadataModel

logger = logging.getLogger("agentflow.api_discovery.governance")


class APIGovernanceEngine:
    """Enterprise API Governance & OAuth Intelligence Engine."""

    def __init__(self) -> None:
        self._deprecated_endpoints: Dict[str, str] = {}  # op_id -> replacement_op_id

    def mark_deprecated(self, operation_id: str, replacement_operation_id: Optional[str] = None) -> None:
        self._deprecated_endpoints[operation_id] = replacement_operation_id or ""
        logger.warning(f"Governance Engine marked operation '{operation_id}' as DEPRECATED.")

    def audit_endpoint(self, endpoint: EndpointMetadataModel) -> Dict[str, str]:
        """Audits endpoint for deprecation status, OAuth completeness, and security recommendations."""
        audit_res = {"status": "ACTIVE"}

        if endpoint.operation_id in self._deprecated_endpoints or endpoint.deprecation_status:
            replacement = self._deprecated_endpoints.get(endpoint.operation_id, "No direct replacement")
            audit_res["status"] = "DEPRECATED"
            audit_res["replacement"] = replacement
            logger.warning(f"Endpoint '{endpoint.operation_id}' is DEPRECATED. Replacement: {replacement}")

        if endpoint.auth_type == "OAuth2" and not endpoint.oauth_scopes:
            audit_res["security_warning"] = "OAuth2 authentication type specified but required oauth_scopes list is empty."

        return audit_res


governance_engine = APIGovernanceEngine()
