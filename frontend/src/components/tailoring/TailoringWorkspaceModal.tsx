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
  Printer,
  Layers,
  FileText,
} from 'lucide-react';
import { Job } from '../../types/job';
import {
  DocumentTailoringResponse,
  AntiHallucinationAuditResult,
  ATSTailoredResume,
  ArchetypeConfig,
} from '../../types/tailoring';
import {
  generateTailoredDocuments,
  auditDocumentText,
  generateATSResume,
  getArchetypes,
} from '../../api/tailoring';
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
  const [activeTab, setActiveTab] = useState<'ats_resume' | 'resume' | 'cover_letter'>('ats_resume');
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generateError, setGenerateError] = useState<string | null>(null);

  // ATS Resume Studio state
  const [atsResume, setAtsResume] = useState<ATSTailoredResume | null>(null);
  const [isGeneratingATS, setIsGeneratingATS] = useState<boolean>(false);
  const [selectedArchetype, setSelectedArchetype] = useState<string | null>(null);
  const [availableArchetypes, setAvailableArchetypes] = useState<ArchetypeConfig[]>([]);

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

  // Load archetypes and auto-generate when opened
  useEffect(() => {
    if (isOpen) {
      loadArchetypes();
      if (!atsResume && !isGeneratingATS) {
        handleGenerateATS(null);
      }
      if (!tailoringData && !isGenerating) {
        handleGenerateLegacyDrafts();
      }
    }
  }, [isOpen]);

  const loadArchetypes = async () => {
    try {
      const archs = await getArchetypes();
      setAvailableArchetypes(archs);
    } catch (err) {
      console.error('Failed to load archetypes:', err);
    }
  };

  const handleGenerateATS = async (forcedArchId: string | null = selectedArchetype) => {
    setIsGeneratingATS(true);
    setGenerateError(null);
    try {
      const resume = await generateATSResume(candidateProfileId, job.id, forcedArchId);
      setAtsResume(resume);
      setSelectedArchetype(forcedArchId);
    } catch (err: any) {
      console.error('Failed to generate ATS resume:', err);
      setGenerateError(err.message || 'Failed to assemble ATS resume.');
    } finally {
      setIsGeneratingATS(false);
    }
  };

  const handleGenerateLegacyDrafts = async () => {
    setIsGenerating(true);
    setGenerateError(null);
    setSaveSuccessMessage(null);

    try {
      const result = await generateTailoredDocuments(candidateProfileId, job.id);
      setTailoringData(result);

      // Format resume bullets into editable markdown text
      const bulletSections: string[] = [];
      const rd = result.resume_draft || {};
      bulletSections.push(`### Target Role: ${rd.target_role || rd.target_job_title || job.title}\n`);
      if (rd.tailored_summary) {
        bulletSections.push(`**Professional Summary:**\n${rd.tailored_summary}\n`);
      }
      const skills = rd.highlighted_skills || [];
      if (skills.length > 0) {
        bulletSections.push(`**Highlighted Verified Skills:**\n${skills.join(', ')}\n`);
      }
      bulletSections.push('**Tailored Experience Bullets:**');

      if (rd.bullets && rd.bullets.length > 0) {
        rd.bullets.forEach((b) => {
          const comp = b.source_experience_company ? ` (${b.source_experience_company})` : '';
          const skill = b.relevant_skill ? ` [Skill: ${b.relevant_skill}]` : '';
          bulletSections.push(`• ${b.bullet_point}${comp}${skill}`);
        });
      } else if (rd.tailored_experience_bullets) {
        for (const [company, bullets] of Object.entries(rd.tailored_experience_bullets)) {
          bulletSections.push(`\n*${company}*`);
          (bullets || []).forEach((b) => bulletSections.push(`• ${b}`));
        }
      }
      const formattedResume = bulletSections.join('\n');
      setResumeText(formattedResume);

      // Format cover letter
      const cl = (result.cover_letter || result.cover_letter_draft || {}) as any;
      if (cl.full_text) {
        setCoverLetterText(cl.full_text);
      } else {
        const bodyParagraphs = cl.body_paragraphs || [];
        const formattedCL = [
          `Dear ${cl.recipient || 'Hiring Team'} at ${cl.recipient_company || job.company},`,
          '',
          cl.opening_paragraph || '',
          '',
          ...bodyParagraphs,
          '',
          cl.closing_paragraph || '',
          '',
          cl.call_to_action || '',
          '',
          'Sincerely,',
          'Candidate',
        ]
          .filter((line) => line !== undefined)
          .join('\n');
        setCoverLetterText(formattedCL);
      }

      setAuditResult(result.audit_result);
    } catch (err: any) {
      setGenerateError(err.message || 'Failed to generate tailored application documents.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRunAudit = async () => {
    const textToAudit = activeTab === 'cover_letter' ? coverLetterText : resumeText;
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

  const handlePrintATSResume = () => {
    if (!atsResume) return;

    // Build print HTML document with standard single-column ATS styling
    const skillsHtml = Object.entries(atsResume.skill_categories)
      .map(
        ([cat, items]) =>
          `<div style="display:flex;margin-bottom:2px;"><strong style="min-width:130px;color:#111;">${cat}:</strong> <span>${items.join(', ')}</span></div>`
      )
      .join('');

    const projectsHtml = atsResume.projects
      .map(
        (p) => `
        <div style="margin-bottom:6px;">
          <div style="display:flex;justify-content:space-between;font-weight:bold;font-size:9.5pt;">
            <span>${p.project_name} <span style="font-weight:normal;font-style:italic;color:#4b5563;">— ${p.role_or_title}</span></span>
            <span style="font-size:8.5pt;color:#4b5563;">${p.timeline}</span>
          </div>
          <ul style="margin:2px 0 0 16px;padding:0;">
            ${p.bullets.map((b) => `<li style="font-size:9pt;margin-bottom:2px;line-height:1.28;text-align:justify;">${b}</li>`).join('')}
          </ul>
        </div>
      `
      )
      .join('');

    const educationHtml = atsResume.education
      .map((e) => `<div style="font-size:9pt;color:#111;">${e}</div>`)
      .join('');

    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>${atsResume.candidate_name} - ATS Resume</title>
        <style>
          @page { margin: 0.45in 0.5in; size: letter; }
          body { font-family: Arial, Helvetica, sans-serif; font-size: 9.5pt; line-height: 1.28; color: #111; margin: 0; padding: 0.2in 0.3in; }
          .header { text-align: center; margin-bottom: 8px; }
          .header h1 { font-size: 16pt; margin: 0 0 2px 0; text-transform: uppercase; font-weight: bold; }
          .headline { font-size: 10pt; font-weight: 600; color: #374151; margin-bottom: 3px; }
          .contact { font-size: 8.5pt; color: #4b5563; }
          .section-title { font-size: 9.5pt; font-weight: bold; text-transform: uppercase; border-bottom: 1px solid #111; padding-bottom: 1px; margin: 8px 0 4px 0; }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>${atsResume.candidate_name}</h1>
          <div class="headline">${atsResume.headline}</div>
          <div class="contact">
            ${atsResume.location} • ${atsResume.email}
            ${atsResume.github_url ? `• <a href="${atsResume.github_url}">GitHub</a>` : ''}
            ${atsResume.linkedin_url ? `• <a href="${atsResume.linkedin_url}">LinkedIn</a>` : ''}
          </div>
        </div>
        <div class="section-title">Professional Summary</div>
        <div style="font-size:9pt;text-align:justify;margin-bottom:4px;">${atsResume.summary}</div>
        <div class="section-title">Technical Skills</div>
        <div style="font-size:9pt;margin-bottom:4px;">${skillsHtml}</div>
        <div class="section-title">Key Projects & Systems</div>
        <div>${projectsHtml}</div>
        <div class="section-title">Education</div>
        <div>${educationHtml}</div>
      </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
      printWindow.print();
    }, 250);
  };

  const handleCopy = () => {
    let textToCopy = '';
    if (activeTab === 'ats_resume' && atsResume) {
      const skillsStr = Object.entries(atsResume.skill_categories)
        .map(([c, items]) => `${c}: ${items.join(', ')}`)
        .join('\n');
      const projectsStr = atsResume.projects
        .map((p) => `${p.project_name} (${p.timeline})\n${p.bullets.map((b) => `• ${b}`).join('\n')}`)
        .join('\n\n');
      textToCopy = `${atsResume.candidate_name}\n${atsResume.headline}\n${atsResume.email} | ${atsResume.location}\n\nSUMMARY:\n${atsResume.summary}\n\nSKILLS:\n${skillsStr}\n\nPROJECTS:\n${projectsStr}\n\nEDUCATION:\n${atsResume.education.join('\n')}`;
    } else if (activeTab === 'resume') {
      textToCopy = resumeText;
    } else {
      textToCopy = coverLetterText;
    }

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
      const docType = activeTab === 'cover_letter' ? 'tailored_cover_letter' : 'tailored_resume';
      const content =
        activeTab === 'ats_resume' && atsResume
          ? JSON.stringify(atsResume)
          : activeTab === 'resume'
          ? resumeText
          : coverLetterText;

      await attachDocument(applicationId, {
        doc_type: docType,
        content: content,
        is_approved_by_user: true,
      });

      setSaveSuccessMessage(`Approved & attached ${activeTab === 'cover_letter' ? 'Cover Letter' : 'ATS Resume'} to Application!`);
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
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-5xl overflow-hidden shadow-2xl my-6 flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4 bg-slate-950/70">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg border border-indigo-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight">
                Grounded Document Tailoring Studio
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

        {/* Tab Selector & Pre-Flight Badges */}
        <div className="px-6 py-3 bg-slate-950/40 border-b border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('ats_resume')}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                activeTab === 'ats_resume'
                  ? 'bg-sky-600 text-white shadow'
                  : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              ATS Resume (1-Page PDF)
            </button>
            <button
              onClick={() => setActiveTab('resume')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                activeTab === 'resume'
                  ? 'bg-sky-600 text-white shadow'
                  : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700'
              }`}
            >
              Raw Bullets Draft
            </button>
            <button
              onClick={() => setActiveTab('cover_letter')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                activeTab === 'cover_letter'
                  ? 'bg-sky-600 text-white shadow'
                  : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700'
              }`}
            >
              Cover Letter
            </button>
          </div>

          {/* Pre-Flight Status Badges */}
          {activeTab === 'ats_resume' && atsResume ? (
            <div className="flex items-center gap-2">
              <div
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${
                  atsResume.budget_audit.is_strictly_one_page
                    ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                    : 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                }`}
              >
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>
                  Budget: {atsResume.budget_audit.estimated_total_lines} / 42 lines (Strictly 1-Page)
                </span>
              </div>
              <div className="hidden md:flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-medium bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
                <Layers className="w-3 h-3 text-indigo-400" />
                <span>Lens: {atsResume.archetype_display_name}</span>
              </div>
            </div>
          ) : auditResult ? (
            <div className="flex items-center gap-2">
              {(auditResult.is_grounded ?? auditResult.audit_status === 'PASS') ? (
                <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>Audit PASS: 100% Grounded</span>
                </div>
              ) : (
                <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-300 border border-amber-500/30">
                  <ShieldAlert className="w-4 h-4 text-amber-400" />
                  <span>
                    Flagged {(auditResult.hallucinated_terms || auditResult.unverified_skills_flagged || []).length} unverified skills
                  </span>
                </div>
              )}
              <button
                onClick={handleRunAudit}
                disabled={isAuditing}
                className="text-[11px] text-slate-400 hover:text-sky-300 underline disabled:opacity-50"
              >
                {isAuditing ? 'Auditing...' : 'Re-verify'}
              </button>
            </div>
          ) : null}
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4">
          {generateError && (
            <div className="p-4 bg-red-950/30 border border-red-800/50 rounded-xl text-xs text-red-300 space-y-2">
              <p className="font-semibold flex items-center gap-1.5">
                <AlertCircle className="w-4 h-4" /> Error
              </p>
              <p>{generateError}</p>
            </div>
          )}

          {/* TAB 1: ATS Resume Studio */}
          {activeTab === 'ats_resume' && (
            <div className="space-y-4">
              {/* Lens Switcher Toolbar */}
              <div className="flex items-center justify-between flex-wrap gap-2 p-3 bg-slate-950 border border-slate-800 rounded-xl">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-300 flex items-center gap-1">
                    <Layers className="w-3.5 h-3.5 text-sky-400" /> Choose Role Lens:
                  </span>
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <button
                      onClick={() => handleGenerateATS(null)}
                      disabled={isGeneratingATS}
                      className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                        selectedArchetype === null
                          ? 'bg-sky-600 text-white'
                          : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                      }`}
                    >
                      Auto-Optimized (JD)
                    </button>
                    {availableArchetypes.map((arch) => (
                      <button
                        key={arch.archetype_id}
                        onClick={() => handleGenerateATS(arch.archetype_id)}
                        disabled={isGeneratingATS}
                        className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                          selectedArchetype === arch.archetype_id
                            ? 'bg-sky-600 text-white'
                            : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                        }`}
                        title={arch.description}
                      >
                        {arch.display_name.split(' ')[0]} {arch.archetype_id === 'genai' ? 'LLM' : arch.archetype_id === 'swe' ? 'SWE' : arch.archetype_id === 'ai_eng' ? 'ML' : 'Data'}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="text-[11px] text-slate-400">
                  {isGeneratingATS ? 'Re-angling resume...' : 'Single-column ATS layout'}
                </div>
              </div>

              {/* Live Visual ATS Resume Paper Preview */}
              {isGeneratingATS ? (
                <div className="py-20 flex flex-col items-center justify-center space-y-3">
                  <RotateCw className="w-8 h-8 text-sky-400 animate-spin" />
                  <p className="text-sm font-semibold text-white">Re-angling ATS Resume...</p>
                  <p className="text-xs text-slate-400 text-center max-w-sm">
                    Re-ordering skills, selecting angle-specific verified phrasings, and fitting to 1-page budget.
                  </p>
                </div>
              ) : atsResume ? (
                <div className="bg-white text-gray-900 shadow-xl rounded border border-slate-300 p-8 max-w-3xl mx-auto font-sans text-xs leading-normal select-text">
                  {/* Header */}
                  <div className="text-center pb-2 mb-3 border-b border-gray-200">
                    <h1 className="text-xl font-bold uppercase tracking-wide text-black mb-1">
                      {atsResume.candidate_name}
                    </h1>
                    <div className="text-sm font-semibold text-gray-700 mb-1">
                      {atsResume.headline}
                    </div>
                    <div className="text-xs text-gray-600 flex justify-center flex-wrap gap-2">
                      <span>{atsResume.location}</span>
                      <span>•</span>
                      <span>{atsResume.email}</span>
                      {atsResume.github_url && (
                        <>
                          <span>•</span>
                          <a
                            href={atsResume.github_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-blue-600 hover:underline"
                          >
                            GitHub
                          </a>
                        </>
                      )}
                      {atsResume.linkedin_url && (
                        <>
                          <span>•</span>
                          <a
                            href={atsResume.linkedin_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-blue-600 hover:underline"
                          >
                            LinkedIn
                          </a>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Professional Summary */}
                  <div className="mb-3">
                    <div className="font-bold uppercase tracking-wider text-[11px] text-gray-900 border-b border-gray-800 pb-0.5 mb-1.5">
                      Professional Summary
                    </div>
                    <p className="text-justify text-gray-800 leading-relaxed">
                      {atsResume.summary}
                    </p>
                  </div>

                  {/* Technical Skills */}
                  <div className="mb-3">
                    <div className="font-bold uppercase tracking-wider text-[11px] text-gray-900 border-b border-gray-800 pb-0.5 mb-1.5">
                      Technical Skills
                    </div>
                    <div className="space-y-1">
                      {Object.entries(atsResume.skill_categories).map(([category, skills]) => (
                        <div key={category} className="flex">
                          <span className="font-bold text-gray-900 min-w-[150px]">
                            {category}:
                          </span>
                          <span className="text-gray-800">{skills.join(', ')}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Key Projects */}
                  <div className="mb-3">
                    <div className="font-bold uppercase tracking-wider text-[11px] text-gray-900 border-b border-gray-800 pb-0.5 mb-1.5 flex justify-between items-baseline">
                      <span>Key Projects & Systems</span>
                      <span className="text-[10px] font-normal normal-case text-gray-500 italic">
                        (Flagship showcase prioritized)
                      </span>
                    </div>
                    <div className="space-y-2.5">
                      {atsResume.projects.map((p, idx) => (
                        <div key={idx} className="space-y-1">
                          <div className="flex justify-between items-baseline">
                            <div>
                              <span className="font-bold text-gray-900">{p.project_name}</span>
                              <span className="text-gray-600 italic ml-1">
                                — {p.role_or_title}
                              </span>
                              {p.is_flagship && (
                                <span className="ml-2 px-1.5 py-0.2 rounded text-[10px] bg-sky-100 text-sky-800 font-semibold border border-sky-300">
                                  Flagship
                                </span>
                              )}
                            </div>
                            <span className="text-gray-600 font-medium text-[11px]">
                              {p.timeline}
                            </span>
                          </div>
                          <ul className="list-disc pl-5 space-y-0.5">
                            {p.bullets.map((b, bIdx) => (
                              <li key={bIdx} className="text-gray-800 leading-relaxed text-justify">
                                {b}
                              </li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Education */}
                  <div>
                    <div className="font-bold uppercase tracking-wider text-[11px] text-gray-900 border-b border-gray-800 pb-0.5 mb-1.5">
                      Education
                    </div>
                    <div className="space-y-0.5">
                      {atsResume.education.map((e, idx) => (
                        <div key={idx} className="text-gray-800">
                          {e}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
          )}

          {/* TAB 2 & 3: Legacy Drafts (Raw Bullets & Cover Letter) */}
          {(activeTab === 'resume' || activeTab === 'cover_letter') && (
            <div className="space-y-4">
              {auditResult && !(auditResult.is_grounded ?? auditResult.audit_status === 'PASS') && (
                <div className="p-3 bg-amber-950/30 border border-amber-800/40 rounded-xl text-xs space-y-1">
                  <div className="font-semibold text-amber-300 flex items-center gap-1.5">
                    <ShieldAlert className="w-4 h-4" /> Potential Unverified Skills Detected:
                  </div>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {(auditResult.hallucinated_terms || auditResult.unverified_skills_flagged || []).map((skill, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 rounded bg-amber-900/40 text-amber-200 border border-amber-700/50 text-[11px]"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

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
            </div>
          )}

          {saveSuccessMessage && (
            <div className="p-3 bg-emerald-950/30 border border-emerald-800/40 rounded-xl text-xs text-emerald-300 flex items-center gap-2">
              <FileCheck2 className="w-4 h-4 text-emerald-400" />
              {saveSuccessMessage}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-slate-800 px-6 py-4 bg-slate-950/70">
          <div className="flex items-center gap-2">
            {activeTab === 'ats_resume' ? (
              <button
                onClick={() => handleGenerateATS(selectedArchetype)}
                disabled={isGeneratingATS}
                className="flex items-center gap-2 text-xs text-slate-400 hover:text-white transition-colors"
              >
                <RotateCw className={`w-3.5 h-3.5 ${isGeneratingATS ? 'animate-spin' : ''}`} />
                Re-apply Lens
              </button>
            ) : (
              <button
                onClick={handleGenerateLegacyDrafts}
                disabled={isGenerating}
                className="flex items-center gap-2 text-xs text-slate-400 hover:text-white transition-colors"
              >
                <RotateCw className={`w-3.5 h-3.5 ${isGenerating ? 'animate-spin' : ''}`} />
                Regenerate Draft
              </button>
            )}
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            {/* Download / Print ATS PDF Button */}
            {activeTab === 'ats_resume' && atsResume && (
              <button
                onClick={handlePrintATSResume}
                className="flex-1 sm:flex-initial flex items-center justify-center gap-2 px-4 py-2 text-xs font-semibold rounded-xl bg-sky-600 hover:bg-sky-500 text-white transition-colors shadow-lg shadow-sky-950"
              >
                <Printer className="w-3.5 h-3.5" />
                Download / Print ATS PDF
              </button>
            )}

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
              disabled={isSaving || isGenerating || isGeneratingATS}
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
