import { apiClient } from './client';
import {
  ApplicationResponse,
  ApplicationStatus,
  GeneratedDocumentResponse,
} from '../types/application';

export async function listApplications(
  userId?: string,
  status?: ApplicationStatus
): Promise<ApplicationResponse[]> {
  const searchParams = new URLSearchParams();
  if (userId) searchParams.append('user_id', userId);
  if (status) searchParams.append('status', status);

  const queryString = searchParams.toString();
  const endpoint = queryString ? `/api/v1/applications?${queryString}` : '/api/v1/applications';
  return apiClient<ApplicationResponse[]>(endpoint);
}

export async function getApplication(applicationId: string): Promise<ApplicationResponse> {
  return apiClient<ApplicationResponse>(`/api/v1/applications/${applicationId}`);
}

export async function createApplication(payload: {
  user_id: string;
  job_match_id: string;
  status?: ApplicationStatus;
  notes?: string;
}): Promise<ApplicationResponse> {
  return apiClient<ApplicationResponse>('/api/v1/applications', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateApplicationStatus(
  applicationId: string,
  status: ApplicationStatus,
  notes?: string
): Promise<ApplicationResponse> {
  return apiClient<ApplicationResponse>(`/api/v1/applications/${applicationId}`, {
    method: 'PATCH',
    body: JSON.stringify({
      status,
      notes,
    }),
  });
}

export async function deleteApplication(applicationId: string): Promise<void> {
  return apiClient<void>(`/api/v1/applications/${applicationId}`, {
    method: 'DELETE',
  });
}

export async function attachDocument(
  applicationId: string,
  payload: {
    doc_type: string;
    content: string;
    is_approved_by_user?: boolean;
  }
): Promise<GeneratedDocumentResponse> {
  return apiClient<GeneratedDocumentResponse>(`/api/v1/applications/${applicationId}/documents`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function updateDocumentApproval(
  applicationId: string,
  documentId: string,
  payload: {
    content?: string;
    is_approved_by_user?: boolean;
  }
): Promise<GeneratedDocumentResponse> {
  return apiClient<GeneratedDocumentResponse>(
    `/api/v1/applications/${applicationId}/documents/${documentId}`,
    {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }
  );
}
