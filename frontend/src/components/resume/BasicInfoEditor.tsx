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
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-100">
        <UserCheck className="w-4 h-4 text-slate-500" />
        <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
          Basic Profile Information
        </h3>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">
            Professional Headline
          </label>
          <input
            type="text"
            value={headline}
            onChange={(e) => onHeadlineChange(e.target.value)}
            placeholder="e.g. Senior Software Engineer | Distributed Systems & AI"
            className="w-full px-3 py-2 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500"
          />
          <p className="text-[11px] text-slate-500 mt-1">
            Concise title summarizing your professional identity.
          </p>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-700 mb-1">
            Professional Summary
          </label>
          <textarea
            value={summary}
            onChange={(e) => onSummaryChange(e.target.value)}
            placeholder="e.g. Accomplished software engineer with experience building scalable backend services..."
            rows={4}
            className="w-full px-3 py-2 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500 leading-relaxed"
          />
          <p className="text-[11px] text-slate-500 mt-1">
            Executive summary of your key expertise and domain knowledge.
          </p>
        </div>
      </div>
    </Card>
  );
};
