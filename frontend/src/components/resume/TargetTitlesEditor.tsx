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
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Target className="w-5 h-5 text-amber-400" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Target Job Titles ({targetTitles.length})
          </h3>
        </div>
        <span className="text-xs text-slate-500 font-mono">Job Matching Roles</span>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {targetTitles.map((title, index) => (
          <div
            key={index}
            className="flex items-center gap-2 px-3 py-1 bg-slate-950 border border-slate-800 rounded-lg text-xs text-amber-300 font-medium"
          >
            <span>{title}</span>
            <button
              type="button"
              onClick={() => handleRemoveTitle(index)}
              className="text-slate-500 hover:text-rose-400 transition-colors p-0.5"
              title="Remove target title"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}

        {targetTitles.length === 0 && (
          <p className="text-xs text-slate-500 italic py-2">
            No target titles inferred. Add target job roles (e.g. Staff Engineer, Tech Lead) to optimize job matching.
          </p>
        )}
      </div>

      <form onSubmit={handleAddTitle} className="flex gap-2 pt-2 border-t border-slate-800/80">
        <input
          type="text"
          value={newTitleInput}
          onChange={(e) => setNewTitleInput(e.target.value)}
          placeholder="Add target job title (e.g. Lead Full Stack Developer)..."
          className="flex-1 px-3 py-1.5 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-sky-500"
        />
        <button
          type="submit"
          className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-300 transition-colors flex items-center gap-1.5 shrink-0"
        >
          <Plus className="w-3.5 h-3.5" />
          Add Role
        </button>
      </form>
    </Card>
  );
};
