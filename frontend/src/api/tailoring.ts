import { apiClient } from './client';
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
