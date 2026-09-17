# User Flows & Interactions

## 1. Candidate Onboarding & Profile Setup Flow

```text
[ Start ]
   │
   ▼
[ User Signs Up / Logs In ]
   │
   ▼
[ Upload Resume (PDF / DOCX) ] ──► [ Text Extracted & Parsed ]
   │                                           │
   ▼                                           ▼
[ Review Parsed Profile ] ◄─────────── [ Populate Skills & Experience ]
   │
   ▼
[ Save Candidate Profile ] ──► [ Generate Profile Embedding (pgvector) ]
```

## 2. Job Discovery & Multi-Tier Matching Flow

```text
[ Ingest Jobs (Manual URL / Import) ]
   │
   ▼
[ Normalize Job Data Schema ]
   │
   ▼
[ Stage 1: Deterministic Filtering ] ──► (Disqualified Jobs Excluded)
   │
   ▼
[ Stage 2: Vector Similarity Search ] ──► (Top 30 Semantic Matches Selected)
   │
   ▼
[ Stage 3: LLM Skill Gap Analysis ]
   │
   ▼
[ Render Match Breakdown in Dashboard ]
```

## 3. Human-in-the-Loop Document Tailoring & Application Flow

```text
[ Review Matched Job in UI ]
   │
   ▼
[ Request Tailored Resume / Cover Letter ]
   │
   ▼
[ LLM Generates Grounded Bullet Points ]
   │
   ▼
[ Automated Anti-Hallucination Guardrail Audit ]
   │
   ▼
[ Candidate Edits & Approves Tailored Content ]
   │
   ▼
[ Click 'Apply Externally' Button ] ──► [ Opens Original Job Link in New Tab ]
   │
   ▼
[ Application Status Tracked in Kanban ]
```
