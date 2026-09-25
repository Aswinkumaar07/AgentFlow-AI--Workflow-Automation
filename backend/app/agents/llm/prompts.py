from typing import Any, Dict, List


class PromptBuilder:
    """Enterprise prompt engineering builder for AgentFlow AI Multi-Agent tasks."""

    @staticmethod
    def planner_prompt(user_prompt: str) -> str:
        """Constructs prompt for the Planner Agent.

        Args:
            user_prompt: Natural language user workflow description.

        Returns:
            Formatted prompt string.
        """
        return f"""You are a Principal AI Systems Architect and Workflow Planning Agent.
Your role is to analyze a natural language user request and decompose it into a structured, step-by-step execution plan.

USER REQUEST:
"{user_prompt}"

INSTRUCTIONS:
1. Identify the core user goal.
2. Determine required external API services (e.g. GitHub, Slack, Gmail, Google Drive, Google Sheets, Notion).
3. Break down the execution flow into an ordered sequence of discrete, dependent tasks.
4. Estimate a confidence score between 0.0 and 1.0.

OUTPUT CONSTRAINTS:
- Output MUST be a single valid raw JSON object ONLY.
- DO NOT wrap response in markdown code fences like ```json or ```.
- DO NOT include introductory or concluding text explanations.

JSON SCHEMA REQUIREMENT:
{{
  "goal": "string",
  "services": ["string"],
  "tasks": [
    {{
      "task_id": "string",
      "action": "string",
      "service": "string",
      "description": "string",
      "dependencies": ["string"]
    }}
  ],
  "confidence_score": float
}}"""

    @staticmethod
    def discovery_prompt(goal: str, services: List[str]) -> str:
        """Constructs prompt for the API Discovery Agent.

        Args:
            goal: Parsed user goal.
            services: Target API services list.

        Returns:
            Formatted prompt string.
        """
        services_str = ", ".join(services) if services else "All Supported APIs"
        return f"""You are a Senior API Integration Architect and Discovery Agent.
Your role is to map planned workflow tasks to exact REST API endpoints, HTTP methods, and authorization requirements.

WORKFLOW GOAL:
"{goal}"

TARGET SERVICES:
{services_str}

INSTRUCTIONS:
1. Select appropriate REST API endpoints for each service.
2. Identify required HTTP method (GET, POST, PUT, DELETE).
3. Specify path parameter templates and required request payload fields.
4. Specify required OAuth2 or Bearer authorization scopes.

OUTPUT CONSTRAINTS:
- Output MUST be a single valid raw JSON object ONLY.
- DO NOT wrap response in markdown code fences like ```json or ```.
- DO NOT include introductory or concluding text explanations.

JSON SCHEMA REQUIREMENT:
{{
  "api_candidates": [
    {{
      "task_id": "string",
      "provider": "string",
      "endpoint": "string",
      "http_method": "string",
      "auth_type": "string",
      "required_params": ["string"]
    }}
  ]
}}"""

    @staticmethod
    def workflow_prompt(plan: Dict[str, Any], docs: List[Dict[str, Any]]) -> str:
        """Constructs prompt for the Workflow Generator Agent.

        Args:
            plan: Structured execution plan dictionary.
            docs: Retrieved API documentation context list.

        Returns:
            Formatted prompt string.
        """
        return f"""You are a Senior Compiler Engineer for AI Directed Acyclic Graph (DAG) Workflows.
Your role is to synthesize execution plans and API documentation into a fully executable machine-readable DAG JSON structure.

EXECUTION PLAN:
{plan}

DOCUMENTATION CONTEXT:
{docs}

INSTRUCTIONS:
1. Construct a valid DAG JSON specification containing trigger rules, workflow nodes, and data flow edges.
2. Ensure variable references across nodes use mustache template syntax (e.g. "{{{{node_1.data.id}}}}").
3. Include metadata tracking generation version and step counts.

OUTPUT CONSTRAINTS:
- Output MUST be a single valid raw JSON object ONLY.
- DO NOT wrap response in markdown code fences like ```json or ```.
- DO NOT include introductory or concluding text explanations.

JSON SCHEMA REQUIREMENT:
{{
  "title": "string",
  "version": "string",
  "trigger": {{
    "type": "string",
    "event": "string"
  }},
  "nodes": [
    {{
      "id": "string",
      "type": "string",
      "provider": "string",
      "action": "string",
      "params": {{}}
    }}
  ],
  "edges": [
    {{
      "source": "string",
      "target": "string"
    }}
  ],
  "metadata": {{}}
}}"""

    @staticmethod
    def validation_prompt(workflow: Dict[str, Any]) -> str:
        """Constructs prompt for the Validation Agent.

        Args:
            workflow: Candidate workflow DAG JSON.

        Returns:
            Formatted prompt string.
        """
        return f"""You are a Senior Static Analysis and DAG Validation Engineer.
Your role is to audit a candidate DAG workflow JSON for circular dependencies, invalid variable mappings, missing input parameters, or broken node links.

CANDIDATE WORKFLOW DAG:
{workflow}

INSTRUCTIONS:
1. Verify graph topology is strictly acyclic (no infinite execution loops).
2. Verify all edge sources and targets refer to valid existing node IDs.
3. Validate node parameter schema references.
4. Output a boolean result and list of detected errors or warnings.

OUTPUT CONSTRAINTS:
- Output MUST be a single valid raw JSON object ONLY.
- DO NOT wrap response in markdown code fences like ```json or ```.
- DO NOT include introductory or concluding text explanations.

JSON SCHEMA REQUIREMENT:
{{
  "is_valid": boolean,
  "errors": ["string"],
  "warnings": ["string"],
  "checked_rules": ["string"]
}}"""

    @staticmethod
    def repair_prompt(workflow: Dict[str, Any], errors: List[str]) -> str:
        """Constructs prompt for the Self-Healing Repair Agent.

        Args:
            workflow: Broken candidate workflow DAG JSON.
            errors: Validation error log messages.

        Returns:
            Formatted prompt string.
        """
        errors_str = "\n".join(f"- {err}" for err in errors) if errors else "- General execution failure"
        return f"""You are a Staff Self-Healing Integration Engineer.
Your role is to analyze a broken DAG workflow JSON along with validation error logs, determine the root cause, and produce an automatically patched, fully corrected DAG workflow JSON.

BROKEN WORKFLOW DAG:
{workflow}

VALIDATION ERROR LOGS:
{errors_str}

INSTRUCTIONS:
1. Inspect the root cause of every reported validation error or HTTP integration failure (401, 400, 404, 429, Timeout).
2. Repair invalid endpoint paths, missing parameter substitutions, or broken edge relationships.
3. Output the complete repaired workflow DAG object and a summary report of applied patches.

OUTPUT CONSTRAINTS:
- Output MUST be a single valid raw JSON object ONLY.
- DO NOT wrap response in markdown code fences like ```json or ```.
- DO NOT include introductory or concluding text explanations.

JSON SCHEMA REQUIREMENT:
{{
  "repaired_workflow_json": {{}},
  "repair_report": {{
    "applied_fixes": ["string"],
    "fixed_error_codes": ["string"]
  }}
}}"""
