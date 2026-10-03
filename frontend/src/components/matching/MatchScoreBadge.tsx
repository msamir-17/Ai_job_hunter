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
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700">
        Not evaluated
      </span>
    );
  }

  const rounded = Math.round(score);

  let colorClasses = 'bg-red-500/10 text-red-400 border-red-500/30';
  if (rounded >= 80) {
    colorClasses = 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40 shadow-emerald-950/20';
  } else if (rounded >= 60) {
    colorClasses = 'bg-sky-500/15 text-sky-300 border-sky-500/40';
  } else if (rounded >= 40) {
    colorClasses = 'bg-amber-500/15 text-amber-300 border-amber-500/40';
  }

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
    lg: 'text-sm px-3.5 py-1.5 font-bold',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-semibold border ${colorClasses} ${sizeClasses[size]}`}
    >
      <span
        className={`w-2 h-2 rounded-full ${
          rounded >= 80
            ? 'bg-emerald-400 animate-pulse'
            : rounded >= 60
            ? 'bg-sky-400'
            : rounded >= 40
            ? 'bg-amber-400'
            : 'bg-red-400'
        }`}
      />
      <span>{rounded}%</span>
      {showLabel && (
        <span className="text-[10px] uppercase tracking-wider opacity-80">
          {rounded >= 80 ? 'Strong' : rounded >= 60 ? 'Good' : rounded >= 40 ? 'Fair' : 'Weak'}
        </span>
      )}
    </span>
  );
};
