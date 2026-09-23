import { apiClient } from './client';
import { CandidateProfileResponse, CandidateProfileCreate } from '../types/candidateProfile';

export async function getCandidateProfile(
  profileId: string
): Promise<CandidateProfileResponse> {
  return apiClient<CandidateProfileResponse>(`/api/v1/candidate-profile/${profileId}`, {
    method: 'GET',
  });
}

export async function createCandidateProfile(
  payload: CandidateProfileCreate
): Promise<CandidateProfileResponse> {
  return apiClient<CandidateProfileResponse>('/api/v1/candidate-profile', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
