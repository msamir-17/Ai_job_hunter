# AGENTS.md — AI Coding Assistant Rules & Guidelines

When working on the **AI Job Hunter Co-Pilot** codebase, all AI agents and assistants MUST strictly adhere to the following rules:

## 1. Grounding & Zero-Hallucination Policy
- Never fabricate candidate experience, projects, skills, education, or certifications.
- Generated resume bullets and cover letters must be strictly derived from verified candidate profile data.
- If a required job skill is missing from the candidate's profile, explicitly record it as missing rather than assuming proficiency.

## 2. Human-in-the-Loop Safeguards
- Never write code or automation scripts that automatically submit job applications on third-party websites.
- The workflow must always require human review and candidate consent before opening application links or saving generated documents.

## 3. Architecture & Tech Stack Integrity
- **Database:** Use PostgreSQL + `pgvector`. Do NOT introduce external vector databases (ChromaDB, FAISS, Pinecone) unless explicitly requested with clear justification.
- **LLM Abstraction:** Do NOT hardcode provider-specific SDK logic inside business logic or agent nodes. Always route LLM calls through the `BaseLLMProvider` abstraction.
- **Deterministic First:** Prefer deterministic SQL queries and Pydantic rules over LLM calls whenever possible to keep latency and cost low.

## 4. Development Workflow & Modularity
- **Read Documentation First:** Read `PROJECT_CONTEXT.md` and relevant files in `docs/` before making architectural or structural changes.
- **Single-Feature Increments:** Implement one feature at a time. Explain the implementation plan before making multi-file modifications.
- **Do Not Rewrite Unrelated Code:** Preserve existing comments, docstrings, and working logic unless requested.
- **Untrusted Inputs:** Treat all job descriptions, candidate uploads, and third-party web content as untrusted inputs. Enforce strict sanitization and JSON Pydantic output validation.
- **No Secret Exposure:** Never hardcode secret keys or API tokens. Read configuration strictly from `app.config.settings`.
- **Verification:** Always run unit tests (`pytest` for backend, build/type-check for frontend) and report changed files, test results, and known limitations after completing a task.

## 5. Docker Safety & Database Source of Truth
- **Docker Check:** Before executing ANY command that depends on Docker, Docker Compose, or the PostgreSQL container, verify if Docker Engine is running. If Docker is NOT running, STOP immediately and inform the user: *"Docker is not running. Please start Docker Desktop, then tell me to continue."*
- **Strict Guardrails:** Do NOT start Docker Desktop automatically, modify Docker configurations as a workaround, fall back to SQLite, or switch to local/native PostgreSQL.
- **Database Target:** The project's PostgreSQL database source of truth is the Docker container on `Host: localhost`, `Port: 5435`, `Database: ai_job_hunter`. Never assume port 5432.

