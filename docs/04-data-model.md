# Data Model & Schema Specifications

## 1. Relational Entities & Relationships

### `users`
- `id`: UUID (PK)
- `email`: VARCHAR(255) (Unique, Indexed)
- `hashed_password`: VARCHAR(255)
- `full_name`: VARCHAR(255)
- `created_at`: TIMESTAMPTZ

### `candidate_profiles`
- `id`: UUID (PK)
- `user_id`: UUID (FK -> users.id)
- `headline`: VARCHAR(255)
- `summary`: TEXT
- `skills`: JSONB (Array of verified skills)
- `experience`: JSONB (Structured employment history)
- `education`: JSONB (Degrees and academic background)
- `target_titles`: JSONB (Preferred roles)
- `embedding`: VECTOR(384) (Dense profile vector generated via `all-MiniLM-L6-v2`)

### `resumes`
- `id`: UUID (PK)
- `candidate_profile_id`: UUID (FK -> candidate_profiles.id)
- `file_name`: VARCHAR(255)
- `raw_text`: TEXT
- `parsed_json`: JSONB
- `created_at`: TIMESTAMPTZ

### `jobs`
- `id`: UUID (PK)
- `source`: VARCHAR(50) (e.g., "manual", "imported")
- `external_id`: VARCHAR(255)
- `title`: VARCHAR(255) (Indexed)
- `company`: VARCHAR(255) (Indexed)
- `location`: VARCHAR(255)
- `is_remote`: BOOLEAN
- `salary_min`: INTEGER
- `salary_max`: INTEGER
- `description_raw`: TEXT
- `skills_required`: JSONB
- `url`: VARCHAR(1024)
- `embedding`: VECTOR(384) (Dense job vector generated via `all-MiniLM-L6-v2`)
- `created_at`: TIMESTAMPTZ

### `job_matches`
- `id`: UUID (PK)
- `candidate_profile_id`: UUID (FK -> candidate_profiles.id)
- `job_id`: UUID (FK -> jobs.id)
- `passed_deterministic`: BOOLEAN
- `vector_score`: FLOAT (Cosine similarity score)
- `llm_score`: INTEGER (Match score 0-100)
- `matched_skills`: JSONB
- `missing_skills`: JSONB
- `analysis_summary`: TEXT
- `status`: VARCHAR(50) ("shortlisted", "rejected", "approved")

### `applications`
- `id`: UUID (PK)
- `user_id`: UUID (FK -> users.id)
- `job_match_id`: UUID (FK -> job_matches.id)
- `status`: VARCHAR(50) ("saved", "applied", "interviewing", "rejected", "offer")
- `applied_at`: TIMESTAMPTZ
- `notes`: TEXT

### `generated_documents`
- `id`: UUID (PK)
- `application_id`: UUID (FK -> applications.id)
- `doc_type`: VARCHAR(50) ("tailored_resume_bullets", "cover_letter")
- `content`: TEXT
- `is_approved_by_user`: BOOLEAN
