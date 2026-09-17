# AI Job Hunter Co-Pilot — Project Context

## Project Overview
The AI Job Hunter Co-Pilot is a production-oriented AI application designed to help job candidates (specifically fresher AI/ML engineers) find, analyze, match, and apply for relevant job opportunities with grounded AI assistance.

## Key Principles & Architectural Guardrails

1. **Deterministic-First Multi-Tier Pipeline:**
   - **Stage 1 (Deterministic):** Hard SQL/Python filtering by experience level, remote status, location, and salary bounds.
   - **Stage 2 (Vector Similarity):** `pgvector` dense vector similarity search using 384-dimensional HuggingFace embeddings (`all-MiniLM-L6-v2`).
   - **Stage 3 (LLM Analysis):** Deep language understanding, skill gap extraction, match scoring, and grounded resume bullet tailoring.

2. **Single Database Architecture:**
   - PostgreSQL 16 with the `pgvector` extension manages both relational data (Users, Resumes, Jobs, Applications) and dense vector embeddings.
   - No standalone vector databases (ChromaDB, FAISS, Pinecone) are used.

3. **Isolated LLM Provider Abstraction:**
   - Core LangGraph workflow interacts with LLMs exclusively via an abstract `BaseLLMProvider` interface.
   - Providers (Google Gemini, Groq, Mistral) are swappable via environment configuration (`ACTIVE_LLM_PROVIDER`) without modifying workflow logic.

4. **Strict Human-in-the-Loop (HITL):**
   - **No Auto-Applying:** The system never submits job applications automatically.
   - Candidates review matched jobs, inspect skill gaps, approve/edit generated materials, and click the original application URL manually.

5. **Anti-Hallucination & Fact Grounding:**
   - Generated resume bullets and cover letters must be strictly grounded in verified candidate profile/resume data.
   - The AI must explicitly identify missing requirements rather than fabricating experience.

6. **Tech Stack:**
   - **Frontend:** React, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query.
   - **Backend:** Python, FastAPI, Pydantic, SQLAlchemy 2.0, PostgreSQL + pgvector, pytest.
   - **AI/Agent Layer:** LangGraph, Local HuggingFace embeddings, Multi-provider LLM abstraction.
