# Matching Engine Design

## 1. 3-Tier Funnel Architecture

To optimize performance and minimize API token costs, jobs pass through three successive evaluation stages:

```text
500 Ingested Jobs
   │
   ▼ [Stage 1: Deterministic Filtering (SQL / Python)] -> Cost: $0.00
100 Candidates Passing Hard Criteria (including max experience ceiling e.g. <= 3.0 yrs)
   │
   ▼ [Stage 2: Vector Embedding Similarity (pgvector)] -> Cost: $0.00 (Local HF)
30 Top Semantic Matches
   │
   ▼ [Stage 2.5: Jev Fast-Pass Decision Model (NEW)]  -> Latency: ~100ms / job
   │  - Evaluates qualification (Noul), skill score 1-5 (Score), domain fit (Choice)
   │  - Re-verifies <= 3 yr ceiling & drops low-confidence fits (< 0.70)
10 Filtered High-Confidence Jobs
   │
   ▼ [Stage 3: LLM Skill Gap Analysis & Tailoring]     -> Cost: ~$0.002 / job
10 Final Shortlisted Jobs for Candidate Review
```

## 2. Stage Details

### Stage 1: Deterministic Filtering
- Location matching & remote preference enforcement.
- Candidate experience ceiling enforcement (`max_experience_required`: e.g. strictly exclude jobs requiring > 3 years).
- Experience level bounds & gap tolerance (`max_allowed_experience_gap`).
- Blacklisted keywords & salary floor/ceiling checks.

### Stage 2: Dense Vector Similarity
- Dense vector generation via HuggingFace `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions).
- Cosine distance index (`HNSW`) in PostgreSQL via `pgvector`.
- Orders jobs by similarity to candidate profile embedding.

### Stage 2.5: Jev Fast-Pass Decision Filter (System One)
- Evaluates state in 70–300ms using typed questions (`Noul`, `Score`, `Choice`).
- Validates candidate technical qualification, 1–5 skill overlap score, and experience ceiling.
- Filters out non-viable jobs before invoking generative LLMs.

### Stage 3: LLM Skill Gap Analysis & Tailoring
- Invokes active LLM provider via `BaseLLMProvider`.
- Returns structured match score (0-100), verified skill overlap, missing required skills, and rationale.

