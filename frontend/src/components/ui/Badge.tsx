import React from 'react';

interface BadgeProps {
  variant?: 'draft' | 'verified' | 'neutral' | 'info';
  children: React.ReactNode;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ variant = 'neutral', children, className = '' }) => {
  const styles = {
    draft: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
    verified: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
    neutral: 'bg-slate-800 text-slate-300 border-slate-700',
    info: 'bg-sky-500/10 text-sky-300 border-sky-500/30',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${styles[variant]} ${className}`}
    >
      {variant === 'draft' && <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />}
      {variant === 'verified' && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />}
      {children}
    </span>
  );
};
