import React from 'react';

interface MatchScoreBadgeProps {
  score?: number | null;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export const MatchScoreBadge: React.FC<MatchScoreBadgeProps> = ({
  score,
  size = 'md',
  showLabel = true,
}) => {
  if (score === null || score === undefined) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-500 border border-slate-200">
        Not evaluated
      </span>
    );
  }

  const rounded = Math.round(score);

  let colorClasses = 'bg-red-50 text-red-700 border-red-200';
  let dotColor = 'bg-red-500';
  if (rounded >= 80) {
    colorClasses = 'bg-emerald-50 text-emerald-800 border-emerald-200';
    dotColor = 'bg-emerald-500';
  } else if (rounded >= 60) {
    colorClasses = 'bg-blue-50 text-blue-800 border-blue-200';
    dotColor = 'bg-blue-500';
  } else if (rounded >= 40) {
    colorClasses = 'bg-amber-50 text-amber-800 border-amber-200';
    dotColor = 'bg-amber-500';
  }

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-0.5',
    lg: 'text-sm px-3 py-1 font-semibold',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium border ${colorClasses} ${sizeClasses[size]}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
      <span>{rounded}%</span>
      {showLabel && (
        <span className="text-[10px] uppercase tracking-wider opacity-75">
          {rounded >= 80 ? 'Strong' : rounded >= 60 ? 'Good' : rounded >= 40 ? 'Fair' : 'Weak'}
        </span>
      )}
    </span>
  );
};
