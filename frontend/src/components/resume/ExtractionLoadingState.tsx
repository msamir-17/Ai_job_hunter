import React from 'react';
import { Bot, Sparkles, Loader2 } from 'lucide-react';
import { Card } from '../ui/Card';

interface ExtractionLoadingStateProps {
  fileName?: string;
}

export const ExtractionLoadingState: React.FC<ExtractionLoadingStateProps> = ({ fileName }) => {
  return (
    <Card className="mb-8 border-sky-500/30 bg-slate-900/90 py-12 text-center">
      <div className="max-w-md mx-auto flex flex-col items-center">
        <div className="relative mb-6">
          <div className="p-4 bg-sky-500/10 text-sky-400 rounded-2xl border border-sky-500/20 animate-pulse">
            <Bot className="w-10 h-10" />
          </div>
          <div className="absolute -bottom-1 -right-1 p-1.5 bg-sky-600 text-white rounded-full">
            <Loader2 className="w-4 h-4 animate-spin" />
          </div>
        </div>

        <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
          Extracting your resume...
          <Sparkles className="w-4 h-4 text-sky-400" />
        </h3>
        <p className="text-xs text-slate-300 mb-4 leading-relaxed">
          AI is analyzing raw text from <span className="font-semibold text-sky-300">{fileName || 'your document'}</span> and parsing it into a structured candidate draft for your review.
        </p>

        <div className="px-4 py-2 bg-amber-500/10 border border-amber-500/20 rounded-lg text-[11px] text-amber-300 font-medium">
          ⚠️ Note: AI extraction generates an unverified draft. You will review and edit all fields before saving to your profile.
        </div>
      </div>
    </Card>
  );
};
