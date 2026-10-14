import { apiClient } from './client';
import { FeedbackCreate, FeedbackResponse } from '../types/feedback';

export async function discardJobApi(
  payload: FeedbackCreate
): Promise<FeedbackResponse> {
  return apiClient<FeedbackResponse>('/api/v1/feedback/discard', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function listFeedbackApi(
  candidateProfileId?: string
): Promise<FeedbackResponse[]> {
  const query = candidateProfileId ? `?candidate_profile_id=${candidateProfileId}` : '';
  return apiClient<FeedbackResponse[]>(`/api/v1/feedback${query}`, {
    method: 'GET',
  });
}

export async function deleteFeedbackApi(
  feedbackId: string
): Promise<void> {
  return apiClient<void>(`/api/v1/feedback/${feedbackId}`, {
    method: 'DELETE',
  });
}
