import time
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.runtime.variable_store import VariableStore


class ExecutionContext(BaseModel):
    """Runtime execution context housing workflow spec, variables, previous step outputs, and secrets."""

    execution_id: str
    workflow_id: str
    tenant_id: str = "usr_1"
    context_data: Dict[str, Any] = Field(default_factory=dict)
    previous_outputs: Dict[str, Any] = Field(default_factory=dict)
    secrets: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def build_node_input_payload(
        self, node_id: str, node_params: Dict[str, Any], workflow_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Constructs standardized node input payload and interpolates template parameters."""
        var_store = VariableStore(self.context_data)
        user_email = "aswinkumaar07@gmail.com"
        if isinstance(self.context_data, dict) and self.context_data.get("user_email"):
            user_email = self.context_data.get("user_email")

        scope = {
            "context": self.context_data,
            "previous_outputs": self.previous_outputs,
            "secrets": self.secrets,
            "metadata": self.metadata,
            "user": {"email": user_email, "name": "Aswin"},
        }
        # Add shortcuts like step_1 -> previous_outputs["step_1"]
        for step_id, out_val in self.previous_outputs.items():
            scope[step_id] = out_val

        # Expose top-level context variables (e.g. item, index) in scope for loop resolution
        if isinstance(self.context_data, dict):
            for k, v in self.context_data.items():
                if k not in scope:
                    scope[k] = v

        interpolated_params = var_store.interpolate(node_params, scope)

        # Log variable resolution for AI-16 compliance
        if isinstance(node_params, dict) and isinstance(interpolated_params, dict):
            for k, orig in node_params.items():
                res_val = interpolated_params.get(k)
                if isinstance(orig, str) and "{{" in orig and res_val != orig:
                    import json, logging
                    logger = logging.getLogger("agentflow.runtime.context")
                    logger.info(
                        f"[AI-16][VARIABLE_RESOLUTION] {json.dumps({'execution_id': self.execution_id, 'workflow_id': self.workflow_id, 'node_id': node_id, 'expression': orig, 'resolved_value': str(res_val)})}"
                    )

        return {
            "workflow": workflow_spec,
            "context": self.context_data,
            "variables": self.context_data,
            "previous_outputs": self.previous_outputs,
            "parameters": interpolated_params,
            "secrets": self.secrets,
            "metadata": {
                **self.metadata,
                "node_id": node_id,
                "execution_id": self.execution_id,
                "interpolated_params": interpolated_params,
            },
        }

    def record_step_output(self, step_id: str, output: Any) -> None:
        self.previous_outputs[step_id] = output
        self.context_data[step_id] = output
