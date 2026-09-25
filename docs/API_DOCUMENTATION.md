# AgentFlow AI — REST & WebSocket API Documentation

Base Endpoint URL: `/api/v1`

---

## 📡 1. Runtime Engine V3 Endpoints

### `POST /api/v1/runtime/execute-preset`
Executes preset Workflow 1, 2, 3, or 4 end-to-end with durable checkpoints and telemetry.
- **Query Parameter**: `preset_id` (`wf_1` | `wf_2` | `wf_3` | `wf_4`)
- **Response**:
```json
{
  "execution_id": "exec_v3_9a2f1b",
  "workflow_id": "wf_1_gmail_drive_slack_sheets",
  "status": "COMPLETED",
  "duration_ms": 142.5,
  "node_records": {
    "step_1": { "status": "COMPLETED", "latency": 18.2, "output": { "attachment_id": "att_8819" } },
    "step_2": { "status": "COMPLETED", "latency": 24.5, "output": { "file_id": "file_drive_step_2" } }
  },
  "completed_nodes": ["step_1", "step_2", "step_3", "step_4"]
}
```

### `GET /api/v1/runtime/{execution_id}`
Returns live telemetry state, completed nodes, pending nodes, and variable scope.

### `POST /api/v1/runtime/{execution_id}/pause`
Pauses execution after in-flight node finishes.

### `POST /api/v1/runtime/{execution_id}/resume`
Resumes paused execution from durable checkpoint.

### `POST /api/v1/runtime/{execution_id}/cancel`
Cancels execution immediately and marks pending nodes as `CANCELLED`.

### `POST /api/v1/runtime/{execution_id}/rollback`
Triggers Saga rollback compensating all completed nodes in reverse topological order.

### `POST /api/v1/runtime/{execution_id}/replay`
Replays a failed run directly from Dead Letter Queue (DLQ).

---

## 🤖 2. Planner V3 Endpoints

### `POST /api/v1/planner/generate`
Generates a complete validated DAG workflow graph from natural language.
- **Payload**:
```json
{
  "prompt": "Sync new Gmail invoices to Google Drive and notify Slack channel #invoices"
}
```
- **Response**:
```json
{
  "workflow_id": "wf_planner_7718",
  "nodes": [ ... ],
  "edges": [ ... ],
  "confidence_score": 0.98,
  "steps_count": 3
}
```

---

## 📊 3. Analytics & Telemetry Endpoints

### `GET /api/v1/analytics/overview`
Returns high-level SaaS KPIs (total executions, SLA uptime %, average latency ms, retries).

### `GET /api/v1/analytics/connectors`
Returns call counts, latency breakdown, and SLA compliance across all 9 SaaS connectors.

### `GET /api/v1/analytics/insights`
Returns dynamic AI optimization suggestions based on active telemetry logs.

---

## 🔌 4. Invisible OAuth 2.0 Endpoints

### `GET /api/v1/oauth/accounts`
Returns all connected provider accounts with health status (`HEALTHY` | `EXPIRED` | `DEGRADED`).

### `POST /api/v1/oauth/connect/{provider}`
Initiates OAuth PKCE popup authorization flow.

### `POST /api/v1/oauth/refresh/{account_id}`
Forces instant token refresh using stored refresh tokens.

---

## 🔌 5. WebSockets

### `WS /ws/execution/{execution_id}`
Establishes bi-directional WebSocket connection streaming live node execution state transitions (`NODE_STARTED`, `NODE_COMPLETED`, `NODE_FAILED`, `WORKFLOW_COMPLETED`).
