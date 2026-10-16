import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FileText, User, Briefcase, LayoutGrid, LogOut, Key } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { AuthModal } from '../auth/AuthModal';

const navItems = [
  { path: '/profile', label: 'Profile', icon: <User className="w-3.5 h-3.5" /> },
  { path: '/resume-review', label: 'Resume', icon: <FileText className="w-3.5 h-3.5" /> },
  { path: '/jobs', label: 'Jobs', icon: <Briefcase className="w-3.5 h-3.5" /> },
  { path: '/applications', label: 'Applications', icon: <LayoutGrid className="w-3.5 h-3.5" /> },
];

export const Header: React.FC = () => {
  const location = useLocation();
  const { user, logout } = useAuth();
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  return (
    <>
      <header className="border-b border-slate-200 bg-white sticky top-0 z-50 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 h-12 flex items-center justify-between gap-6">

          {/* Brand */}
          <Link
            to="/"
            className="text-[15px] font-bold tracking-tight text-slate-800 hover:text-blue-600 transition-colors shrink-0"
          >
            HireIQ
          </Link>

          {/* Nav */}
          <nav className="flex items-center gap-0.5">
            {navItems.map((item) => {
              const isActive =
                location.pathname === item.path ||
                (item.path !== '/' && location.pathname.startsWith(item.path));
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[13px] font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-slate-500 hover:text-slate-800 hover:bg-slate-100'
                  }`}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Auth */}
          <div className="flex items-center gap-2 shrink-0">
            {user ? (
              <div className="flex items-center gap-2 pl-2 pr-1 py-1 bg-slate-50 border border-slate-200 rounded-lg">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                <span
                  className="text-[12px] font-medium text-slate-700 truncate max-w-[120px]"
                  title={user.email}
                >
                  {user.full_name || user.email}
                </span>
                <button
                  onClick={logout}
                  title="Sign out"
                  className="p-1 hover:bg-slate-200 text-slate-400 hover:text-slate-700 rounded transition-colors"
                >
                  <LogOut className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => setIsAuthModalOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-[13px] font-medium transition-colors"
              >
                <Key className="w-3.5 h-3.5" />
                <span>Sign In</span>
              </button>
            )}
          </div>
        </div>
      </header>

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
      />
    </>
  );
};
