# AgentFlow AI — User Guide

Welcome to the AgentFlow AI User Guide. This manual walks you through building, executing, monitoring, and managing automated API workflows.

---

## 🎨 1. Workflow Builder & AI Planner

### Building via AI Prompt
1. Navigate to **Builder** from the left navigation bar.
2. In the top AI prompt box, type your automation goal in plain English:
   > *"When a new invoice email arrives in Gmail, save the attachment to Google Drive, notify Slack #invoices, and append a row in Google Sheets."*
3. Click **Generate Workflow**. The Multi-Agent Planner will generate nodes, edges, parameters, and automatic account bindings.

### Manual Canvas Editing
- **Add Nodes**: Drag connectors from the left Connector Palette onto the canvas.
- **Connect Nodes**: Drag from a node's output handle to another node's input handle.
- **Auto-Layout**: Click **Auto Layout** in the top toolbar to automatically organize nodes into a clean left-to-right DAG.
- **Node Inspector**: Click any node to configure parameters, view schema, or switch connected OAuth accounts.

---

## ⚡ 2. Execution Studio

1. Click **Run Workflow** or select a **Verified Preset** (`WF 1`, `WF 2`, `WF 3`, `WF 4`).
2. Watch live execution on the canvas:
   - **Pulse Rings & Glow**: Shows currently running node.
   - **Green Badge**: Step completed successfully with latency in milliseconds.
   - **Red Badge**: Step failed (pushes run to Dead Letter Queue).
3. Use the **Payload Inspector Modal** to inspect raw JSON inputs, outputs, variables, and execution path.
4. Drag the bottom **Live Logs Console** handle upward to view ms-precision execution logs.

---

## 🔑 3. Invisible OAuth Account Management

1. Navigate to **Settings** → **OAuth 2.0 Accounts**.
2. View connected account health badges (`HEALTHY`, `EXPIRED`, `DEGRADED`).
3. Click **Connect New Account** to authorize via OAuth popup.
4. Newly connected accounts automatically bind to active builder nodes without manual configuration!

---

## 📊 4. Telemetry & Analytics

1. Navigate to **Analytics**.
2. Select date filters: `24h`, `7d`, `30d`, `90d`.
3. View volume trend charts, latency distribution bars, connector SLA health grid, and AI optimization recommendations.
