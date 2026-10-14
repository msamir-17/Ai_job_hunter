import React, { useState } from 'react';
import { X, ThumbsDown, AlertCircle, Check } from 'lucide-react';
import { Job } from '../../types/job';

interface DiscardReasonModalProps {
  job: Job;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (reasonCode: string, notes?: string, dislikedSkill?: string) => Promise<void>;
  isSubmitting: boolean;
}

const REASONS = [
  { code: 'wrong_seniority', label: 'Seniority Mismatch (Too junior or senior for role)' },
  { code: 'wrong_location', label: 'Location Mismatch (Not remote or incompatible location)' },
  { code: 'salary_too_low', label: 'Compensation Below Target' },
  { code: 'tech_stack_mismatch', label: 'Tech Stack Mismatch (Unwanted tools or frameworks)' },
  { code: 'culture_fit', label: 'Company or Role Alignment' },
  { code: 'other', label: 'Other Reason' },
];

export const DiscardReasonModal: React.FC<DiscardReasonModalProps> = ({
  job,
  isOpen,
  onClose,
  onConfirm,
  isSubmitting,
}) => {
  const [selectedReason, setSelectedReason] = useState<string>('tech_stack_mismatch');
  const [dislikedSkill, setDislikedSkill] = useState<string>('');
  const [notes, setNotes] = useState<string>('');

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onConfirm(selectedReason, notes.trim() || undefined, dislikedSkill.trim() || undefined);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-rose-500/10 text-rose-400 rounded-xl border border-rose-500/20">
              <ThumbsDown className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Discard Job Recommendation</h3>
              <p className="text-xs text-slate-400 line-clamp-1">{job.title} at {job.company}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Informational callout */}
        <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-3 flex items-start gap-2.5 text-xs text-slate-300">
          <AlertCircle className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />
          <span>
            Recording your reason adapts your search vector using the Rocchio algorithm, steering future AI recommendations away from similar jobs.
          </span>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-slate-300 mb-2">Select Primary Discard Reason</label>
            <div className="space-y-1.5">
              {REASONS.map((r) => (
                <label
                  key={r.code}
                  className={`flex items-center gap-2.5 p-2.5 rounded-xl border cursor-pointer transition-all ${
                    selectedReason === r.code
                      ? 'bg-rose-950/20 border-rose-500/50 text-rose-200'
                      : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <input
                    type="radio"
                    name="discard_reason"
                    value={r.code}
                    checked={selectedReason === r.code}
                    onChange={(e) => setSelectedReason(e.target.value)}
                    className="accent-rose-500"
                  />
                  <span className="font-medium">{r.label}</span>
                </label>
              ))}
            </div>
          </div>

          {selectedReason === 'tech_stack_mismatch' && (
            <div>
              <label className="block font-semibold text-slate-300 mb-1">
                Disliked Technology / Skill (Optional)
              </label>
              <input
                type="text"
                value={dislikedSkill}
                onChange={(e) => setDislikedSkill(e.target.value)}
                placeholder="e.g. PHP, Ruby, Angular, COBOL..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-rose-500"
              />
            </div>
          )}

          <div>
            <label className="block font-semibold text-slate-300 mb-1">
              Additional Notes (Optional)
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Provide context on why this role does not match your target preferences..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-rose-500 resize-none font-sans"
            />
          </div>

          {/* Action buttons */}
          <div className="pt-3 border-t border-slate-800 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white bg-slate-950 border border-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-5 py-2 rounded-xl text-xs font-bold bg-rose-600 hover:bg-rose-500 text-white transition-all disabled:opacity-50 flex items-center gap-1.5 shadow-lg shadow-rose-600/20"
            >
              <Check className="w-4 h-4" />
              {isSubmitting ? 'Updating AI Vector...' : 'Confirm Discard'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
