import React from 'react';
import { UserCheck } from 'lucide-react';
import { Card } from '../ui/Card';

interface BasicInfoEditorProps {
  headline: string;
  summary: string;
  onHeadlineChange: (headline: string) => void;
  onSummaryChange: (summary: string) => void;
}

export const BasicInfoEditor: React.FC<BasicInfoEditorProps> = ({
  headline,
  summary,
  onHeadlineChange,
  onSummaryChange,
}) => {
  return (
    <Card className="mb-6">
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-800">
        <UserCheck className="w-5 h-5 text-sky-400" />
        <h3 className="text-sm font-bold text-white uppercase tracking-wider">
          Basic Profile Information
        </h3>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            Professional Headline
          </label>
          <input
            type="text"
            value={headline}
            onChange={(e) => onHeadlineChange(e.target.value)}
            placeholder="e.g. Senior Staff Software Engineer | Distributed Systems & AI"
            className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-sky-500"
          />
          <p className="text-[11px] text-slate-500 mt-1">
            Concise title summarizing your professional identity.
          </p>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            Professional Summary
          </label>
          <textarea
            value={summary}
            onChange={(e) => onSummaryChange(e.target.value)}
            placeholder="e.g. Accomplished software engineer with 8+ years building scalable microservices..."
            rows={4}
            className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-sky-500 leading-relaxed"
          />
          <p className="text-[11px] text-slate-500 mt-1">
            Comprehensive executive summary of your key expertise and domain knowledge.
          </p>
        </div>
      </div>
    </Card>
  );
};
