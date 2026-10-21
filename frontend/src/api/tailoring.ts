import { apiClient, BASE_URL } from './client';
import {
  AntiHallucinationAuditResult,
  ArchetypeConfig,
  ATSTailoredResume,
  DocumentTailoringResponse,
} from '../types/tailoring';

export async function generateTailoredDocuments(
  candidateProfileId: string,
  jobId: string
): Promise<DocumentTailoringResponse> {
  return apiClient<DocumentTailoringResponse>('/api/v1/tailoring/generate', {
    method: 'POST',
    body: JSON.stringify({
      candidate_profile_id: candidateProfileId,
      job_id: jobId,
    }),
  });
}

export async function auditDocumentText(
  candidateProfileId: string,
  textToAudit: string,
  jobId?: string | null
): Promise<AntiHallucinationAuditResult> {
  return apiClient<AntiHallucinationAuditResult>('/api/v1/tailoring/audit', {
    method: 'POST',
    body: JSON.stringify({
      candidate_profile_id: candidateProfileId,
      text_to_audit: textToAudit,
      job_id: jobId || undefined,
    }),
  });
}

export async function getArchetypes(): Promise<ArchetypeConfig[]> {
  return apiClient<ArchetypeConfig[]>('/api/v1/tailoring/archetypes', {
    method: 'GET',
  });
}

export async function generateATSResume(
  candidateProfileId: string,
  jobId: string,
  forcedArchetypeId?: string | null
): Promise<ATSTailoredResume> {
  return apiClient<ATSTailoredResume>('/api/v1/tailoring/ats-resume', {
    method: 'POST',
    body: JSON.stringify({
      candidate_profile_id: candidateProfileId,
      job_id: jobId,
      forced_archetype_id: forcedArchetypeId || undefined,
    }),
  });
}

export async function downloadATSTailoredResumePdf(
  resume: ATSTailoredResume,
  filename?: string
): Promise<void> {
  const url = `${BASE_URL}/api/v1/tailoring/ats-resume/download-from-data`;
  const token = localStorage.getItem('auth_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(resume),
  });

  if (!response.ok) {
    throw new Error(`Failed to generate PDF: ${response.statusText}`);
  }

  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = downloadUrl;
  const cleanName = (resume.candidate_name || 'Resume').replace(/[^a-zA-Z0-9_-]/g, '_');
  link.download = filename || `${cleanName}_ATS_Resume.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(downloadUrl);
}

