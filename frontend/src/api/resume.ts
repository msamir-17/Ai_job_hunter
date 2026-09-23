import { apiClient } from './client';
import { ResumeResponse, ResumeExtractResponse, ResumeDraft } from '../types/resume';
import { CandidateProfileResponse } from '../types/candidateProfile';

export async function uploadResume(
  candidateProfileId: string,
  file: File
): Promise<ResumeResponse> {
  const formData = new FormData();
  formData.append('candidate_profile_id', candidateProfileId);
  formData.append('file', file);

  return apiClient<ResumeResponse>('/api/v1/resumes/upload', {
    method: 'POST',
    body: formData,
  });
}

export async function extractResume(
  resumeId: string
): Promise<ResumeExtractResponse> {
  return apiClient<ResumeExtractResponse>(`/api/v1/resumes/${resumeId}/extract`, {
    method: 'POST',
  });
}

export async function confirmResumeDraft(
  resumeId: string,
  draft: ResumeDraft
): Promise<CandidateProfileResponse> {
  return apiClient<CandidateProfileResponse>(`/api/v1/resumes/${resumeId}/confirm`, {
    method: 'POST',
    body: JSON.stringify(draft),
  });
}
