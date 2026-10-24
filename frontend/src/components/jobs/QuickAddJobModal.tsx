import React, { useState } from 'react';
import { X, Link2, FileText, Sparkles, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { submitManualJob } from '../../api/jobs';
import { Job } from '../../types/job';

interface QuickAddJobModalProps {
  isOpen: boolean;
  onClose: () => void;
  onJobAdded: (job: Job) => void;
}

export const QuickAddJobModal: React.FC<QuickAddJobModalProps> = ({
  isOpen,
  onClose,
  onJobAdded,
}) => {
  const [mode, setMode] = useState<'url' | 'paste'>('url');
  const [url, setUrl] = useState('');
  const [rawText, setRawText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successJob, setSuccessJob] = useState<Job | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessJob(null);

    if (mode === 'url' && !url.trim()) {
      setErrorMessage('Please enter a valid job posting URL.');
      return;
    }
    if (mode === 'paste' && !rawText.trim()) {
      setErrorMessage('Please paste job description text.');
      return;
    }

    setIsLoading(true);
    try {
      const job = await submitManualJob({
        url: url.trim() || null,
        raw_text: rawText.trim() || null,
      });

      setSuccessJob(job);
      onJobAdded(job);
      setTimeout(() => {
        onClose();
        setUrl('');
        setRawText('');
        setSuccessJob(null);
      }, 1200);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to submit job. Please check the URL or text.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-100 w-full max-w-lg overflow-hidden transition-all">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-blue-100 text-blue-600">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-900">Add Custom Job</h2>
              <p className="text-xs text-slate-500">Import via direct ATS URL or paste job description</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab switch */}
        <div className="flex border-b border-slate-200 px-6 pt-3 gap-4">
          <button
            type="button"
            onClick={() => {
              setMode('url');
              setErrorMessage(null);
            }}
            className={`pb-2 text-xs font-semibold flex items-center gap-1.5 border-b-2 transition-colors ${
              mode === 'url'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Link2 className="w-3.5 h-3.5" />
            <span>Job URL (Greenhouse, Lever, etc.)</span>
          </button>
          <button
            type="button"
            onClick={() => {
              setMode('paste');
              setErrorMessage(null);
            }}
            className={`pb-2 text-xs font-semibold flex items-center gap-1.5 border-b-2 transition-colors ${
              mode === 'paste'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Paste Job Description</span>
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {errorMessage && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}

          {successJob && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>Successfully added: <strong>{successJob.title}</strong> at {successJob.company}!</span>
            </div>
          )}

          {mode === 'url' ? (
            <div className="space-y-2">
              <label className="block text-xs font-medium text-slate-700">
                Job Posting URL
              </label>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://boards.greenhouse.io/stripe/jobs/12345 or https://jobs.lever.co/..."
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all placeholder:text-slate-400"
                disabled={isLoading}
                autoFocus
              />
              <p className="text-[11px] text-slate-400">
                Greenhouse and Lever links are fetched directly via official APIs without web scraping.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Optional Job Application URL
                </label>
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://company.com/apply"
                  className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all placeholder:text-slate-400"
                  disabled={isLoading}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1">
                  Raw Job Description Text
                </label>
                <textarea
                  value={rawText}
                  onChange={(e) => setRawText(e.target.value)}
                  placeholder="Paste the full job responsibilities, company info, and qualifications here..."
                  rows={6}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all placeholder:text-slate-400"
                  disabled={isLoading}
                />
              </div>
            </div>
          )}

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 rounded-xl text-xs font-medium text-slate-600 hover:bg-slate-100 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white transition-all shadow-sm hover:shadow disabled:opacity-50"
            >
              {isLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              <span>{isLoading ? 'Processing...' : 'Import Job'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
