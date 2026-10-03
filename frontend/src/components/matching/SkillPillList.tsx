import React from 'react';
import { Check, AlertCircle } from 'lucide-react';

interface SkillPillListProps {
  matchedSkills: string[];
  missingSkills: string[];
  maxDisplay?: number;
}

export const SkillPillList: React.FC<SkillPillListProps> = ({
  matchedSkills,
  missingSkills,
  maxDisplay = 10,
}) => {
  const displayedMatched = matchedSkills.slice(0, maxDisplay);
  const displayedMissing = missingSkills.slice(0, maxDisplay);

  if (matchedSkills.length === 0 && missingSkills.length === 0) {
    return <span className="text-xs text-slate-500 italic">No skill analysis available</span>;
  }

  return (
    <div className="space-y-2">
      {matchedSkills.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] font-semibold text-emerald-400 mr-1 flex items-center gap-1">
            <Check className="w-3.5 h-3.5" /> Matched:
          </span>
          {displayedMatched.map((skill, idx) => (
            <span
              key={`match-${idx}`}
              className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/30"
            >
              {skill}
            </span>
          ))}
          {matchedSkills.length > maxDisplay && (
            <span className="text-[10px] text-emerald-400/80 font-mono">
              +{matchedSkills.length - maxDisplay} more
            </span>
          )}
        </div>
      )}

      {missingSkills.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] font-semibold text-amber-400 mr-1 flex items-center gap-1">
            <AlertCircle className="w-3.5 h-3.5" /> Skill Gaps:
          </span>
          {displayedMissing.map((skill, idx) => (
            <span
              key={`missing-${idx}`}
              className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium bg-amber-500/10 text-amber-300 border border-amber-500/30"
            >
              {skill}
            </span>
          ))}
          {missingSkills.length > maxDisplay && (
            <span className="text-[10px] text-amber-400/80 font-mono">
              +{missingSkills.length - maxDisplay} more
            </span>
          )}
        </div>
      )}
    </div>
  );
};
