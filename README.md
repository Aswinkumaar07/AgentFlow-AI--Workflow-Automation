# AgentFlow AI — Enterprise Intelligent API Workflow Automation

> **Production SaaS Platform** · Natural Language Multi-Agent AI · Autonomous API Workflow Engine

[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178C6?logo=typescript)](https://www.typescriptlang.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Vite](https://img.shields.io/badge/Vite-8.1-646CFF?logo=vite)](https://vite.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-v4-38BDF8?logo=tailwindcss)](https://tailwindcss.com)

---

## 🚀 Overview

AgentFlow AI is a high-performance enterprise SaaS platform for intelligent API workflow automation. Users describe complex automation logic in plain English, and multi-agent AI systems plan, validate, bind credentials, and execute durable DAG workflows.

### 🌟 Key Highlights
- **Multi-Agent Planner V3**: Prompt → Connector Discovery → Ranker → Parameter AI → Validator → Execution Graph.
- **Runtime Engine V3**: Topological execution, event bus, human approval wait states, durable node checkpoints, circuit breaker fault tolerance, and Dead Letter Queue (DLQ) replay.
- **Production Connectors**: Native adapters for Google Gmail, Google Drive, Google Sheets, Slack Web API, GitHub API v3, Stripe Connect, Notion API, and Generic REST APIs with OAuth 2.0 automatic token refresh.
- **n8n-Grade Builder Studio**: Drag-and-drop ReactFlow canvas, auto-layout algorithms, undo/redo history, copy/paste, and node context menus.
- **Invisible OAuth 2.0**: Automated credential detection, multi-account binding, 60s background health monitor, and pop-up auth polling.
- **Execution Studio**: Live WebSocket event streaming (`/ws/execution/{id}`), resizable log console, elapsed timer, progress bar, 3-tab payload inspector, and canvas status overlays.
- **Real Analytics & Telemetry**: Stateful `AnalyticsEngine`, Recharts volume & latency charts, 9-connector SLA tracking, dynamic AI optimization recommendations, and date range filters (`24h`, `7d`, `30d`, `90d`).

---

## 📚 Platform Documentation Catalog

Detailed documentation is available in the [`docs/`](./docs/) directory:

| Document | Description |
|---|---|
| 🛠️ [**Developer Guide**](./docs/DEVELOPER_GUIDE.md) | Setup, repository structure, adding connectors, state management & testing guidelines. |
| 🚢 [**Deployment Guide**](./docs/DEPLOYMENT_GUIDE.md) | Docker, Docker Compose, Kubernetes manifests, NGINX SSL reverse proxy, and environment configs. |
| 📡 [**API Documentation**](./docs/API_DOCUMENTATION.md) | Complete REST & WebSocket API specification across all 26 platform endpoints. |
| 🏗️ [**Architecture Documentation**](./docs/ARCHITECTURE_DOCUMENTATION.md) | System design, Multi-Agent Planner V3, Runtime Engine V3, Event Bus, & Invisible OAuth. |
| 📖 [**User Guide**](./docs/USER_GUIDE.md) | Step-by-step user manual for Builder, Execution Studio, Marketplace, & Analytics. |
| 🔍 [**Troubleshooting Guide**](./docs/TROUBLESHOOTING_GUIDE.md) | Resolving OAuth token expiry, DLQ recovery, WebSocket reconnection, & rate limits. |

---

## 📦 Quickstart

### Prerequisites
- **Node.js**: `v20.x` or higher
- **Python**: `v3.11` or higher
- **npm**: `v10.x` or higher

### 1. Clone & Setup Frontend
```bash
# Clone the repository
git clone https://github.com/org/agentflow-ai.git
cd agentflow-ai

# Install frontend dependencies
npm install

# Build production bundle
npm run build

# Start frontend development server
npm run dev
```

### 2. Setup Backend FastAPI Server
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install backend dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

Frontend runs at `http://localhost:5173` and backend API runs at `http://localhost:8000` (`/docs` for Swagger UI).

---

## 🎨 Technology Stack

```
Frontend:  React 19 · TypeScript 6.0 · Vite 8 · Tailwind CSS v4 · Framer Motion · ReactFlow v12 · Recharts · Lucide
Backend:   FastAPI 0.110 · Python 3.11 · Pydantic v2 · SQLAlchemy 2.0 · WebSockets · HTTPX · PyJWT
Security:  AES-256 GCM Secret Vault · OWASP Headers · OAuth 2.0 PKCE · JWT Bearer Auth
```
