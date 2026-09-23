import React from 'react';
import { ShieldCheck, RefreshCw, AlertTriangle } from 'lucide-react';
import { Alert } from '../ui/Alert';

interface ConfirmationBarProps {
  onConfirm: () => Promise<void>;
  isSubmitting: boolean;
  error: string | null;
  onErrorClear: () => void;
  onResetDraft?: () => void;
}

export const ConfirmationBar: React.FC<ConfirmationBarProps> = ({
  onConfirm,
  isSubmitting,
  error,
  onErrorClear,
  onResetDraft,
}) => {
  return (
    <div className="sticky bottom-6 z-40 p-5 bg-slate-900/95 border border-sky-500/30 rounded-2xl backdrop-blur-md shadow-2xl shadow-slate-950">
      {error && (
        <Alert variant="error" className="mb-4" onDismiss={onErrorClear}>
          {error}
        </Alert>
      )}

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg border border-emerald-500/20 shrink-0 mt-0.5">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-0.5">
              Human-in-the-Loop Explicit Confirmation
            </h4>
            <p className="text-xs text-slate-300">
              Only confirm information you have reviewed and verified. Confirmed information will be merged into your verified candidate profile.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 shrink-0 self-end md:self-auto">
          {onResetDraft && (
            <button
              type="button"
              onClick={onResetDraft}
              disabled={isSubmitting}
              className="px-4 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors disabled:opacity-50"
            >
              Discard / Reset
            </button>
          )}

          <button
            type="button"
            onClick={onConfirm}
            disabled={isSubmitting}
            className="px-6 py-2.5 text-xs font-bold rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white transition-all shadow-lg shadow-emerald-950 disabled:opacity-50 flex items-center gap-2"
          >
            {isSubmitting ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Merging into Profile...
              </>
            ) : (
              <>
                <ShieldCheck className="w-4 h-4 text-emerald-200" />
                Confirm & Save to Profile
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
