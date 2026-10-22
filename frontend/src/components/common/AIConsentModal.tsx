import React, { useState, useEffect } from 'react';
import { ShieldCheck, ExternalLink, Sparkles, Check, X, ShieldAlert } from 'lucide-react';
import { getLLMProviderInfo, LLMProviderInfo } from '../../api/settings';

interface AIConsentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConsent: () => void;
}

const CONSENT_STORAGE_KEY = 'ai_job_hunter_llm_consent';

export function hasUserGivenAIConsent(): boolean {
  try {
    return localStorage.getItem(CONSENT_STORAGE_KEY) === 'true';
  } catch {
    return false;
  }
}

export function saveUserAIConsent(): void {
  try {
    localStorage.setItem(CONSENT_STORAGE_KEY, 'true');
  } catch {
    // Ignore localStorage failures
  }
}

export const AIConsentModal: React.FC<AIConsentModalProps> = ({
  isOpen,
  onClose,
  onConsent,
}) => {
  const [providerInfo, setProviderInfo] = useState<LLMProviderInfo | null>(null);
  const [agreed, setAgreed] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (isOpen) {
      setIsLoading(true);
      getLLMProviderInfo()
        .then((info) => setProviderInfo(info))
        .catch(() => {
          setProviderInfo({
            active_provider: 'gemini',
            display_name: 'Google Gemini',
            policy_url: 'https://ai.google.dev/terms',
            privacy_notice:
              'Resume text and job descriptions are processed by Google AI APIs for skill extraction and semantic matching.',
            is_third_party: true,
          });
        })
        .finally(() => setIsLoading(false));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleConfirm = () => {
    if (!agreed) return;
    saveUserAIConsent();
    onConsent();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div
        className="bg-white rounded-2xl shadow-2xl max-w-lg w-full border border-slate-100 overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-labelledby="consent-title"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 px-6 py-5 text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/10 rounded-xl backdrop-blur-md">
              <Sparkles className="w-6 h-6 text-yellow-300" />
            </div>
            <div>
              <h2 id="consent-title" className="text-lg font-bold">
                AI Processing Disclosure
              </h2>
              <p className="text-xs text-blue-100">
                Transparent data handling before AI parsing & tailoring
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">
          <div className="p-3.5 bg-blue-50/70 border border-blue-100 rounded-xl flex items-start gap-3">
            <ShieldCheck className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
            <div className="text-xs text-slate-700 leading-relaxed">
              <span className="font-semibold text-slate-900">Privacy Notice: </span>
              To extract structured candidate facts and tailor resumes to job descriptions,
              your resume text is processed using our active third-party AI provider:{' '}
              <span className="inline-block font-semibold px-2 py-0.5 bg-blue-100 text-blue-800 rounded-md">
                {isLoading ? 'Loading provider...' : providerInfo ? providerInfo.display_name : 'AI Provider'}
              </span>
            </div>
          </div>

          <div className="text-xs text-slate-600 space-y-2 leading-relaxed">
            <p>
              {providerInfo?.privacy_notice ||
                'Your resume text is sent securely to the AI provider solely to extract profile skills, experience, and tailor application documents.'}
            </p>
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/60 text-slate-700 flex items-center justify-between">
              <span className="font-medium text-xs">Provider Terms & Privacy Policy</span>
              {providerInfo?.policy_url && (
                <a
                  href={providerInfo.policy_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800 hover:underline"
                >
                  View Policy
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              )}
            </div>
          </div>

          <div className="p-3 bg-amber-50/80 border border-amber-200 rounded-xl flex items-start gap-2.5">
            <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div className="text-[11px] text-amber-800 leading-relaxed">
              <strong>Zero-Fabrication Guardrail:</strong> AI suggestions are strictly verified against
              your confirmed candidate profile. You retain full review and approval control over every generated document.
            </div>
          </div>

          {/* Consent Checkbox */}
          <label className="flex items-start gap-3 pt-2 cursor-pointer select-none">
            <input
              type="checkbox"
              id="ai-consent-checkbox"
              checked={agreed}
              onChange={(e) => setAgreed(e.target.checked)}
              className="mt-0.5 w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500 cursor-pointer"
            />
            <span className="text-xs text-slate-800 font-medium">
              I understand and consent to having my resume text processed by{' '}
              {providerInfo ? providerInfo.display_name : 'the third-party AI provider'} for parsing,
              scoring, and tailoring.
            </span>
          </label>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-100 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 hover:bg-slate-200/60 rounded-xl transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={!agreed}
            onClick={handleConfirm}
            className={`px-5 py-2 text-xs font-semibold rounded-xl flex items-center gap-1.5 transition-all ${
              agreed
                ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-md shadow-blue-500/20 cursor-pointer'
                : 'bg-slate-200 text-slate-400 cursor-not-allowed'
            }`}
          >
            <Check className="w-4 h-4" />
            Accept & Continue
          </button>
        </div>
      </div>
    </div>
  );
};
