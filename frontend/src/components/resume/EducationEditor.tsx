import React, { useState } from 'react';
import { GraduationCap, Plus, Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import { EducationItem } from '../../types/resume';
import { Card } from '../ui/Card';

interface EducationEditorProps {
  education: EducationItem[];
  onEducationChange: (edu: EducationItem[]) => void;
}

export const EducationEditor: React.FC<EducationEditorProps> = ({
  education,
  onEducationChange,
}) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0);

  const handleUpdateItem = (index: number, updatedFields: Partial<EducationItem>) => {
    const updated = [...education];
    updated[index] = { ...updated[index], ...updatedFields };
    onEducationChange(updated);
  };

  const handleAddEducation = () => {
    const newItem: EducationItem = {
      institution: '',
      degree: '',
      field_of_study: '',
      start_date: '',
      end_date: '',
      description: '',
    };
    onEducationChange([...education, newItem]);
    setExpandedIndex(education.length);
  };

  const handleRemoveEducation = (index: number) => {
    const updated = education.filter((_, i) => i !== index);
    onEducationChange(updated);
    if (expandedIndex === index) {
      setExpandedIndex(null);
    }
  };

  return (
    <Card className="mb-6">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <GraduationCap className="w-5 h-5 text-emerald-400" />
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Education ({education.length})
          </h3>
        </div>
        <button
          type="button"
          onClick={handleAddEducation}
          className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-sky-300 transition-colors flex items-center gap-1.5"
        >
          <Plus className="w-3.5 h-3.5" />
          Add Education
        </button>
      </div>

      {education.length === 0 ? (
        <p className="text-xs text-slate-500 italic py-4 text-center">
          No education entries extracted. Click "Add Education" to add entries manually.
        </p>
      ) : (
        <div className="space-y-4">
          {education.map((item, index) => {
            const isExpanded = expandedIndex === index;

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
                    <div className="p-2 bg-slate-900 border border-slate-800 text-emerald-400 rounded-lg text-xs font-bold font-mono">
                      #{index + 1}
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-white">
                        {item.degree || 'Degree'}{' '}
                        {item.field_of_study && `in ${item.field_of_study}`}{' '}
                        {item.institution && <span className="text-slate-400 font-normal">at {item.institution}</span>}
                      </h4>
                      <p className="text-[11px] text-slate-500">
                        {item.start_date || 'Start'} - {item.end_date || 'Graduation'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveEducation(index);
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
                  <div className="p-4 border-t border-slate-800/80 space-y-3 bg-slate-950/40">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-[11px] font-semibold text-slate-400 mb-1">Institution</label>
                        <input
                          type="text"
                          value={item.institution || ''}
                          onChange={(e) => handleUpdateItem(index, { institution: e.target.value })}
                          placeholder="e.g. Stanford University"
                          className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-sky-500"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-semibold text-slate-400 mb-1">Degree</label>
                        <input
                          type="text"
                          value={item.degree || ''}
                          onChange={(e) => handleUpdateItem(index, { degree: e.target.value })}
                          placeholder="e.g. Bachelor of Science"
                          className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-sky-500"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-semibold text-slate-400 mb-1">Field of Study</label>
                        <input
                          type="text"
                          value={item.field_of_study || ''}
                          onChange={(e) => handleUpdateItem(index, { field_of_study: e.target.value })}
                          placeholder="e.g. Computer Science"
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
                            placeholder="e.g. 2016"
                            className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-sky-500"
                          />
                        </div>
                        <div>
                          <label className="block text-[11px] font-semibold text-slate-400 mb-1">End Date</label>
                          <input
                            type="text"
                            value={item.end_date || ''}
                            onChange={(e) => handleUpdateItem(index, { end_date: e.target.value })}
                            placeholder="e.g. 2020"
                            className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-sky-500"
                          />
                        </div>
                      </div>
                    </div>

                    <div>
                      <label className="block text-[11px] font-semibold text-slate-400 mb-1">Description / Honors</label>
                      <textarea
                        value={item.description || ''}
                        onChange={(e) => handleUpdateItem(index, { description: e.target.value })}
                        placeholder="GPA, achievements, honors, or thesis title..."
                        rows={2}
                        className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-sky-500"
                      />
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
