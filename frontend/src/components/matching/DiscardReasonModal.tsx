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
  { code: 'wrong_seniority', label: 'Seniority Mismatch (Too junior or senior)' },
  { code: 'wrong_location', label: 'Location Mismatch (Incompatible location)' },
  { code: 'salary_too_low', label: 'Compensation Below Target' },
  { code: 'tech_stack_mismatch', label: 'Tech Stack Mismatch (Unwanted tools)' },
  { code: 'culture_fit', label: 'Role Alignment' },
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
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white border border-slate-200 rounded-xl max-w-lg w-full p-6 shadow-xl space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-slate-100 text-slate-700 rounded-lg border border-slate-200">
              <ThumbsDown className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Discard Job</h3>
              <p className="text-xs text-slate-500 line-clamp-1">{job.title} at {job.company}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-md transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Informational callout */}
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 flex items-start gap-2.5 text-xs text-slate-600">
          <AlertCircle className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
          <span>
            Recording your reason adapts recommendation preferences, steering future job suggestions away from similar roles.
          </span>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-3.5 text-xs">
          <div>
            <label className="block font-semibold text-slate-700 mb-1.5">Primary Reason</label>
            <div className="space-y-1">
              {REASONS.map((r) => (
                <label
                  key={r.code}
                  className={`flex items-center gap-2 p-2 rounded-lg border cursor-pointer transition-colors ${
                    selectedReason === r.code
                      ? 'bg-red-50 border-red-200 text-red-900'
                      : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <input
                    type="radio"
                    name="discard_reason"
                    value={r.code}
                    checked={selectedReason === r.code}
                    onChange={(e) => setSelectedReason(e.target.value)}
                    className="accent-red-600"
                  />
                  <span className="font-medium text-xs">{r.label}</span>
                </label>
              ))}
            </div>
          </div>

          {selectedReason === 'tech_stack_mismatch' && (
            <div>
              <label className="block font-medium text-slate-700 mb-1">
                Disliked Technology / Tool (Optional)
              </label>
              <input
                type="text"
                value={dislikedSkill}
                onChange={(e) => setDislikedSkill(e.target.value)}
                placeholder="e.g. PHP, Ruby, Angular..."
                className="w-full bg-white border border-slate-300 rounded-lg px-3 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500"
              />
            </div>
          )}

          <div>
            <label className="block font-medium text-slate-700 mb-1">
              Additional Notes (Optional)
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Why this role does not match your preferences..."
              className="w-full bg-white border border-slate-300 rounded-lg p-2.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500 resize-none font-sans"
            />
          </div>

          {/* Action buttons */}
          <div className="pt-2 border-t border-slate-100 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-600 hover:text-slate-800 bg-white border border-slate-200 hover:bg-slate-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-1.5 rounded-lg text-xs font-medium bg-red-600 hover:bg-red-700 text-white transition-colors disabled:opacity-50 flex items-center gap-1.5"
            >
              <Check className="w-3.5 h-3.5" />
              <span>{isSubmitting ? 'Updating...' : 'Discard Job'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
