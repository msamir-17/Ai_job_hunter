import React from 'react';
import { FileText, Loader2, AlertCircle } from 'lucide-react';
import { Card } from '../ui/Card';

interface ExtractionLoadingStateProps {
  fileName?: string;
}

export const ExtractionLoadingState: React.FC<ExtractionLoadingStateProps> = ({ fileName }) => {
  return (
    <Card className="mb-8 border-slate-200 bg-white py-12 text-center shadow-sm">
      <div className="max-w-md mx-auto flex flex-col items-center">
        <div className="relative mb-6">
          <div className="p-4 bg-blue-50 text-blue-600 rounded-xl border border-blue-100">
            <FileText className="w-8 h-8" />
          </div>
          <div className="absolute -bottom-1 -right-1 p-1 bg-blue-600 text-white rounded-full">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          </div>
        </div>

        <h3 className="text-base font-bold text-slate-900 mb-1.5">
          Extracting Resume Data
        </h3>
        <p className="text-xs text-slate-500 mb-4 leading-relaxed">
          Analyzing structured text from <span className="font-semibold text-slate-800">{fileName || 'your document'}</span> to prepare an editable draft for your verification.
        </p>

        <div className="px-4 py-2.5 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 font-medium flex items-center gap-2 text-left">
          <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
          <span>Extraction generates an unverified draft. You will review and edit all fields before saving to your profile.</span>
        </div>
      </div>
    </Card>
  );
};

