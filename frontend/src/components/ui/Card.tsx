import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  header?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({ children, className = '', header }) => {
  return (
    <div className={`bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur shadow-sm ${className}`}>
      {header && <div className="border-b border-slate-800 pb-4 mb-4">{header}</div>}
      {children}
    </div>
  );
};
