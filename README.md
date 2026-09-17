# AI Job Hunter Co-Pilot

A production-oriented AI job hunting platform designed to assist candidates with candidate profile parsing, intelligent job matching, skill gap analysis, grounded resume tailoring, cover letter drafting, and application tracking—with candidate approval required at every step.

## Technology Stack

* **Frontend:** React, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query
* **Backend:** Python, FastAPI, Pydantic, SQLAlchemy 2.0, PostgreSQL + pgvector, pytest
* **AI/Agent Layer:** LangGraph, Multi-Provider LLM Abstraction (Gemini, Groq, Mistral), Local HuggingFace Embeddings (`all-MiniLM-L6-v2`)

## Repository Structure

```text
ai_job_hunter/
├── README.md               # Project overview and developer quickstart
├── PROJECT_CONTEXT.md      # Core architecture principles and background
├── AGENTS.md               # Guidelines for AI coding assistants
├── .env.example            # Environment settings template
├── .gitignore              # Git exclusion rules
├── docs/                   # System design and architecture documentation
│   ├── 01-requirements.md
│   ├── 02-user-flows.md
│   ├── 03-architecture.md
│   ├── 04-data-model.md
│   ├── 05-agent-design.md
│   ├── 06-matching-design.md
│   ├── 07-evaluation.md
│   ├── 08-security.md
│   └── 09-deployment.md
├── backend/                # Python FastAPI application
│   ├── app/
│   │   ├── main.py         # Application entrypoint & health check
│   │   └── config.py       # Pydantic Settings management
│   └── tests/
│       └── test_health.py  # Health endpoint unit test
├── frontend/               # React + TypeScript + Vite application
│   ├── src/
│   │   ├── App.tsx         # Main application routes & query client setup
│   │   ├── main.tsx        # React DOM entrypoint
│   │   └── pages/          # Placeholder page components
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
└── data/                   # Raw, processed, and evaluation data directories
    ├── raw/
    ├── processed/
    └── evaluation/
```

## Quickstart Guide

### 1. Prerequisites
* Python 3.10+
* Node.js v18+ and npm v9+

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Health endpoint will be available at: `http://localhost:8000/health`

Running backend tests:
```bash
cd backend
pytest
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend development server will be available at: `http://localhost:5173`

## License
MIT
