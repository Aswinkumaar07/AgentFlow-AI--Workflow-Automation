# AgentFlow AI – Backend Architecture

Production-grade, enterprise-ready backend foundation for **AgentFlow AI - Intelligent API Workflow Automation** built with Python 3.12, FastAPI, SQLAlchemy 2.0, PostgreSQL, and Redis.

---

## 🏛️ Architecture Principles

- **Repository Pattern & Service Layer**: Complete decoupling of data persistence, business logic, and API presentation routers.
- **Clean Architecture & Dependency Injection**: Fast, testable, modular components.
- **Standardized JSON Envelope**:
  - Success Response:
    ```json
    {
      "success": true,
      "message": "Operation completed successfully.",
      "data": {}
    }
    ```
  - Error Response:
    ```json
    {
      "success": false,
      "message": "Unauthorized",
      "error_code": "AUTH_401"
    }
    ```
- **AI-Ready Plugin Interfaces**: Placeholders and Abstract Base Classes (ABCs) in `app/agents/` for Multi-Agent Planner, LangGraph Workflow Generator, API Discovery, RAG, Memory, and Self-Healing.

---

## 🛠️ Tech Stack

- **Framework**: FastAPI (Python 3.12)
- **Database**: PostgreSQL 16 + SQLAlchemy 2.0 (Async) + Alembic
- **Caching**: Redis 7
- **Security**: JWT (python-jose) + Password Hashing (passlib / bcrypt)
- **Validation**: Pydantic v2
- **Containerization**: Docker & Docker Compose

---

## 🚦 Quick Start with Docker Compose

```bash
cd backend
cp .env.example .env
docker-compose up --build -d
```

Access Swagger UI Documentation at: **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## 🔗 Core API Endpoints (`/api/v1`)

| Module | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **Health** | `GET` | `/api/v1/health` | System health check |
| **Auth** | `POST` | `/api/v1/auth/register` | Register user |
| **Auth** | `POST` | `/api/v1/auth/login` | Login & issue JWT tokens |
| **Auth** | `POST` | `/api/v1/auth/refresh` | Refresh JWT access token |
| **Users** | `GET` | `/api/v1/users/me` | Current authenticated user profile |
| **Workflows** | `POST` | `/api/v1/workflows` | Create workflow DAG |
| **Workflows** | `GET` | `/api/v1/workflows` | List user workflows |
| **Executions** | `POST` | `/api/v1/executions/{id}/execute` | Execute workflow pipeline |
| **Executions** | `GET` | `/api/v1/executions/{id}/logs` | Step-by-step execution telemetry logs |
| **Analytics** | `GET` | `/api/v1/analytics` | Dashboard statistics |
