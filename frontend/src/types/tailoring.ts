export interface TailoredResumeDraft {
  target_job_title: string;
  tailored_summary: string;
  tailored_experience_bullets: Record<string, string[]>;
  highlighted_skills: string[];
}

export interface TailoredCoverLetterDraft {
  recipient_company: string;
  recipient_role: string;
  opening_paragraph: string;
  body_paragraphs: string[];
  closing_paragraph: string;
  call_to_action: string;
}

export interface AntiHallucinationAuditResult {
  total_skills_detected: number;
  verified_skills: string[];
  unverified_skills_flagged: string[];
  audit_status: 'PASS' | 'FLAGGED';
  message: string;
}

export interface DocumentTailoringResponse {
  candidate_profile_id: string;
  job_id: string;
  resume_draft: TailoredResumeDraft;
  cover_letter_draft: TailoredCoverLetterDraft;
  audit_result: AntiHallucinationAuditResult;
}
