import React, { useState, useEffect } from 'react';
import {
  X,
  Sparkles,
  ShieldCheck,
  ShieldAlert,
  Copy,
  Check,
  Save,
  RotateCw,
  FileCheck2,
  AlertCircle,
} from 'lucide-react';
import { Job } from '../../types/job';
import {
  DocumentTailoringResponse,
  AntiHallucinationAuditResult,
} from '../../types/tailoring';
import { generateTailoredDocuments, auditDocumentText } from '../../api/tailoring';
import { attachDocument } from '../../api/applications';

interface TailoringWorkspaceModalProps {
  candidateProfileId: string;
  job: Job;
  applicationId?: string | null;
  isOpen: boolean;
  onClose: () => void;
  onSavedToApplication?: () => void;
}

export const TailoringWorkspaceModal: React.FC<TailoringWorkspaceModalProps> = ({
  candidateProfileId,
  job,
  applicationId,
  isOpen,
  onClose,
  onSavedToApplication,
}) => {
  const [activeTab, setActiveTab] = useState<'resume' | 'cover_letter'>('resume');
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generateError, setGenerateError] = useState<string | null>(null);

  // Document drafts
  const [tailoringData, setTailoringData] = useState<DocumentTailoringResponse | null>(null);
  const [resumeText, setResumeText] = useState<string>('');
  const [coverLetterText, setCoverLetterText] = useState<string>('');

  // Audit state
  const [isAuditing, setIsAuditing] = useState<boolean>(false);
  const [auditResult, setAuditResult] = useState<AntiHallucinationAuditResult | null>(null);

  // Save / Copy state
  const [copied, setCopied] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [saveSuccessMessage, setSaveSuccessMessage] = useState<string | null>(null);

  // Auto-generate if opened and empty
  useEffect(() => {
    if (isOpen && !tailoringData && !isGenerating) {
      handleGenerate();
    }
  }, [isOpen]);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setGenerateError(null);
    setSaveSuccessMessage(null);

    try {
      const result = await generateTailoredDocuments(candidateProfileId, job.id);
      setTailoringData(result);

      // Format resume bullets into editable markdown text
      const bulletSections: string[] = [];
      bulletSections.push(`### Target Role: ${result.resume_draft.target_job_title}\n`);
      bulletSections.push(`**Professional Summary:**\n${result.resume_draft.tailored_summary}\n`);
      bulletSections.push(`**Highlighted Verified Skills:**\n${result.resume_draft.highlighted_skills.join(', ')}\n`);
      bulletSections.push('**Tailored Experience Bullets:**');

      for (const [company, bullets] of Object.entries(result.resume_draft.tailored_experience_bullets)) {
        bulletSections.push(`\n*${company}*`);
        bullets.forEach((b) => bulletSections.push(`• ${b}`));
      }
      const formattedResume = bulletSections.join('\n');
      setResumeText(formattedResume);

      // Format cover letter
      const cl = result.cover_letter_draft;
      const formattedCL = [
        `Dear Hiring Team at ${cl.recipient_company || job.company},`,
        '',
        cl.opening_paragraph,
        '',
        ...cl.body_paragraphs,
        '',
        cl.closing_paragraph,
        '',
        cl.call_to_action,
        '',
        'Sincerely,',
        'Candidate',
      ].join('\n');
      setCoverLetterText(formattedCL);

      setAuditResult(result.audit_result);
    } catch (err: any) {
      setGenerateError(err.message || 'Failed to generate tailored application documents.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRunAudit = async () => {
    const textToAudit = activeTab === 'resume' ? resumeText : coverLetterText;
    if (!textToAudit) return;

    setIsAuditing(true);
    try {
      const res = await auditDocumentText(candidateProfileId, textToAudit, job.id);
      setAuditResult(res);
    } catch (err: any) {
      console.error('Audit failed:', err);
    } finally {
      setIsAuditing(false);
    }
  };

  const handleCopy = () => {
    const textToCopy = activeTab === 'resume' ? resumeText : coverLetterText;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSaveAndApprove = async () => {
    if (!applicationId) {
      setSaveSuccessMessage('Saved locally. Track this job in Kanban to link documents.');
      return;
    }

    setIsSaving(true);
    try {
      const docType = activeTab === 'resume' ? 'tailored_resume' : 'tailored_cover_letter';
      const content = activeTab === 'resume' ? resumeText : coverLetterText;

      await attachDocument(applicationId, {
        doc_type: docType,
        content: content,
        is_approved_by_user: true, // Candidate explicitly approved
      });

      setSaveSuccessMessage(`Approved & attached ${activeTab === 'resume' ? 'Resume' : 'Cover Letter'} to Application!`);
      if (onSavedToApplication) onSavedToApplication();
    } catch (err: any) {
      setSaveSuccessMessage(`Save failed: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl overflow-hidden shadow-2xl my-6 flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4 bg-slate-950/70">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg border border-indigo-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight">
                Grounded Document Tailoring
              </h2>
              <p className="text-xs text-slate-400">
                Tailored strictly to verified profile facts for {job.title} at {job.company}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab & Audit Banner */}
        <div className="px-6 py-3 bg-slate-950/40 border-b border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('resume')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                activeTab === 'resume'
                  ? 'bg-sky-600 text-white shadow'
                  : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700'
              }`}
            >
              Tailored Bullets Draft
            </button>
            <button
              onClick={() => setActiveTab('cover_letter')}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                activeTab === 'cover_letter'
                  ? 'bg-sky-600 text-white shadow'
                  : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700'
              }`}
            >
              Cover Letter Draft
            </button>
          </div>

          {/* Anti-Hallucination Audit Indicator */}
          {auditResult && (
            <div className="flex items-center gap-2">
              {auditResult.audit_status === 'PASS' ? (
                <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>Audit PASS: 100% Grounded</span>
                </div>
              ) : (
                <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-300 border border-amber-500/30">
                  <ShieldAlert className="w-4 h-4 text-amber-400" />
                  <span>Flagged {auditResult.unverified_skills_flagged.length} unverified skills</span>
                </div>
              )}

              <button
                onClick={handleRunAudit}
                disabled={isAuditing}
                className="text-[11px] text-slate-400 hover:text-sky-300 underline disabled:opacity-50"
                title="Re-run deterministic Python audit on modified text"
              >
                {isAuditing ? 'Auditing...' : 'Re-verify'}
              </button>
            </div>
          )}
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4">
          {isGenerating ? (
            <div className="py-20 flex flex-col items-center justify-center space-y-3">
              <RotateCw className="w-8 h-8 text-sky-400 animate-spin" />
              <p className="text-sm font-semibold text-white">Generating Grounded Documents...</p>
              <p className="text-xs text-slate-400 max-w-sm text-center">
                Deriving tailored resume bullets and cover letter strictly from verified candidate profile data.
              </p>
            </div>
          ) : generateError ? (
            <div className="p-4 bg-red-950/30 border border-red-800/50 rounded-xl text-xs text-red-300 space-y-2">
              <p className="font-semibold flex items-center gap-1.5">
                <AlertCircle className="w-4 h-4" /> Generation Error
              </p>
              <p>{generateError}</p>
              <button
                onClick={handleGenerate}
                className="mt-2 px-3 py-1 bg-red-900/40 hover:bg-red-900/60 rounded text-red-200 text-xs"
              >
                Try Again
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Audit Details Banner if flagged */}
              {auditResult && auditResult.audit_status === 'FLAGGED' && (
                <div className="p-3 bg-amber-950/30 border border-amber-800/40 rounded-xl text-xs space-y-1">
                  <div className="font-semibold text-amber-300 flex items-center gap-1.5">
                    <ShieldAlert className="w-4 h-4" /> Potential Unverified Skills Detected:
                  </div>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {auditResult.unverified_skills_flagged.map((skill, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 rounded bg-amber-900/40 text-amber-200 border border-amber-700/50 text-[11px]"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">
                    Review and verify that you actually possess these skills or remove them to maintain a 100% grounded application.
                  </p>
                </div>
              )}

              {/* Text Editor */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-400 flex items-center justify-between">
                  <span>
                    Editable {activeTab === 'resume' ? 'Resume Bullets' : 'Cover Letter'} Draft:
                  </span>
                  <span className="text-[11px] text-slate-500 font-normal">
                    Edits will be audited against your candidate profile
                  </span>
                </label>
                <textarea
                  value={activeTab === 'resume' ? resumeText : coverLetterText}
                  onChange={(e) => {
                    if (activeTab === 'resume') setResumeText(e.target.value);
                    else setCoverLetterText(e.target.value);
                  }}
                  rows={14}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs font-mono text-slate-200 focus:outline-none focus:border-sky-500 leading-relaxed resize-y selection:bg-sky-500/30"
                  placeholder="Tailored text draft..."
                />
              </div>

              {saveSuccessMessage && (
                <div className="p-3 bg-emerald-950/30 border border-emerald-800/40 rounded-xl text-xs text-emerald-300 flex items-center gap-2">
                  <FileCheck2 className="w-4 h-4 text-emerald-400" />
                  {saveSuccessMessage}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-slate-800 px-6 py-4 bg-slate-950/70">
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="flex items-center gap-2 text-xs text-slate-400 hover:text-white transition-colors"
          >
            <RotateCw className={`w-3.5 h-3.5 ${isGenerating ? 'animate-spin' : ''}`} />
            Regenerate Draft
          </button>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              onClick={handleCopy}
              className="flex-1 sm:flex-initial flex items-center justify-center gap-2 px-4 py-2 text-xs font-medium rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 text-slate-400" />
                  Copy Text
                </>
              )}
            </button>

            <button
              onClick={handleSaveAndApprove}
              disabled={isSaving || isGenerating}
              className="flex-1 sm:flex-initial flex items-center justify-center gap-2 px-5 py-2 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition-colors shadow-lg shadow-emerald-950 disabled:opacity-50"
            >
              <Save className="w-3.5 h-3.5" />
              {isSaving ? 'Approving...' : 'Approve & Save Document'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
