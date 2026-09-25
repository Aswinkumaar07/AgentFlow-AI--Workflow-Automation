import logging
from typing import Any, Dict, Optional
from app.connectors.cache.connection_pool import connection_pool

logger = logging.getLogger("agentflow.connectors.clients.mcp")


class MCPClient:
    """Native Client for executing Model Context Protocol (MCP) tool calls."""

    async def call_tool(
        self, mcp_server_url: str, tool_name: str, arguments: Dict[str, Any], headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        req_headers = dict(headers or {})
        req_headers["Content-Type"] = "application/json"

        payload = {
            "jsonrpc": "2.0",
            "id": "mcp_req_1",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        logger.info(f"Dispatching MCP Tool Call [{tool_name}] to [{mcp_server_url}]")
        return await connection_pool.request("POST", mcp_server_url, headers=req_headers, json_data=payload)


mcp_client = MCPClient()
