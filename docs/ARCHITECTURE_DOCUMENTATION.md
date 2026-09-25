# AgentFlow AI — Architecture Documentation

This document describes the high-level architecture, design patterns, data flow, and resilience mechanisms of AgentFlow AI.

---

## 🏗️ 1. High-Level Architecture Diagram

```
                             ┌────────────────────────────────────────┐
                             │          React 19 Frontend             │
                             │  (Vite 8, Tailwind v4, ReactFlow v12)   │
                             └───────────────────┬────────────────────┘
                                                 │ REST / WebSockets
                                                 ▼
                             ┌────────────────────────────────────────┐
                             │       FastAPI Gateway & Middleware     │
                             │   (Security Headers, CORS, Logging)    │
                             └───────┬────────────────────────┬───────┘
                                     │                        │
                    ┌────────────────┴───────────┐  ┌─────────┴────────────────┐
                    │ Multi-Agent Planner V3     │  │ Runtime Engine V3         │
                    │  • Discovery Agent         │  │  • Topological Executor   │
                    │  • Ranker Agent            │  │  • Event Bus Streaming    │
                    │  • Parameter AI Agent      │  │  • Durable Checkpointer   │
                    │  • Graph Validator         │  │  • Saga Rollback Manager  │
                    └────────────────────────────┘  └─────────┬────────────────┘
                                                              │
                                            ┌─────────────────┴───────────────┐
                                            │ Enterprise Connector Manager    │
                                            │  • Registry & ALIAS_MAP         │
                                            │  • Secret Vault (AES-256 GCM)   │
                                            │  • Invisible OAuth Token Engine │
                                            └─────────────────┬───────────────┘
                                                              │
                                       ┌──────────────────────┴──────────────────────┐
                                       │ SaaS Provider Adapters (Gmail, Drive, etc.) │
                                       └─────────────────────────────────────────────┘
```

---

## 🧠 2. Core Architecture Subsystems

### A. Multi-Agent Planner V3
- **Discovery Agent**: Scans natural language prompts to detect required SaaS tools and operations.
- **Ranker Agent**: Scores candidate connectors based on historical SLA, reliability, and user context.
- **Parameter AI Agent**: Synthesizes template parameter expressions (`{{step_1.attachment_id}}`).
- **Graph Validator**: Enforces DAG acyclicity, validates input/output schemas, and verifies account bindings.

### B. Durable Runtime Engine V3
- **Topological DAG Scheduler**: Executes independent node branches concurrently while preserving dependencies.
- **Variable Store & Template Interpolator**: Resolves JSON path expressions (`{{step_1.output.id}}`, `{item.email}`) dynamically across step contexts.
- **Event Bus**: Broadcasts real-time execution events to WebSocket clients.
- **Durable Checkpointer**: Writes step snapshots to database or memory after every node execution.
- **Dead Letter Queue (DLQ)**: Pushes failed runs with stack traces and enables one-click replay.
- **Saga Rollback Manager**: Compensates completed nodes in reverse order if downstream failure occurs.

### C. Invisible OAuth 2.0 Engine
- **Token Refresh Manager**: Checks token expiration before every API call and silently refreshes credentials.
- **Background Health Monitor**: Polls token validity every 60 seconds and updates UI status badges.
- **Popup Polling Engine**: Automatically binds newly connected accounts to active builder nodes without manual configuration.

### D. Analytics & Telemetry Engine
- **Stateful Telemetry Tracker**: Accumulates live metrics across 9 SaaS providers.
- **AI Insight Synthesizer**: Recommends optimizations (e.g. rate limit batching, latency caching) based on real log data.
