import React, { useState } from 'react';
import { Cpu, Plus, X, Edit3, Check } from 'lucide-react';
import { Card } from '../ui/Card';

interface SkillsEditorProps {
  skills: string[];
  onSkillsChange: (skills: string[]) => void;
}

export const SkillsEditor: React.FC<SkillsEditorProps> = ({ skills, onSkillsChange }) => {
  const [newSkillInput, setNewSkillInput] = useState<string>('');
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editingValue, setEditingValue] = useState<string>('');

  const handleAddSkill = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = newSkillInput.trim();
    if (!trimmed) return;
    if (!skills.includes(trimmed)) {
      onSkillsChange([...skills, trimmed]);
    }
    setNewSkillInput('');
  };

  const handleRemoveSkill = (index: number) => {
    const updated = skills.filter((_, i) => i !== index);
    onSkillsChange(updated);
  };

  const startEditing = (index: number, currentVal: string) => {
    setEditingIndex(index);
    setEditingValue(currentVal);
  };

  const saveEditing = (index: number) => {
    const trimmed = editingValue.trim();
    if (trimmed) {
      const updated = [...skills];
      updated[index] = trimmed;
      onSkillsChange(updated);
    } else {
      handleRemoveSkill(index);
    }
    setEditingIndex(null);
    setEditingValue('');
  };

  return (
    <Card className="mb-6">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-slate-500" />
          <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
            Technical Skills ({skills.length})
          </h3>
        </div>
        <span className="text-xs text-slate-400">Click chip to edit</span>
      </div>

      <div className="mb-4 flex flex-wrap gap-1.5">
        {skills.map((skill, index) => {
          const isEditing = editingIndex === index;
          return isEditing ? (
            <div key={index} className="flex items-center gap-1 bg-white border border-blue-500 rounded-lg px-2 py-0.5">
              <input
                type="text"
                value={editingValue}
                onChange={(e) => setEditingValue(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && saveEditing(index)}
                autoFocus
                className="w-28 text-xs bg-transparent text-slate-900 focus:outline-none"
              />
              <button
                type="button"
                onClick={() => saveEditing(index)}
                className="text-emerald-600 hover:text-emerald-800 p-0.5"
                title="Save"
              >
                <Check className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <div
              key={index}
              className="group flex items-center gap-1 px-2.5 py-1 bg-blue-50 border border-blue-200 rounded-md text-xs text-blue-800 transition-colors"
            >
              <span className="font-medium">{skill}</span>
              <button
                type="button"
                onClick={() => startEditing(index, skill)}
                className="text-blue-400 hover:text-blue-700 opacity-0 group-hover:opacity-100 transition-opacity p-0.5"
                title="Edit skill"
              >
                <Edit3 className="w-3 h-3" />
              </button>
              <button
                type="button"
                onClick={() => handleRemoveSkill(index)}
                className="text-blue-400 hover:text-red-600 transition-colors p-0.5"
                title="Remove"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          );
        })}

        {skills.length === 0 && (
          <p className="text-xs text-slate-400 italic py-2">No skills extracted yet. Add technical skills below.</p>
        )}
      </div>

      <form onSubmit={handleAddSkill} className="flex gap-2 pt-3 border-t border-slate-100">
        <input
          type="text"
          value={newSkillInput}
          onChange={(e) => setNewSkillInput(e.target.value)}
          placeholder="Add a skill (e.g. FastAPI, PostgreSQL, PyTorch)..."
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
