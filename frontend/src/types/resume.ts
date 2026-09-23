export interface ExperienceItem {
  company?: string | null;
  title?: string | null;
  location?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  description?: string | null;
  achievements?: string[];
  technologies?: string[];
}

export interface EducationItem {
  institution?: string | null;
  degree?: string | null;
  field_of_study?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  description?: string | null;
}

export interface ResumeDraft {
  headline?: string | null;
  summary?: string | null;
  skills: string[];
  experience: ExperienceItem[];
  education: EducationItem[];
  target_titles: string[];
}

export interface ResumeResponse {
  id: string;
  candidate_profile_id: string;
  file_name: string;
  status: string;
  raw_text_length: number;
  created_at: string;
}

export interface ResumeExtractResponse {
  id: string;
  candidate_profile_id: string;
  file_name: string;
  status: string;
  draft: ResumeDraft;
}
