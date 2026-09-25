# AgentFlow AI — Troubleshooting & Diagnostics Guide

This document provides resolutions for common operational issues, error codes, and troubleshooting workflows.

---

## 🔍 Common Issues & Resolutions

### 1. OAuth Token Expiry / Authentication Failure
- **Symptom**: Node fails with `401 Unauthorized` or status `DEGRADED`.
- **Diagnosis**: Refresh token expired or revoked at provider level.
- **Fix**:
  1. Go to **Settings** → **OAuth 2.0 Accounts**.
  2. Click **Refresh Token** or **Reconnect**.
  3. The 60-second health monitor will automatically restore status to `HEALTHY`.

### 2. Execution Stuck in `PAUSED` or `WAITING` State
- **Symptom**: Workflow progress halts at a node.
- **Diagnosis**: Node is a Human Approval node or Wait node.
- **Fix**:
  1. Click **Approve** in the Execution Studio toolbar or call `POST /api/v1/runtime/{id}/approve?node_id=step_id`.
  2. Execution will resume automatically from the durable checkpoint.

### 3. Replaying Failed Executions from DLQ
- **Symptom**: Execution status marked `FAILED`.
- **Diagnosis**: Transient network failure or rate limit hit.
- **Fix**:
  1. Open **Error Replay & DLQ** from the sidebar.
  2. Inspect the expandable stack trace.
  3. Click **Replay Checkpoint** to re-execute from the exact failed node without re-running prior steps.

### 4. WebSocket Disconnection in Execution Studio
- **Symptom**: Live canvas glow pauses or status updates lag.
- **Diagnosis**: Temporary network drop or server restart.
- **Fix**: The `useExecutionWebSocket` hook features automatic exponential backoff reconnection. The status badge will show `Reconnected` automatically within 3 seconds.

---

## 🛠️ Diagnostics Commands

Backend Health Check:
```bash
curl -X GET http://localhost:8000/api/v1/health
```

Preset Execution Verification:
```bash
curl -X POST "http://localhost:8000/api/v1/runtime/execute-preset?preset_id=wf_1"
```
