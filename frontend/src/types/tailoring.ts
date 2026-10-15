export interface TailoredResumeBullet {
  bullet_point: string;
  relevant_skill: string;
  source_experience_company?: string | null;
  grounding_rationale: string;
}

export interface TailoredResumeDraft {
  target_role?: string;
  target_job_title?: string;
  company_name?: string;
  bullets?: TailoredResumeBullet[];
  tailored_summary?: string;
  tailored_experience_bullets?: Record<string, string[]>;
  highlighted_skills?: string[];
}

export interface TailoredCoverLetterDraft {
  recipient?: string;
  recipient_company?: string;
  opening_paragraph: string;
  body_paragraphs: string[];
  closing_paragraph: string;
  call_to_action?: string;
  full_text?: string;
  highlighted_skills?: string[];
}

export interface AntiHallucinationAuditResult {
  is_grounded?: boolean;
  hallucinated_terms?: string[];
  verified_terms_used?: string[];
  audit_explanation?: string;
  total_skills_detected?: number;
  verified_skills?: string[];
  unverified_skills_flagged?: string[];
  audit_status?: 'PASS' | 'FLAGGED';
  message?: string;
}

export interface DocumentTailoringResponse {
  candidate_profile_id: string;
  job_id: string;
  resume_draft: TailoredResumeDraft;
  cover_letter?: TailoredCoverLetterDraft;
  cover_letter_draft?: TailoredCoverLetterDraft;
  audit_result: AntiHallucinationAuditResult;
  is_approved_by_user?: boolean;
}

export interface ArchetypeConfig {
  archetype_id: string;
  display_name: string;
  description: string;
  section_order: string[];
  skill_category_order: string[];
  primary_angle: string;
  max_projects: number;
  max_bullets_per_flagship: number;
  max_bullets_per_standard: number;
  headline_template: string;
  summary_template: string;
  keywords: string[];
}

export interface TailoredProjectItem {
  project_name: string;
  role_or_title: string;
  timeline: string;
  is_flagship: boolean;
  bullets: string[];
  cited_fact_ids: string[];
}

export interface OnePageBudgetAudit {
  total_characters: number;
  estimated_total_lines: number;
  max_allowed_lines: number;
  is_strictly_one_page: boolean;
  summary_lines: number;
  skills_lines: number;
  projects_lines: number;
  education_lines: number;
  audit_notes: string;
}

export interface ATSTailoredResume {
  candidate_name: string;
  headline: string;
  email: string;
  location: string;
  github_url?: string | null;
  linkedin_url?: string | null;
  portfolio_url?: string | null;
  target_job_title: string;
  target_company: string;
  archetype_id: string;
  archetype_display_name: string;
  summary: string;
  skill_categories: Record<string, string[]>;
  projects: TailoredProjectItem[];
  education: string[];
  budget_audit: OnePageBudgetAudit;
}
