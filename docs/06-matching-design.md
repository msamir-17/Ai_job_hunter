# Matching Engine Design

## 1. 3-Tier Funnel Architecture

To optimize performance and minimize API token costs, jobs pass through three successive evaluation stages:

```text
500 Ingested Jobs
   │
   ▼ [Stage 1: Deterministic Filtering (SQL / Python)] -> Cost: $0.00
100 Candidates Passing Hard Criteria
   │
   ▼ [Stage 2: Vector Embedding Similarity (pgvector)] -> Cost: $0.00 (Local HF)
30 Top Semantic Matches
   │
   ▼ [Stage 3: LLM Skill Gap Analysis & Tailoring]     -> Cost: ~$0.002 / job
10 Final Shortlisted Jobs for Candidate Review
```

## 2. Stage Details

### Stage 1: Deterministic Filtering
- Location matching & remote preference enforcement.
- Experience level bounds (e.g., exclude senior management roles for fresher candidate profile).
- Blacklisted keywords & salary floor/ceiling checks.

### Stage 2: Dense Vector Similarity
- Dense vector generation via HuggingFace `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions).
- Cosine distance index (`HNSW`) in PostgreSQL via `pgvector`.
- Orders jobs by similarity to candidate profile embedding.

### Stage 3: LLM Skill Gap Analysis
- Invokes active LLM provider via `BaseLLMProvider`.
- Returns structured match score (0-100), verified skill overlap, missing required skills, and rationale.
