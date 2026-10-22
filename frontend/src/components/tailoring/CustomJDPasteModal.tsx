import React, { useState } from 'react';
import {
  X,
  Sparkles,
  ClipboardPaste,
  Building2,
  Briefcase,
  Layers,
  Languages,
  AlertCircle,
  Loader2,
} from 'lucide-react';
import { tailorCustomJD } from '../../api/tailoring';
import { CustomJDTailoringResponse } from '../../types/tailoring';

interface CustomJDPasteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (data: CustomJDTailoringResponse) => void;
}

export const CustomJDPasteModal: React.FC<CustomJDPasteModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [jobTitle, setJobTitle] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [archetypeId, setArchetypeId] = useState('genai');
  const [languageTone, setLanguageTone] = useState<'hinglish' | 'english'>('hinglish');
  const [saveToTracker, setSaveToTracker] = useState(true);

  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handlePasteFromClipboard = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setJobDescription(text);
      }
    } catch (err) {
      console.warn('Could not read from clipboard:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!jobDescription.trim() || jobDescription.trim().length < 20) {
      setErrorMessage('Please paste a job description with at least 20 characters.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const result = await tailorCustomJD({
        job_title: jobTitle.trim() || undefined,
        company_name: companyName.trim() || undefined,
        job_description: jobDescription.trim(),
        archetype_id: archetypeId,
        language_tone: languageTone,
        save_to_tracker: saveToTracker,
      });

      onSuccess(result);
      onClose();
    } catch (err: any) {
      console.error('Failed to tailor custom JD:', err);
      setErrorMessage(
        err.message || 'Failed to process external job description. Ensure the backend server is running.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-800/50">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 rounded-xl">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                  Tailor External Job Description
                </h2>
                <span className="text-[11px] font-semibold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 px-2 py-0.5 rounded-full">
                  Recruiter & ATS Suite
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Paste any external JD to instantly run a 6-sec recruiter audit, assemble a 1-page ATS resume, and generate cold outreach.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content / Form */}
        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto space-y-5 flex-1">
          {errorMessage && (
            <div className="p-3.5 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 rounded-xl text-xs text-rose-700 dark:text-rose-300 flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Role & Company Quick Fields */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1.5">
                <Briefcase className="w-3.5 h-3.5 text-slate-400" />
                Target Job Title <span className="text-slate-400 font-normal">(Optional)</span>
              </label>
              <input
                type="text"
                placeholder="Auto-extracted if left empty"
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                className="w-full text-xs px-3 py-2.5 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1.5">
                <Building2 className="w-3.5 h-3.5 text-slate-400" />
                Company Name <span className="text-slate-400 font-normal">(Optional)</span>
              </label>
              <input
                type="text"
                placeholder="Auto-extracted if left empty"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                className="w-full text-xs px-3 py-2.5 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-900 dark:text-white"
              />
            </div>
          </div>

          {/* Archetype & Tone Selectors */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-slate-400" />
                Resume Archetype Lens
              </label>
              <select
                value={archetypeId}
                onChange={(e) => setArchetypeId(e.target.value)}
                className="w-full text-xs px-3 py-2.5 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-900 dark:text-white"
              >
                <option value="genai">⚡ Generative AI & LLM Systems</option>
                <option value="ai_eng">🤖 AI / Machine Learning Engineer</option>
                <option value="swe">🛠️ Software / Backend Engineer</option>
                <option value="data">📊 Data Platform & Analytics</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1.5">
                <Languages className="w-3.5 h-3.5 text-slate-400" />
                Recruiter Feedback Tone
              </label>
              <select
                value={languageTone}
                onChange={(e) => setLanguageTone(e.target.value as 'hinglish' | 'english')}
                className="w-full text-xs px-3 py-2.5 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-900 dark:text-white"
              >
                <option value="hinglish">🇮🇳 Hinglish (Brutal, crisp coaching)</option>
                <option value="english">🌐 English (Formal executive critique)</option>
              </select>
            </div>
          </div>

          {/* Raw JD Textarea */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Job Description Text <span className="text-rose-500">*</span>
              </label>
              <button
                type="button"
                onClick={handlePasteFromClipboard}
                className="text-xs text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 font-medium flex items-center gap-1"
              >
                <ClipboardPaste className="w-3.5 h-3.5" />
                Paste from Clipboard
              </button>
            </div>
            <textarea
              rows={8}
              required
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste full job posting here (e.g. from LinkedIn, Lever, Greenhouse, Workday)..."
              className="w-full text-xs p-3.5 font-mono bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-900 dark:text-white leading-relaxed resize-y"
            />
            <div className="flex items-center justify-between mt-1 text-[11px] text-slate-400">
              <span>Smart parser will automatically identify requirements and technical stack</span>
              <span>{jobDescription.length} characters</span>
            </div>
          </div>

          {/* Save to Tracker Checkbox */}
          <div className="flex items-center gap-2 pt-1">
            <input
              type="checkbox"
              id="save-to-tracker"
              checked={saveToTracker}
              onChange={(e) => setSaveToTracker(e.target.checked)}
              className="w-4 h-4 text-indigo-600 border-slate-300 rounded focus:ring-indigo-500"
            />
            <label htmlFor="save-to-tracker" className="text-xs text-slate-700 dark:text-slate-300 cursor-pointer select-none">
              Save this external role to my <strong>Application Tracker</strong> (Status: Saved)
            </label>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-200 dark:border-slate-800">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2.5 text-xs font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !jobDescription.trim()}
              className="flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl shadow-sm transition-all"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing & Tailoring...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Run Recruiter Audit & Tailor Resume
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
