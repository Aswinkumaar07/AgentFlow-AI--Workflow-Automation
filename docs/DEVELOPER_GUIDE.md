# AgentFlow AI — Developer Guide

Welcome to the AgentFlow AI Developer Guide. This document provides technical instructions for contributing to, extending, and maintaining the AgentFlow AI platform.

---

## 📁 Repository Structure

```
.
├── backend/                  # FastAPI Backend Python Workspace
│   ├── app/
│   │   ├── agents/           # Multi-Agent Planner V3 (Discovery, Ranker, Parameter AI, Validator)
│   │   ├── analytics/        # Real-time Analytics Engine & SLA telemetry tracker
│   │   ├── api/v1/           # REST endpoints & WebSocket routers
│   │   ├── connectors/       # Production Provider Adapters (Gmail, Drive, Sheets, Slack, GitHub, Notion, Stripe)
│   │   ├── core/             # Config, security, exception handlers, JWT authentication
│   │   ├── database/         # SQLAlchemy 2.0 ORM sessions and migrations
│   │   ├── oauth/            # Invisible OAuth 2.0 manager, refresh engine & health monitor
│   │   ├── runtime/          # Runtime Engine V3 (Executor, Event Bus, DLQ, Checkpoints, Approvals)
│   │   └── main.py           # FastAPI application entrypoint & middleware stack
│   └── requirements.txt
├── src/                      # React 19 Frontend Workspace
│   ├── api/                  # API Client modules (analytics, execution, marketplace, oauth, runtime)
│   ├── components/           # UI Component catalog (builder, dashboard, execution, layout, common)
│   ├── hooks/                # Custom hooks (useExecutionWebSocket, useTheme, etc.)
│   ├── pages/                # Top-level Page views (Dashboard, Builder, Execution Studio, Analytics, Settings, Marketplace, ErrorReplay)
│   ├── store/                # Zustand State Stores (useWorkflowStore, useExecutionStore, usePlannerStore)
│   ├── types/                # TypeScript Interfaces & Data Models
│   └── App.tsx               # Root Application wrapper & Provider tree
├── docs/                     # Production Platform Documentation
└── vite.config.ts            # Vite Build & Rollup Manual Chunks Config
```

---

## 🛠️ Local Development Environment Setup

### 1. Environment Variables (`backend/.env`)
Create a `.env` file in `backend/`:
```env
PROJECT_NAME="AgentFlow AI Enterprise"
DEBUG=True
API_V1_STR="/api/v1"
SECRET_KEY="super-secret-jwt-key-replace-in-production"
ENCRYPTION_KEY="32-byte-base64-secret-key-for-aes-256-gcm"

# OAuth Credentials
GMAIL_CLIENT_ID="your-gmail-client-id"
GMAIL_CLIENT_SECRET="your-gmail-client-secret"
SLACK_CLIENT_ID="your-slack-client-id"
SLACK_CLIENT_SECRET="your-slack-client-secret"
```

### 2. Frontend Development Server
```bash
npm run dev
```
Runs at `http://localhost:5173`. Any changes to components trigger instant Vite HMR.

---

## 🔌 Adding a New Connector Provider Adapter

To add a new provider adapter (e.g. `HubSpotAdapter`):

1. **Create Adapter Directory**: `backend/app/connectors/providers/hubspot/`
2. **Implement `HubSpotAdapter`**:
   ```python
   from app.connectors.interfaces import BaseProviderAdapter
   from app.connectors.models import ConnectorMetadataModel, ConnectorRequestModel, ConnectorResponseModel

   class HubSpotAdapter(BaseProviderAdapter):
       @property
       def provider_name(self) -> str:
           return "HubSpot"

       def get_metadata(self) -> ConnectorMetadataModel:
           return ConnectorMetadataModel(
               provider="HubSpot",
               version="v3",
               supported_operations=["hubspot.contacts.create", "hubspot.deals.list"],
               auth_types=["OAuth2", "Bearer"],
           )

       async def execute_operation(self, request: ConnectorRequestModel, credentials=None) -> ConnectorResponseModel:
           # Implementation logic here
           pass
   ```
3. **Register in `ConnectorRegistry`**:
   Add `self.register(HubSpotAdapter())` in `backend/app/connectors/registry.py` and update `ALIAS_MAP`.

---

## 🧪 Code Verification & Formatting

Run full TypeScript build check:
```bash
npm run build
```
Verify `Exit Code 0` with zero type errors.

Run backend tests:
```bash
cd backend
pytest app/tests/ -v
```
