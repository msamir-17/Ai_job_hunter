import { EducationItem, ExperienceItem } from './resume';

export interface CandidateProfileBase {
  headline?: string | null;
  summary?: string | null;
  skills?: string[] | null;
  experience?: ExperienceItem[] | null;
  education?: EducationItem[] | null;
  target_titles?: string[] | null;
}

export interface CandidateProfileCreate extends CandidateProfileBase {
  user_id: string;
}

export interface CandidateProfileUpdate extends CandidateProfileBase {}

export interface CandidateProfileResponse extends CandidateProfileBase {
  id: string;
  user_id: string;
}
