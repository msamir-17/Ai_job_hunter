# Evaluation Framework & Quality Metrics

## 1. Metrics Overview

The matching engine, extraction quality, and document tailoring are evaluated using measurable key performance indicators:

1. **Job Extraction Quality:**
   - Field Completeness Rate: % of ingested jobs containing mandatory metadata (title, company, description, URL).
   - Deduplication Precision: % of duplicate job postings correctly detected and unified.

2. **Semantic Matching Performance:**
   - Recall@30: % of candidate-accepted jobs appearing in the top 30 vector similarity search results.
   - Deterministic Accuracy: Precision of hard filter exclusions.

3. **Factuality & Grounding (Critical):**
   - Hallucination Rate: % of generated resume bullet points containing skills or experience not present in the candidate profile (Target: **0%**).

4. **System Efficiency & Reliability:**
   - Pipeline Latency: End-to-end execution time per job analysis (Target: **< 3.0s**).
   - Cost Per Job Analyzed: Token cost per evaluated posting (Target: **< $0.005**).
   - Schema Conformance: % of LLM output responses parsing cleanly into Pydantic models.
