# Security Architecture & Risk Mitigations

## 1. Risk Matrix & Mitigations

| Threat | Risk | Control / Mitigation |
|---|---|---|
| **API Key Leakage** | Critical | Load secrets strictly via `pydantic-settings` from local `.env`. Never expose keys to client JS. |
| **Prompt Injection** | High | Treat job descriptions as untrusted input. Wrap inside `<job_description>` tags and enforce JSON Pydantic response schemas. |
| **Resume Hallucination** | High | Run anti-hallucination guardrail validation against verified candidate skills. |
| **Unsafe Uploads** | Medium | Validate file extensions (`.pdf`, `.docx`), verify MIME types, limit max size to 5MB, use isolated parsers. |
| **Database Injection** | High | Use SQLAlchemy ORM parameterized queries for all relational and vector operations. |
| **Unintended Auto-Apply** | Critical | Strict architectural rule: System only opens application URLs in user browser. Auto-form filling is prohibited. |
