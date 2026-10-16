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
    <div className="sticky bottom-6 z-40 p-4 bg-white/95 border border-slate-300 rounded-xl backdrop-blur-md shadow-lg">
      {error && (
        <Alert variant="error" className="mb-3" onDismiss={onErrorClear}>
          {error}
        </Alert>
      )}

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-2.5">
          <div className="p-1.5 bg-amber-50 text-amber-600 rounded-md border border-amber-200 shrink-0 mt-0.5">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-semibold text-slate-800 uppercase tracking-wide">
              Human Verification Required
            </h4>
            <p className="text-xs text-slate-500">
              Only confirm verified information. Confirmed facts will merge into your candidate profile.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0 self-end md:self-auto">
          {onResetDraft && (
            <button
              type="button"
              onClick={onResetDraft}
              disabled={isSubmitting}
              className="px-3.5 py-2 text-xs font-medium rounded-lg bg-white hover:bg-slate-50 border border-slate-200 text-slate-600 transition-colors disabled:opacity-50"
            >
              Discard Draft
            </button>
          )}

          <button
            type="button"
            onClick={onConfirm}
            disabled={isSubmitting}
            className="px-4 py-2 text-xs font-medium rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition-colors disabled:opacity-50 flex items-center gap-1.5 shadow-sm"
          >
            {isSubmitting ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Saving to Profile...</span>
              </>
            ) : (
              <>
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Confirm & Save to Profile</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
