import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  header?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({ children, className = '', header }) => {
  return (
    <div className={`bg-white border border-slate-200 rounded-xl p-6 shadow-sm ${className}`}>
      {header && <div className="border-b border-slate-100 pb-4 mb-4">{header}</div>}
      {children}
    </div>
  );
};
