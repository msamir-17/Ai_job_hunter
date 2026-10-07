import { apiClient } from './client';
import { CandidateProfileResponse, CandidateProfileCreate } from '../types/candidateProfile';

export async function listCandidateProfiles(
  limit: number = 10
): Promise<CandidateProfileResponse[]> {
  return apiClient<CandidateProfileResponse[]>(`/api/v1/candidate-profile?limit=${limit}`, {
    method: 'GET',
  });
}

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

export async function getActiveCandidateProfile(): Promise<CandidateProfileResponse> {
  return apiClient<CandidateProfileResponse>('/api/v1/candidate-profile/active', {
    method: 'GET',
  });
}

export async function updateCandidateProfile(
  profileId: string,
  payload: Partial<CandidateProfileCreate>
): Promise<CandidateProfileResponse> {
  return apiClient<CandidateProfileResponse>(`/api/v1/candidate-profile/${profileId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export async function deleteCandidateProfile(
  profileId: string
): Promise<void> {
  return apiClient<void>(`/api/v1/candidate-profile/${profileId}`, {
    method: 'DELETE',
  });
}
