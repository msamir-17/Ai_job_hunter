# Deployment Strategy

## 1. Local Development Setup
- **Database:** PostgreSQL 16 + `pgvector` containerized via Docker Compose.
- **Backend:** Python FastAPI application running under Uvicorn reload server.
- **Frontend:** React + TypeScript application served via Vite development server.

## 2. Minimal Docker Architecture (Planned for Production)
- **`docker-compose.yml` Services:**
  - `db`: PostgreSQL instance with `ankane/pgvector` pre-configured image.
  - `backend`: FastAPI application container running Gunicorn/Uvicorn workers.
  - `frontend`: NGINX web server serving static Vite production bundle.
