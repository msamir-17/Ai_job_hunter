# Local Database Architecture & Deployment Strategy

## 1. Local Database Architecture

The application uses a containerized PostgreSQL 16 database equipped with the `pgvector` extension for storing both relational application metadata and 384-dimensional dense vector embeddings.

### System Flow
```text
Application
    ↓
FastAPI
    ↓
PostgreSQL + pgvector
    ↓
Docker container
    ↓
Persistent Docker volume
```

## 2. Infrastructure Components

* **Docker's Role:** Provides an isolated, reproducible container environment for running PostgreSQL 16 compiled with `pgvector` without requiring native PostgreSQL installation on the host OS.
* **PostgreSQL's Role:** Primary ACID-compliant database storing relational data (Users, Candidate Profiles, Resumes, Jobs, Job Matches, Applications, Generated Documents).
* **`pgvector`'s Role:** PostgreSQL extension providing native vector storage (`VECTOR(384)`) and ultra-fast distance search operations (Cosine `<=>`, L2 `<->`, Inner Product `<#>`) indexed using HNSW.
* **Persistent Docker Volume (`ai_job_hunter_postgres_data`):** Managed Docker disk volume mounted to `/var/lib/postgresql/data` inside the container. Ensures database records and vector indexes persist across container restarts, updates, and recreation.

## 3. Environment Variables Configuration

| Variable | Default Value | Description |
|---|---|---|
| `POSTGRES_USER` | `postgres` | PostgreSQL superuser username |
| `POSTGRES_PASSWORD` | `postgres` | PostgreSQL superuser password |
| `POSTGRES_HOST` | `localhost` | Database host address |
| `POSTGRES_PORT` | `5432` | Local host port exposed for database connections |
| `POSTGRES_DB` | `ai_job_hunter` | Target database name |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/ai_job_hunter` | SQLAlchemy async connection URI |

> **Note:** Never commit real secrets to source control. Set custom credentials in `.env` (ignored by Git).

## 4. Database Operations Guide

### Starting the Database Container
```bash
docker compose up -d
```

### Inspecting Container Status & Logs
```bash
# Check container status
docker compose ps

# View database container logs
docker compose logs db -f
```

### Stopping the Database Container
```bash
# Stop containers (preserves database volume data)
docker compose down

# Stop containers AND delete volume data (use with caution!)
docker compose down -v
```

### Verifying `pgvector` Availability
Execute the following verification commands to ensure PostgreSQL and the `vector` extension are active:

```bash
# 1. Enable the pgvector extension inside the database
docker exec -i ai_job_hunter_db psql -U postgres -d ai_job_hunter -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 2. Verify extension registration in system catalog
docker exec -i ai_job_hunter_db psql -U postgres -d ai_job_hunter -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```
Expected output:
```text
 extname | extversion 
---------+------------
 vector  | 0.8.0
(1 row)
```
