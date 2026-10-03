import { apiClient } from './client';
import { CandidateJobMatch, PipelineRunResponse } from '../types/matching';

export async function runMatchingPipeline(
  candidateProfileId: string,
  jobId: string
): Promise<PipelineRunResponse> {
  return apiClient<PipelineRunResponse>('/api/v1/matching/pipeline/run', {
    method: 'POST',
    body: JSON.stringify({
      candidate_profile_id: candidateProfileId,
      job_id: jobId,
    }),
  });
}

export async function getCandidateJobMatches(
  candidateProfileId: string,
  status?: string,
  limit: number = 50,
  offset: number = 0
): Promise<CandidateJobMatch[]> {
  const searchParams = new URLSearchParams();
  if (status) searchParams.append('status', status);
  searchParams.append('limit', String(limit));
  searchParams.append('offset', String(offset));

  return apiClient<CandidateJobMatch[]>(
    `/api/v1/matching/candidate/${candidateProfileId}/matches?${searchParams.toString()}`
  );
}

export async function runBatchDeterministicFilter(
  candidateProfileId: string,
  limit: number = 50
): Promise<{
  candidate_profile_id: string;
  total_evaluated: number;
  shortlisted_count: number;
  review_count: number;
  rejected_count: number;
}> {
  return apiClient('/api/v1/matching/deterministic/filter', {
    method: 'POST',
    body: JSON.stringify({
      candidate_profile_id: candidateProfileId,
      limit,
    }),
  });
}
