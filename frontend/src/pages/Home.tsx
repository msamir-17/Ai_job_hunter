import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  CheckCircle2,
  Database,
  FileText,
  Briefcase,
  LayoutGrid,
  User,
  ArrowRight,
  ShieldCheck,
  Layers,
} from 'lucide-react';

export const Home: React.FC = () => {
  const [healthStatus, setHealthStatus] = useState<{
    status: string;
    service: string;
    environment: string;
    active_llm_provider: string;
  } | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => { setHealthStatus(data); setLoading(false); })
      .catch((err) => { setError(err.message); setLoading(false); });
  }, []);

  const featureCards = [
    {
      path: '/profile',
      icon: <User className="w-4 h-4 text-blue-600" />,
      iconBg: 'bg-blue-50',
      title: 'Candidate Profile',
      desc: 'Maintain your verified source of truth — skills, target titles, experience and preferences.',
      linkLabel: 'View Profile',
      linkColor: 'text-blue-600 hover:text-blue-800',
    },
    {
      path: '/resume-review',
      icon: <FileText className="w-4 h-4 text-indigo-600" />,
      iconBg: 'bg-indigo-50',
      title: 'Resume Review',
      desc: 'Upload PDF / DOCX, inspect AI extraction, and confirm before merging into your profile.',
      linkLabel: 'Review Resumes',
      linkColor: 'text-indigo-600 hover:text-indigo-800',
    },
    {
      path: '/jobs',
      icon: <Briefcase className="w-4 h-4 text-slate-600" />,
      iconBg: 'bg-slate-100',
      title: 'Job Discovery',
      desc: 'Ingest live jobs, run 3-tier matching, view skill gaps, and tailor application materials.',
      linkLabel: 'Explore Jobs',
      linkColor: 'text-slate-700 hover:text-slate-900',
    },
    {
      path: '/applications',
      icon: <LayoutGrid className="w-4 h-4 text-emerald-600" />,
      iconBg: 'bg-emerald-50',
      title: 'Applications',
      desc: 'Track pipeline stages — Saved, Applied, Interviewing, Offer — and manage tailored docs.',
      linkLabel: 'Open Board',
      linkColor: 'text-emerald-600 hover:text-emerald-800',
    },
  ];

  const modules = [
    { title: 'Profile & Resume', desc: 'PDF / DOCX parsing, draft review & confirmation', status: 'Live' },
    { title: 'Job Source Ingest', desc: 'Normalized job schema, deduplication & Remotive feed', status: 'Live' },
    { title: '3-Tier Match Engine', desc: 'Deterministic + pgvector + LLM reasoning via LangGraph', status: 'Live' },
    { title: 'Grounded Tailoring', desc: 'Fact-checked bullets, cover letters & audit trail', status: 'Live' },
  ];

  return (
    <div className="max-w-5xl mx-auto px-4 py-10 space-y-10">

      {/* Page header */}
      <div className="border-b border-slate-200 pb-6">
        <h1 className="text-2xl font-bold text-slate-800 tracking-tight mb-1">Overview</h1>
        <p className="text-slate-500 text-sm">
          AI-powered job matching with grounded resume tailoring and human-in-the-loop verification.
        </p>
      </div>

      {/* Feature cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {featureCards.map((card) => (
          <div
            key={card.path}
            className="bg-white border border-slate-200 rounded-xl p-5 flex flex-col justify-between hover:shadow-md transition-shadow"
          >
            <div className="space-y-3">
              <div className={`w-8 h-8 ${card.iconBg} rounded-lg flex items-center justify-center`}>
                {card.icon}
              </div>
              <h3 className="text-[14px] font-semibold text-slate-800">{card.title}</h3>
              <p className="text-[12px] text-slate-500 leading-relaxed">{card.desc}</p>
            </div>
            <Link
              to={card.path}
              className={`flex items-center gap-1 text-[12px] font-medium mt-4 pt-3 border-t border-slate-100 group ${card.linkColor}`}
            >
              <span>{card.linkLabel}</span>
              <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>
        ))}
      </div>

      {/* Status + Guardrails */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="md:col-span-2 bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <h2 className="text-[13px] font-semibold text-slate-600 uppercase tracking-wide mb-4 flex items-center gap-2">
            <Database className="w-4 h-4 text-slate-400" />
            Backend Status
          </h2>
          {loading ? (
            <p className="text-slate-400 text-sm">Checking backend health...</p>
          ) : error ? (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              Could not connect to backend: {error}. Ensure the server is running on port 8000.
            </div>
          ) : healthStatus ? (
            <div className="grid grid-cols-2 gap-3 text-sm">
              {[
                { label: 'Status', value: healthStatus.status.toUpperCase(), color: 'text-emerald-600', icon: <CheckCircle2 className="w-3.5 h-3.5 inline mr-1" /> },
                { label: 'LLM Provider', value: healthStatus.active_llm_provider, color: 'text-blue-600' },
                { label: 'Environment', value: healthStatus.environment, color: 'text-slate-700' },
                { label: 'Service', value: healthStatus.service, color: 'text-slate-700' },
              ].map((row) => (
                <div key={row.label} className="p-3 bg-slate-50 border border-slate-100 rounded-lg">
                  <span className="text-[10px] uppercase tracking-wider text-slate-400 font-medium block mb-1">{row.label}</span>
                  <span className={`text-[13px] font-medium ${row.color} capitalize`}>
                    {row.icon}{row.value}
                  </span>
                </div>
              ))}
            </div>
          ) : null}
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
          <h2 className="text-[13px] font-semibold text-slate-600 uppercase tracking-wide mb-4 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-slate-400" />
            Guardrails
          </h2>
          <ul className="space-y-2.5 text-[12px] text-slate-500">
            {[
              'No automated form submissions (HITL enforced)',
              'Grounded generation — zero hallucination policy',
              'Multi-tier filtering & pgvector similarity search',
              'Swappable Gemini / Groq / Mistral provider',
            ].map((rule) => (
              <li key={rule} className="flex items-start gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                {rule}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* System modules */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <h2 className="text-[13px] font-semibold text-slate-600 uppercase tracking-wide mb-1 flex items-center gap-2">
          <Layers className="w-4 h-4 text-slate-400" />
          System Modules
        </h2>
        <p className="text-[12px] text-slate-400 mb-5">Full-stack AI pipeline — all modules live and verified.</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {modules.map((mod, idx) => (
            <div key={idx} className="p-4 rounded-lg border border-slate-100 bg-slate-50">
              <p className="text-[13px] font-semibold text-slate-700 mb-1">{mod.title}</p>
              <p className="text-[11px] text-slate-500 mb-3 leading-relaxed">{mod.desc}</p>
              <span className="inline-block px-2 py-0.5 rounded text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                {mod.status}
              </span>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};
