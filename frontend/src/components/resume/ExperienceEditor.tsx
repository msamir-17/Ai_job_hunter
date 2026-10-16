import React, { useState } from 'react';
import { Briefcase, Plus, Trash2, ChevronDown, ChevronUp, Layers, Award } from 'lucide-react';
import { ExperienceItem } from '../../types/resume';
import { Card } from '../ui/Card';

interface ExperienceEditorProps {
  experience: ExperienceItem[];
  onExperienceChange: (exp: ExperienceItem[]) => void;
}

interface ExperienceRowProps {
  item: ExperienceItem;
  index: number;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onUpdate: (updatedFields: Partial<ExperienceItem>) => void;
  onRemove: () => void;
}

const ExperienceRow: React.FC<ExperienceRowProps> = ({
  item,
  index,
  isExpanded,
  onToggleExpand,
  onUpdate,
  onRemove,
}) => {
  const [newAchInput, setNewAchInput] = useState<string>('');
  const [newTechInput, setNewTechInput] = useState<string>('');

  const handleAddAchievement = () => {
    const trimmed = newAchInput.trim();
    if (!trimmed) return;
    const current = item.achievements || [];
    onUpdate({ achievements: [...current, trimmed] });
    setNewAchInput('');
  };

  const handleRemoveAchievement = (achIdx: number) => {
    const current = item.achievements || [];
    onUpdate({ achievements: current.filter((_, i) => i !== achIdx) });
  };

  const handleAddTechnology = () => {
    const trimmed = newTechInput.trim();
    if (!trimmed) return;
    const current = item.technologies || [];
    if (!current.includes(trimmed)) {
      onUpdate({ technologies: [...current, trimmed] });
    }
    setNewTechInput('');
  };

  const handleRemoveTechnology = (techIdx: number) => {
    const current = item.technologies || [];
    onUpdate({ technologies: current.filter((_, i) => i !== techIdx) });
  };

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg overflow-hidden transition-colors">
      {/* Header bar */}
      <div
        onClick={onToggleExpand}
        className="px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-slate-100/70 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="p-1.5 bg-white border border-slate-200 text-slate-700 rounded-md text-xs font-mono font-semibold">
            #{index + 1}
          </div>
          <div>
            <h4 className="text-xs font-semibold text-slate-900">
              {item.title || 'Untitled Role'}{' '}
              {item.company && <span className="text-slate-500 font-normal">at {item.company}</span>}
            </h4>
            <p className="text-[11px] text-slate-500">
              {item.start_date || 'Start'} – {item.end_date || 'Present'} {item.location && `• ${item.location}`}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onRemove();
            }}
            className="p-1 text-slate-400 hover:text-red-600 rounded transition-colors"
            title="Remove"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          )}
        </div>
      </div>

      {/* Expanded form */}
      {isExpanded && (
        <div className="p-4 border-t border-slate-200 space-y-3 bg-white">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-medium text-slate-600 mb-1">Company</label>
              <input
                type="text"
                value={item.company || ''}
                onChange={(e) => onUpdate({ company: e.target.value })}
                placeholder="e.g. Acme Corp"
                className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-[11px] font-medium text-slate-600 mb-1">Job Title</label>
              <input
                type="text"
                value={item.title || ''}
                onChange={(e) => onUpdate({ title: e.target.value })}
                placeholder="e.g. Senior Software Engineer"
                className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-[11px] font-medium text-slate-600 mb-1">Location</label>
              <input
                type="text"
                value={item.location || ''}
                onChange={(e) => onUpdate({ location: e.target.value })}
                placeholder="e.g. New York, NY (Hybrid)"
                className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500"
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-[11px] font-medium text-slate-600 mb-1">Start Date</label>
                <input
                  type="text"
                  value={item.start_date || ''}
                  onChange={(e) => onUpdate({ start_date: e.target.value })}
                  placeholder="e.g. Jan 2021"
                  className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-slate-600 mb-1">End Date</label>
                <input
                  type="text"
                  value={item.end_date || ''}
                  onChange={(e) => onUpdate({ end_date: e.target.value })}
                  placeholder="e.g. Present"
                  className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-slate-600 mb-1">Description / Summary</label>
            <textarea
              value={item.description || ''}
              onChange={(e) => onUpdate({ description: e.target.value })}
              placeholder="Overview of core duties..."
              rows={2}
              className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Key Achievements */}
          <div className="space-y-2 pt-2 border-t border-slate-100">
            <label className="text-[11px] font-medium text-slate-700 flex items-center gap-1.5">
              <Award className="w-3.5 h-3.5 text-slate-500" />
              Key Achievements ({item.achievements?.length || 0})
            </label>

            {item.achievements && item.achievements.length > 0 && (
              <ul className="space-y-1">
                {item.achievements.map((ach, achIdx) => (
                  <li key={achIdx} className="flex items-start justify-between gap-2 text-xs text-slate-700 bg-slate-50 p-2 rounded border border-slate-200">
                    <span className="leading-snug">• {ach}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveAchievement(achIdx)}
                      className="text-slate-400 hover:text-red-600 shrink-0 p-0.5"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </li>
                ))}
              </ul>
            )}

            <div className="flex gap-2">
              <input
                type="text"
                value={newAchInput}
                onChange={(e) => setNewAchInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddAchievement();
                  }
                }}
                placeholder="Add accomplishment (e.g. Reduced API latency by 40%)..."
                className="flex-1 px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500"
              />
              <button
                type="button"
                onClick={handleAddAchievement}
                className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 text-white hover:bg-slate-900"
              >
                Add
              </button>
            </div>
          </div>

          {/* Technologies Used */}
          <div className="space-y-2 pt-2 border-t border-slate-100">
            <label className="text-[11px] font-medium text-slate-700 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-slate-500" />
              Technologies ({item.technologies?.length || 0})
            </label>

            <div className="flex flex-wrap gap-1">
              {item.technologies?.map((tech, techIdx) => (
                <span
                  key={techIdx}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-[11px] text-slate-700"
                >
                  {tech}
                  <button
                    type="button"
                    onClick={() => handleRemoveTechnology(techIdx)}
                    className="text-slate-400 hover:text-red-600"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                value={newTechInput}
                onChange={(e) => setNewTechInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddTechnology();
                  }
                }}
                placeholder="Add technology (e.g. Docker, Redis)..."
                className="flex-1 px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500"
              />
              <button
                type="button"
                onClick={handleAddTechnology}
                className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 text-white hover:bg-slate-900"
              >
                Add
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export const ExperienceEditor: React.FC<ExperienceEditorProps> = ({
  experience,
  onExperienceChange,
}) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0);

  const handleUpdateItem = (index: number, updatedFields: Partial<ExperienceItem>) => {
    const updated = [...experience];
    updated[index] = { ...updated[index], ...updatedFields };
    onExperienceChange(updated);
  };

  const handleAddExperience = () => {
    const newItem: ExperienceItem = {
      company: '',
      title: '',
      location: '',
      start_date: '',
      end_date: '',
      description: '',
      achievements: [],
      technologies: [],
    };
    onExperienceChange([...experience, newItem]);
    setExpandedIndex(experience.length);
  };

  const handleRemoveExperience = (index: number) => {
    const updated = experience.filter((_, i) => i !== index);
    onExperienceChange(updated);
    if (expandedIndex === index) {
      setExpandedIndex(null);
    }
  };

  return (
    <Card className="mb-6">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <Briefcase className="w-4 h-4 text-slate-500" />
          <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
            Work Experience ({experience.length})
          </h3>
        </div>
        <button
          type="button"
          onClick={handleAddExperience}
          className="px-3 py-1.5 text-xs font-medium rounded-lg bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 transition-colors flex items-center gap-1.5"
        >
          <Plus className="w-3.5 h-3.5" />
          Add Experience
        </button>
      </div>

      {experience.length === 0 ? (
        <p className="text-xs text-slate-400 italic py-4 text-center">
          No experience entries extracted. Click "Add Experience" to add entries manually.
        </p>
      ) : (
        <div className="space-y-3">
          {experience.map((item, index) => (
            <ExperienceRow
              key={index}
              item={item}
              index={index}
              isExpanded={expandedIndex === index}
              onToggleExpand={() => setExpandedIndex(expandedIndex === index ? null : index)}
              onUpdate={(fields) => handleUpdateItem(index, fields)}
              onRemove={() => handleRemoveExperience(index)}
            />
          ))}
        </div>
      )}
    </Card>
  );
};
