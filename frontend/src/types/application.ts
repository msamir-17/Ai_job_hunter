export type ApplicationStatus = 'saved' | 'applied' | 'interviewing' | 'rejected' | 'offer';

export interface GeneratedDocumentResponse {
  id: string;
  application_id: string;
  doc_type: string;
  content: string;
  is_approved_by_user: boolean;
  version: number;
  created_at?: string;
  updated_at?: string;
}

export interface ApplicationResponse {
  id: string;
  user_id: string;
  job_match_id: string;
  status: ApplicationStatus;
  applied_at?: string | null;
  notes?: string | null;
  job_id?: string | null;
  job_title?: string | null;
  job_company?: string | null;
  job_location?: string | null;
  job_is_remote?: boolean;
  job_url?: string | null;
  documents: GeneratedDocumentResponse[];
}
