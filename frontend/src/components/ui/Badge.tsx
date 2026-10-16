import React from 'react';

interface BadgeProps {
  variant?: 'draft' | 'verified' | 'neutral' | 'info';
  children: React.ReactNode;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ variant = 'neutral', children, className = '' }) => {
  const styles = {
    draft: 'bg-amber-50 text-amber-700 border-amber-200',
    verified: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    neutral: 'bg-slate-100 text-slate-600 border-slate-200',
    info: 'bg-blue-50 text-blue-700 border-blue-200',
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
