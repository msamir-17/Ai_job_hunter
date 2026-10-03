import { apiClient } from './client';
import { Job, IngestionRequest, IngestionResult } from '../types/job';

export interface ListJobsParams {
  source?: string;
  is_remote?: boolean;
  limit?: number;
  offset?: number;
}

export async function listJobs(params: ListJobsParams = {}): Promise<Job[]> {
  const searchParams = new URLSearchParams();
  if (params.source) searchParams.append('source', params.source);
  if (params.is_remote !== undefined) searchParams.append('is_remote', String(params.is_remote));
  if (params.limit !== undefined) searchParams.append('limit', String(params.limit));
  if (params.offset !== undefined) searchParams.append('offset', String(params.offset));

  const queryString = searchParams.toString();
  const endpoint = queryString ? `/api/v1/jobs?${queryString}` : '/api/v1/jobs';
  return apiClient<Job[]>(endpoint);
}

export async function getJob(jobId: string): Promise<Job> {
  return apiClient<Job>(`/api/v1/jobs/${jobId}`);
}

export async function ingestJobs(payload: IngestionRequest): Promise<IngestionResult> {
  return apiClient<IngestionResult>('/api/v1/jobs/ingest', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
