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

export interface WorkerHeartbeat {
  worker_id: string;
  status: string;
  last_heartbeat_at: string;
  jobs_processed: number;
  current_stage: string | null;
  is_alive: boolean;
  age_seconds: number;
}

export interface WorkerStatusResponse {
  queue_depths: {
    ingested: number;
    filtered: number;
    scored: number;
    tailored: number;
    notified: number;
    failed: number;
    dead_letter: number;
    [key: string]: number;
  };
  workers: WorkerHeartbeat[];
  active_worker_count: number;
}

export async function getWorkerStatus(): Promise<WorkerStatusResponse> {
  return apiClient<WorkerStatusResponse>('/api/v1/jobs/worker/status');
}

export async function triggerWorkerCycle(limit: number = 15, source: string = 'manual'): Promise<WorkerStatusResponse> {
  return apiClient<WorkerStatusResponse>(`/api/v1/jobs/worker/trigger-cycle?limit=${limit}&source=${source}`, {
    method: 'POST',
  });
}

export interface ManualJobSubmissionPayload {
  raw_text?: string | null;
  url?: string | null;
}

export async function submitManualJob(payload: ManualJobSubmissionPayload): Promise<Job> {
  return apiClient<Job>('/api/v1/jobs/manual', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

