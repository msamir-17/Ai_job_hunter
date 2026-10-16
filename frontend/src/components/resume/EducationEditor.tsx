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
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <GraduationCap className="w-4 h-4 text-slate-500" />
          <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
            Education ({education.length})
          </h3>
        </div>
        <button
          type="button"
          onClick={handleAddEducation}
          className="px-3 py-1.5 text-xs font-medium rounded-lg bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 transition-colors flex items-center gap-1.5"
        >
          <Plus className="w-3.5 h-3.5" />
          Add Education
        </button>
      </div>

      {education.length === 0 ? (
        <p className="text-xs text-slate-400 italic py-4 text-center">
          No education entries extracted. Click "Add Education" to add entries manually.
        </p>
      ) : (
        <div className="space-y-3">
          {education.map((item, index) => {
            const isExpanded = expandedIndex === index;

            return (
              <div
                key={index}
                className="bg-slate-50 border border-slate-200 rounded-lg overflow-hidden transition-colors"
              >
                {/* Header bar */}
                <div
                  onClick={() => setExpandedIndex(isExpanded ? null : index)}
                  className="px-4 py-3 flex items-center justify-between cursor-pointer hover:bg-slate-100/70 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-1.5 bg-white border border-slate-200 text-slate-700 rounded-md text-xs font-mono font-semibold">
                      #{index + 1}
                    </div>
                    <div>
                      <h4 className="text-xs font-semibold text-slate-900">
                        {item.degree || 'Degree'}{' '}
                        {item.field_of_study && `in ${item.field_of_study}`}{' '}
                        {item.institution && <span className="text-slate-500 font-normal">at {item.institution}</span>}
                      </h4>
                      <p className="text-[11px] text-slate-500">
                        {item.start_date || 'Start'} – {item.end_date || 'Graduation'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveEducation(index);
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

                {/* Expanded edit form */}
                {isExpanded && (
                  <div className="p-4 border-t border-slate-200 space-y-3 bg-white">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-[11px] font-medium text-slate-600 mb-1">Institution</label>
                        <input
                          type="text"
                          value={item.institution || ''}
                          onChange={(e) => handleUpdateItem(index, { institution: e.target.value })}
                          placeholder="e.g. Stanford University"
                          className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-medium text-slate-600 mb-1">Degree</label>
                        <input
                          type="text"
                          value={item.degree || ''}
                          onChange={(e) => handleUpdateItem(index, { degree: e.target.value })}
                          placeholder="e.g. Bachelor of Science"
                          className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-medium text-slate-600 mb-1">Field of Study</label>
                        <input
                          type="text"
                          value={item.field_of_study || ''}
                          onChange={(e) => handleUpdateItem(index, { field_of_study: e.target.value })}
                          placeholder="e.g. Computer Science"
                          className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-[11px] font-medium text-slate-600 mb-1">Start Date</label>
                          <input
                            type="text"
                            value={item.start_date || ''}
                            onChange={(e) => handleUpdateItem(index, { start_date: e.target.value })}
                            placeholder="e.g. 2019"
                            className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-[11px] font-medium text-slate-600 mb-1">End Date</label>
                          <input
                            type="text"
                            value={item.end_date || ''}
                            onChange={(e) => handleUpdateItem(index, { end_date: e.target.value })}
                            placeholder="e.g. 2023"
                            className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500"
                          />
                        </div>
                      </div>
                    </div>

                    <div>
                      <label className="block text-[11px] font-medium text-slate-600 mb-1">Description / Honors</label>
                      <textarea
                        value={item.description || ''}
                        onChange={(e) => handleUpdateItem(index, { description: e.target.value })}
                        placeholder="Achievements, honors, or thesis title..."
                        rows={2}
                        className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500"
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
