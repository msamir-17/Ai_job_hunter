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
