# System Requirements Specification

## 1. Project Objective
The AI Job Hunter Co-Pilot is a full-stack platform designed to automate and augment the job discovery, matching, analysis, and document tailoring workflow for job seekers while maintaining human review and consent at all critical steps.

## 2. Functional Requirements

### 2.1 Candidate Profile & Resume Management
- **FR-1.1:** System shall allow candidates to create and maintain a candidate profile (contact info, skills, education, target titles, experience).
- **FR-1.2:** System shall support uploading PDF/DOCX resumes and extract raw text for candidate review.
- **FR-1.3:** System shall normalize candidate profile data into structured JSON format.

### 2.2 Job Ingestion & Normalization
- **FR-2.1:** System shall support job input via manual text paste, single URL import, or structured ingestion modules.
- **FR-2.2:** System shall normalize disparate job data into a unified schema (title, company, description, skills required, location, remote status, salary bounds, application URL).
- **FR-2.3:** System shall identify and de-duplicate duplicate job postings.

### 2.3 Multi-Tier Job Matching
- **FR-3.1:** System shall execute deterministic filters to eliminate jobs failing hard candidate criteria (location, experience level, remote status).
- **FR-3.2:** System shall compute vector similarity scores using HuggingFace embeddings (`all-MiniLM-L6-v2`) stored in `pgvector`.
- **FR-3.3:** System shall pass top vector matches to an LLM for structured match scoring, skill overlap extraction, and missing skill detection.

### 2.4 Grounded Document Tailoring
- **FR-4.1:** System shall generate resume bullet recommendations tailored to specific target jobs.
- **FR-4.2:** System shall generate tailored cover letter drafts.
- **FR-4.3:** System shall strictly restrict document generation to facts verified within the candidate profile (zero hallucination).

### 2.5 Human-in-the-Loop & Application Tracking
- **FR-5.1:** System shall present match analysis and tailored documents for candidate review and approval.
- **FR-5.2:** System shall open original application URLs in the browser; it shall NEVER automatically submit job applications.
- **FR-5.3:** System shall provide a dashboard to track application statuses (`Saved`, `Applied`, `Interviewing`, `Rejected`, `Offered`).

## 3. Non-Functional Requirements
- **NFR-1 (Performance):** Match analysis pipeline execution time shall remain under 3 seconds per job.
- **NFR-2 (Cost Optimization):** Pre-filtering via deterministic rules and vector similarity shall ensure less than 10% of total ingested jobs incur LLM API token costs.
- **NFR-3 (Extensibility):** LLM provider layer shall support hot-swapping between Gemini, Groq, and Mistral without workflow code changes.
