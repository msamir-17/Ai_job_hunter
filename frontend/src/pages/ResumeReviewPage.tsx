import React, { useState } from 'react';
import { CandidateProfileResponse } from '../types/candidateProfile';
import { ResumeDraft } from '../types/resume';
import { uploadResume, extractResume, confirmResumeDraft } from '../api/resume';

import { CandidateProfileSelector } from '../components/resume/CandidateProfileSelector';
import { ResumeUploadSection } from '../components/resume/ResumeUploadSection';
import { ExtractionLoadingState } from '../components/resume/ExtractionLoadingState';
import { DraftReviewBanner } from '../components/resume/DraftReviewBanner';
import { BasicInfoEditor } from '../components/resume/BasicInfoEditor';
import { SkillsEditor } from '../components/resume/SkillsEditor';
import { ExperienceEditor } from '../components/resume/ExperienceEditor';
import { EducationEditor } from '../components/resume/EducationEditor';
import { TargetTitlesEditor } from '../components/resume/TargetTitlesEditor';
import { ConfirmationBar } from '../components/resume/ConfirmationBar';
import { ConfirmationSuccessView } from '../components/resume/ConfirmationSuccessView';
import { Alert } from '../components/ui/Alert';
import { RefreshCw, FileText } from 'lucide-react';

export const ResumeReviewPage: React.FC = () => {
  const [currentProfile, setCurrentProfile] = useState<CandidateProfileResponse | null>(null);
  const [resumeId, setResumeId] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  // Loading states
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isExtracting, setIsExtracting] = useState<boolean>(false);
  const [isSubmittingConfirm, setIsSubmittingConfirm] = useState<boolean>(false);

  // Errors
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [extractionError, setExtractionError] = useState<string | null>(null);
  const [confirmError, setConfirmError] = useState<string | null>(null);

  // AI Draft state
  const [draft, setDraft] = useState<ResumeDraft | null>(null);

  // Success state
  const [confirmedProfile, setConfirmedProfile] = useState<CandidateProfileResponse | null>(null);

  const handleUploadAndExtract = async (file: File) => {
    if (!currentProfile) return;

    setUploadError(null);
    setExtractionError(null);
    setConfirmError(null);
    setConfirmedProfile(null);
    setDraft(null);
    setFileName(file.name);

    setIsUploading(true);
    let uploadedResumeId: string | null = null;

    try {
      // Step 1: Upload resume document
      const uploadRes = await uploadResume(currentProfile.id, file);
      uploadedResumeId = uploadRes.id;
      setResumeId(uploadRes.id);
      setIsUploading(false);

      // Step 2: Trigger structured AI extraction
      setIsExtracting(true);
      const extractRes = await extractResume(uploadedResumeId);
      
      // Ensure arrays have fallbacks
      const extractedDraft: ResumeDraft = {
        headline: extractRes.draft.headline || '',
        summary: extractRes.draft.summary || '',
        skills: extractRes.draft.skills || [],
        experience: extractRes.draft.experience || [],
        education: extractRes.draft.education || [],
        target_titles: extractRes.draft.target_titles || [],
      };

      setDraft(extractedDraft);
    } catch (err: any) {
      if (!uploadedResumeId) {
        setUploadError(err.message || 'Failed to upload resume document.');
      } else {
        setExtractionError(err.message || 'Failed to extract structured resume draft.');
      }
    } finally {
      setIsUploading(false);
      setIsExtracting(false);
    }
  };

  const handleRetryExtraction = async () => {
    if (!resumeId) return;
    setExtractionError(null);
    setIsExtracting(true);
    try {
      const extractRes = await extractResume(resumeId);
      setDraft({
        headline: extractRes.draft.headline || '',
        summary: extractRes.draft.summary || '',
        skills: extractRes.draft.skills || [],
        experience: extractRes.draft.experience || [],
        education: extractRes.draft.education || [],
        target_titles: extractRes.draft.target_titles || [],
      });
    } catch (err: any) {
      setExtractionError(err.message || 'Extraction retry failed.');
    } finally {
      setIsExtracting(false);
    }
  };

  const handleConfirmAndSave = async () => {
    if (!resumeId || !draft) return;

    setConfirmError(null);
    setIsSubmittingConfirm(true);

    try {
      // Send candidate-reviewed draft to confirm endpoint
      const updatedProfile = await confirmResumeDraft(resumeId, draft);
      setCurrentProfile(updatedProfile);
      setConfirmedProfile(updatedProfile);
      setDraft(null); // Clear active draft mode after confirmation
    } catch (err: any) {
      // Keep edited draft intact so user can retry!
      setConfirmError(err.message || 'Failed to confirm and merge resume draft.');
    } finally {
      setIsSubmittingConfirm(false);
    }
  };

  const handleUploadAnother = () => {
    setDraft(null);
    setResumeId(null);
    setFileName(null);
    setConfirmedProfile(null);
    setUploadError(null);
    setExtractionError(null);
    setConfirmError(null);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 pb-24">
      {/* Title Header */}
      <div className="border-b border-slate-800 pb-6 mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-sky-500/10 text-sky-400 rounded-lg border border-sky-500/20">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-white">
              Resume Review & Confirmation UI
            </h1>
            <p className="text-xs text-slate-400">
              Human-in-the-Loop AI extraction draft review and Candidate Profile confirmation
            </p>
          </div>
        </div>
      </div>

      {/* Candidate Profile Context Selector */}
      <CandidateProfileSelector
        currentProfile={currentProfile}
        onProfileSelect={(prof) => {
          setCurrentProfile(prof);
          setConfirmedProfile(null);
        }}
      />

      {/* Confirmation Success View */}
      {confirmedProfile ? (
        <ConfirmationSuccessView
          profile={confirmedProfile}
          onUploadAnother={handleUploadAnother}
        />
      ) : (
        <>
          {/* Resume Upload Section */}
          <ResumeUploadSection
            candidateProfileId={currentProfile?.id || null}
            onUploadAndExtract={handleUploadAndExtract}
            isUploading={isUploading}
            error={uploadError}
            onErrorClear={() => setUploadError(null)}
          />

          {/* AI Extraction Loading State */}
          {isExtracting && <ExtractionLoadingState fileName={fileName || undefined} />}

          {/* Extraction Error Alert with Retry */}
          {extractionError && !isExtracting && (
            <Alert variant="error" className="mb-8">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h4 className="font-semibold text-rose-300">Extraction Failed</h4>
                  <p className="text-xs text-rose-200/90">{extractionError}</p>
                </div>
                {resumeId && (
                  <button
                    type="button"
                    onClick={handleRetryExtraction}
                    className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-rose-900/60 hover:bg-rose-800 text-rose-100 transition-colors flex items-center gap-1.5 shrink-0"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    Retry Extraction
                  </button>
                )}
              </div>
            </Alert>
          )}

          {/* Human Review & Edit Form */}
          {draft && !isExtracting && (
            <div className="space-y-6">
              {/* HITL Banner */}
              <DraftReviewBanner />

              {/* Editable Basic Info */}
              <BasicInfoEditor
                headline={draft.headline || ''}
                summary={draft.summary || ''}
                onHeadlineChange={(h) => setDraft({ ...draft, headline: h })}
                onSummaryChange={(s) => setDraft({ ...draft, summary: s })}
              />

              {/* Editable Skills */}
              <SkillsEditor
                skills={draft.skills}
                onSkillsChange={(skills) => setDraft({ ...draft, skills })}
              />

              {/* Editable Work Experience */}
              <ExperienceEditor
                experience={draft.experience}
                onExperienceChange={(experience) => setDraft({ ...draft, experience })}
              />

              {/* Editable Education */}
              <EducationEditor
                education={draft.education}
                onEducationChange={(education) => setDraft({ ...draft, education })}
              />

              {/* Editable Target Titles */}
              <TargetTitlesEditor
                targetTitles={draft.target_titles}
                onTargetTitlesChange={(target_titles) => setDraft({ ...draft, target_titles })}
              />

              {/* Sticky Confirmation Bar */}
              <ConfirmationBar
                onConfirm={handleConfirmAndSave}
                isSubmitting={isSubmittingConfirm}
                error={confirmError}
                onErrorClear={() => setConfirmError(null)}
                onResetDraft={() => {
                  if (window.confirm('Discard edits and reset draft?')) {
                    handleUploadAnother();
                  }
                }}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
};
