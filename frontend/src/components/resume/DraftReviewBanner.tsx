import React from 'react';
import { ShieldAlert, Info } from 'lucide-react';
import { Badge } from '../ui/Badge';

export const DraftReviewBanner: React.FC = () => {
  return (
    <div className="mb-6 p-5 bg-gradient-to-r from-amber-950/40 via-amber-900/20 to-slate-900 border border-amber-500/40 rounded-xl backdrop-blur">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="p-2.5 bg-amber-500/10 text-amber-400 rounded-lg border border-amber-500/30 shrink-0 mt-0.5">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-base font-bold text-white tracking-tight">
                AI-Generated Draft — Review Required
              </h2>
              <Badge variant="draft">UNVERIFIED DRAFT</Badge>
            </div>
            <p className="text-xs text-amber-200/90 leading-relaxed max-w-3xl">
              This information was extracted from your resume by AI. Review and edit any field below before saving it to your verified candidate profile.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-300 font-medium shrink-0 self-start md:self-auto">
          <Info className="w-3.5 h-3.5 text-amber-400" />
          <span>AI suggestion ≠ verified profile data</span>
        </div>
      </div>
    </div>
  );
};
