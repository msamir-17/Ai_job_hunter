import { apiClient } from './client';
import { AntiHallucinationAuditResult, DocumentTailoringResponse } from '../types/tailoring';

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
