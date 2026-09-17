# System Architecture

## 1. High-Level System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                 React + TypeScript Frontend                 │
│         (Vite, React Router, Tailwind CSS, TanStack)         │
└──────────────────────────────┬──────────────────────────────┘
                               │ REST / HTTP
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend Core                      │
│   ┌───────────────────┬─────────────────────────────────┐   │
│   │   REST Controllers│ Services (Parsing, Vectoring)   │   │
│   └─────────┬─────────┴────────────────┬────────────────┘   │
└─────────────┼──────────────────────────┼────────────────────┘
              │                          │
              ▼                          ▼
┌───────────────────────────┐  ┌──────────────────────────────┐
│  PostgreSQL 16 + pgvector │  │   LangGraph Agent Engine     │
│  - Users & Profiles       │  │   ┌────────────────────────┐ │
│  - Normalized Jobs        │  │   │ BaseLLMProvider Adapt. │ │
│  - Dense Vector Embeddings│  │   └───────────┬────────────┘ │
│  - Job Match Results      │  └───────────────┼──────────────┘
└───────────────────────────┘                  │
                                               ▼
                                 ┌───────────────────────────┐
                                 │ Multi-LLM Provider Layer  │
                                 │ (Gemini, Groq, Mistral)   │
                                 └───────────────────────────┘
```

## 2. Key Component Responsibilities

1. **Frontend (React/TS):** Provides a dashboard for viewing profiles, imported jobs, match analyses, skill gap reports, document editing tools, and Kanban tracking.
2. **Backend (FastAPI):** Serves REST APIs, handles authentication, runs local HuggingFace embedding calculations (`all-MiniLM-L6-v2`), and orchestrates database transactions.
3. **Database (PostgreSQL + pgvector):** Primary relational store with native vector search capability for similarity matching.
4. **Agent Layer (LangGraph):** Manages match evaluation state machine and document generation node execution.
5. **LLM Provider Layer:** Abstract adapter pattern decoupling agent nodes from specific API providers (Gemini, Groq, Mistral).
