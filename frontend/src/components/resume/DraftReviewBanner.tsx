import React from 'react';
import { Info } from 'lucide-react';
import { Badge } from '../ui/Badge';

export const DraftReviewBanner: React.FC = () => {
  return (
    <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-xl">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-amber-900 tracking-tight">
              Draft Review Required
            </h2>
            <Badge variant="draft">UNVERIFIED DRAFT</Badge>
          </div>
          <p className="text-xs text-amber-800 leading-relaxed max-w-3xl">
            This information was extracted from your resume. Review and edit any field below before saving to your verified candidate profile.
          </p>
        </div>

        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white border border-amber-200 text-[11px] text-amber-800 font-medium shrink-0 self-start md:self-auto">
          <Info className="w-3.5 h-3.5 text-amber-600" />
          <span>Extracted draft data</span>
        </div>
      </div>
    </div>
  );
};
