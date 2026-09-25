# AgentFlow AI — Deployment Guide

This guide details instructions for deploying AgentFlow AI to production environments using Docker, Docker Compose, Kubernetes, and NGINX Reverse Proxy with SSL/TLS.

---

## 🐳 Containerized Deployment (Docker & Compose)

### 1. `Dockerfile` (Backend FastAPI)
```dockerfile
FROM python:3.11-slim as builder

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 2. `docker-compose.yml` (Full Stack Stack)
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - PROJECT_NAME=AgentFlow AI Enterprise
      - DEBUG=False
      - API_V1_STR=/api/v1
      - SECRET_KEY=${SECRET_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
    restart: always

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: always
```

---

## 🌐 NGINX Reverse Proxy Configuration (`/etc/nginx/conf.d/agentflow.conf`)

```nginx
server {
    listen 80;
    server_name agentflow.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name agentflow.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/agentflow.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/agentflow.yourdomain.com/privkey.pem;

    # Frontend Static App
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # REST API Reverse Proxy
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket Execution Feed Proxy
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## 🔒 Security Best Practices Checklist
1. **SSL/TLS Enforcement**: Enable HTTP Strict Transport Security (HSTS) with 1-year max age.
2. **Environment Key Rotation**: Generate 32-byte AES-256 keys using `openssl rand -base64 32`.
3. **Database Encryption**: Encrypt Postgres connections with `sslmode=require`.
4. **CORS Policy**: Restrict `CORS_ORIGINS` to exact trusted production domain strings.
