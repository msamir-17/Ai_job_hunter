export interface FeedbackCreate {
  job_id: string;
  candidate_profile_id?: string;
  reason_code: string;
  notes?: string;
  disliked_skill?: string;
}

export interface FeedbackResponse {
  id: string;
  user_id: string;
  candidate_profile_id: string;
  job_id: string;
  action: string;
  reason_code: string;
  notes?: string;
  disliked_skill?: string;
  created_at: string;
  vector_updated: boolean;
  message: string;
}
