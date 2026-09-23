import React, { useState } from 'react';
import { Briefcase, Plus, Trash2, ChevronDown, ChevronUp, Layers, Award } from 'lucide-react';
import { ExperienceItem } from '../../types/resume';
import { Card } from '../ui/Card';

interface ExperienceEditorProps {
  experience: ExperienceItem[];
  onExperienceChange: (exp: ExperienceItem[]) => void;
}

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

  // Achievement bullet management
  const handleAddAchievement = (expIndex: number, text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    const current = experience[expIndex].achievements || [];
    handleUpdateItem(expIndex, { achievements: [...current, trimmed] });
  };

  const handleRemoveAchievement = (expIndex: number, achIndex: number) => {
    const current = experience[expIndex].achievements || [];
    handleUpdateItem(expIndex, { achievements: current.filter((_, i) => i !== achIndex) });
  };

  // Tech stack tag management
  const handleAddTechnology = (expIndex: number, text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    const current = experience[expIndex].technologies || [];
    if (!current.includes(trimmed)) {
      handleUpdateItem(expIndex, { technologies: [...current, trimmed] });
    }
  };

  const handleRemoveTechnology = (expIndex: number, techIndex: number) => {
    const current = experience[expIndex].technologies || [];
    handleUpdateItem(expIndex, { technologies: current.filter((_, i) => i !== techIndex) });
  };

  return (
    <Card className="mb-6">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Briefcase className="w-5 h-5 text-sky-400" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Work Experience ({experience.length})
          </h3>
        </div>
        <button
          type="button"
          onClick={handleAddExperience}
          className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-sky-300 transition-colors flex items-center gap-1.5"
        >
          <Plus className="w-3.5 h-3.5" />
          Add Experience
        </button>
      </div>

      {experience.length === 0 ? (
        <p className="text-xs text-slate-500 italic py-4 text-center">
          No experience entries extracted. Click "Add Experience" to add entries manually.
        </p>
      ) : (
        <div className="space-y-4">
          {experience.map((item, index) => {
            const isExpanded = expandedIndex === index;
            const [newAchInput, setNewAchInput] = useState<string>('');
            const [newTechInput, setNewTechInput] = useState<string>('');

            return (
              <div
                key={index}
                className="bg-slate-950/80 border border-slate-800 rounded-xl overflow-hidden transition-colors"
              >
                {/* Header bar */}
                <div
                  onClick={() => setExpandedIndex(isExpanded ? null : index)}
                  className="px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-slate-900/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-slate-900 border border-slate-800 text-sky-400 rounded-lg text-xs font-bold font-mono">
                      #{index + 1}
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-white">
                        {item.title || 'Untitled Role'}{' '}
                        {item.company && <span className="text-slate-400 font-normal">at {item.company}</span>}
                      </h4>
                      <p className="text-[11px] text-slate-500">
                        {item.start_date || 'Start'} - {item.end_date || 'Present'} {item.location && `• ${item.location}`}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveExperience(index);
                      }}
                      className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-rose-950/40 rounded-lg transition-colors"
                      title="Remove entry from draft review"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    )}
                  </div>
                </div>

                {/* Expanded edit form */}
                {isExpanded && (
                  <div className="p-4 border-t border-slate-800/80 space-y-4 bg-slate-950/40">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-[11px] font-semibold text-slate-400 mb-1">Company</label>
                        <input
                          type="text"
                          value={item.company || ''}
                          onChange={(e) => handleUpdateItem(index, { company: e.target.value })}
                          placeholder="e.g. Acme Corp"
                          className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-sky-500"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-semibold text-slate-400 mb-1">Job Title</label>
                        <input
                          type="text"
                          value={item.title || ''}
                          onChange={(e) => handleUpdateItem(index, { title: e.target.value })}
                          placeholder="e.g. Senior Software Engineer"
                          className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-sky-500"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-semibold text-slate-400 mb-1">Location</label>
                        <input
                          type="text"
                          value={item.location || ''}
                          onChange={(e) => handleUpdateItem(index, { location: e.target.value })}
                          placeholder="e.g. San Francisco, CA (Hybrid)"
                          className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-sky-500"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-[11px] font-semibold text-slate-400 mb-1">Start Date</label>
                          <input
                            type="text"
                            value={item.start_date || ''}
                            onChange={(e) => handleUpdateItem(index, { start_date: e.target.value })}
                            placeholder="e.g. Jan 2021"
                            className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-sky-500"
                          />
                        </div>
                        <div>
                          <label className="block text-[11px] font-semibold text-slate-400 mb-1">End Date</label>
                          <input
                            type="text"
                            value={item.end_date || ''}
                            onChange={(e) => handleUpdateItem(index, { end_date: e.target.value })}
                            placeholder="e.g. Present"
                            className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-sky-500"
                          />
                        </div>
                      </div>
                    </div>

                    <div>
                      <label className="block text-[11px] font-semibold text-slate-400 mb-1">Description / Summary</label>
                      <textarea
                        value={item.description || ''}
                        onChange={(e) => handleUpdateItem(index, { description: e.target.value })}
                        placeholder="Overview of core duties and operational impact..."
                        rows={2}
                        className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-sky-500"
                      />
                    </div>

                    {/* Key Achievements */}
                    <div className="space-y-2 pt-2 border-t border-slate-800/60">
                      <label className="text-[11px] font-semibold text-slate-300 flex items-center gap-1.5">
                        <Award className="w-3.5 h-3.5 text-amber-400" />
                        Key Achievements & Bullet Points ({item.achievements?.length || 0})
                      </label>

                      {item.achievements && item.achievements.length > 0 && (
                        <ul className="space-y-1.5 pl-2">
                          {item.achievements.map((ach, achIdx) => (
                            <li key={achIdx} className="flex items-start justify-between gap-2 text-xs text-slate-300 bg-slate-900/60 p-2 rounded-lg border border-slate-800">
                              <span className="leading-snug">• {ach}</span>
                              <button
                                type="button"
                                onClick={() => handleRemoveAchievement(index, achIdx)}
                                className="text-slate-500 hover:text-rose-400 shrink-0 p-0.5"
                                title="Delete bullet"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
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
                              handleAddAchievement(index, newAchInput);
                              setNewAchInput('');
                            }
                          }}
                          placeholder="Add accomplishment (e.g. Reduced API latency by 40%)..."
                          className="flex-1 px-3 py-1.5 text-xs bg-slate-900 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-sky-500"
                        />
                        <button
                          type="button"
                          onClick={() => {
                            handleAddAchievement(index, newAchInput);
                            setNewAchInput('');
                          }}
                          className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 text-sky-300 hover:bg-slate-700"
                        >
                          Add Bullet
                        </button>
                      </div>
                    </div>

                    {/* Technologies Used */}
                    <div className="space-y-2 pt-2 border-t border-slate-800/60">
                      <label className="text-[11px] font-semibold text-slate-300 flex items-center gap-1.5">
                        <Layers className="w-3.5 h-3.5 text-indigo-400" />
                        Technologies Used ({item.technologies?.length || 0})
                      </label>

                      <div className="flex flex-wrap gap-1.5">
                        {item.technologies?.map((tech, techIdx) => (
                          <span
                            key={techIdx}
                            className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300"
                          >
                            {tech}
                            <button
                              type="button"
                              onClick={() => handleRemoveTechnology(index, techIdx)}
                              className="text-slate-500 hover:text-rose-400 p-0.5"
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
                              handleAddTechnology(index, newTechInput);
                              setNewTechInput('');
                            }
                          }}
                          placeholder="Add tech stack item (e.g. Docker, Redis)..."
                          className="flex-1 px-3 py-1.5 text-xs bg-slate-900 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-sky-500"
                        />
                        <button
                          type="button"
                          onClick={() => {
                            handleAddTechnology(index, newTechInput);
                            setNewTechInput('');
                          }}
                          className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 text-sky-300 hover:bg-slate-700"
                        >
                          Add Tech
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
};
