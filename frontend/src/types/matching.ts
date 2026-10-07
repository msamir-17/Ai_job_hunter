export interface PipelineRunResponse {
  id?: string;
  candidate_profile_id: string;
  job_id: string;
  passed_deterministic: boolean;
  deterministic_status?: string | null;
  vector_score?: number | null;
  vector_passed?: boolean | null;
  llm_score?: number | null;
  matched_skills: string[];
  missing_skills: string[];
  analysis_summary?: string | null;
  recommendation?: string | null;
  overall_status: 'shortlisted' | 'review' | 'rejected';
  current_stage: string;
  error_message?: string | null;
}

export interface CandidateJobMatch {
  id: string;
  candidate_profile_id: string;
  job_id: string;
  job_title?: string | null;
  job_company?: string | null;
  job_location?: string | null;
  job_is_remote?: boolean;
  passed_deterministic: boolean;
  vector_score?: number | null;
  llm_score?: number | null;
  status: 'shortlisted' | 'review' | 'rejected';
  matched_skills: string[];
  missing_skills: string[];
  analysis_summary?: string | null;
}
