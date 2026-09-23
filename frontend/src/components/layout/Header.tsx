import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Bot, FileText, User, Home } from 'lucide-react';

export const Header: React.FC = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Overview', icon: <Home className="w-4 h-4" /> },
    { path: '/resume-review', label: 'Resume Review & HITL', icon: <FileText className="w-4 h-4" /> },
    { path: '/profile', label: 'Candidate Profile', icon: <User className="w-4 h-4" /> },
  ];

  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 py-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="p-2 bg-sky-500/10 text-sky-400 rounded-lg border border-sky-500/20 group-hover:border-sky-500/40 transition-colors">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white group-hover:text-sky-300 transition-colors">
              AI Job Hunter Co-Pilot
            </h1>
            <p className="text-xs text-slate-400 hidden sm:block">
              Human-in-the-Loop Verified Candidate Workflow
            </p>
          </div>
        </Link>

        <nav className="flex items-center gap-1 bg-slate-900/80 border border-slate-800 p-1 rounded-xl">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-sky-500/15 text-sky-300 border border-sky-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
