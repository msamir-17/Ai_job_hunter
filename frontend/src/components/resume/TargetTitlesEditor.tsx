import React, { useState } from 'react';
import { Target, Plus, X } from 'lucide-react';
import { Card } from '../ui/Card';

interface TargetTitlesEditorProps {
  targetTitles: string[];
  onTargetTitlesChange: (titles: string[]) => void;
}

export const TargetTitlesEditor: React.FC<TargetTitlesEditorProps> = ({
  targetTitles,
  onTargetTitlesChange,
}) => {
  const [newTitleInput, setNewTitleInput] = useState<string>('');

  const handleAddTitle = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = newTitleInput.trim();
    if (!trimmed) return;
    if (!targetTitles.includes(trimmed)) {
      onTargetTitlesChange([...targetTitles, trimmed]);
    }
    setNewTitleInput('');
  };

  const handleRemoveTitle = (index: number) => {
    const updated = targetTitles.filter((_, i) => i !== index);
    onTargetTitlesChange(updated);
  };

  return (
    <Card className="mb-6">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <Target className="w-4 h-4 text-slate-500" />
          <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
            Target Job Roles ({targetTitles.length})
          </h3>
        </div>
      </div>

      <div className="mb-4 flex flex-wrap gap-1.5">
        {targetTitles.map((title, index) => (
          <div
            key={index}
            className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-100 border border-slate-200 rounded-md text-xs text-slate-800 font-medium"
          >
            <span>{title}</span>
            <button
              type="button"
              onClick={() => handleRemoveTitle(index)}
              className="text-slate-400 hover:text-red-600 transition-colors p-0.5"
              title="Remove"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}

        {targetTitles.length === 0 && (
          <p className="text-xs text-slate-400 italic py-2">
            No target titles inferred. Add target job roles (e.g. AI Engineer, Python Developer) to optimize job matching.
          </p>
        )}
      </div>

      <form onSubmit={handleAddTitle} className="flex gap-2 pt-3 border-t border-slate-100">
        <input
          type="text"
          value={newTitleInput}
          onChange={(e) => setNewTitleInput(e.target.value)}
          placeholder="Add target role (e.g. Lead Software Engineer)..."
          className="flex-1 px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500"
        />
        <button
          type="submit"
          className="px-3.5 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-900 text-white transition-colors flex items-center gap-1.5 shrink-0"
        >
          <Plus className="w-3.5 h-3.5" />
          Add
        </button>
      </form>
    </Card>
  );
};
