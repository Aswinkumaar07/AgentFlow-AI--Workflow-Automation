import logging
from typing import Any, Dict, Optional
from app.connectors.cache.connection_pool import connection_pool

logger = logging.getLogger("agentflow.connectors.clients.graphql")


class GraphQLClient:
    """Native Client for executing GraphQL Queries and Mutations over ConnectionPool."""

    async def execute_query(
        self, endpoint_url: str, query: str, variables: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        req_headers = dict(headers or {})
        req_headers["Content-Type"] = "application/json"

        payload = {"query": query, "variables": variables or {}}
        logger.info(f"Dispatching GraphQL query to [{endpoint_url}]")

        return await connection_pool.request("POST", endpoint_url, headers=req_headers, json_data=payload)


graphql_client = GraphQLClient()
