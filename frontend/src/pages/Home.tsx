import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Bot, CheckCircle2, ShieldCheck, Database, Layers, ArrowRight, FileText } from 'lucide-react';

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
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setHealthStatus(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div className="max-w-6xl mx-auto px-4 py-12">
      {/* Header Banner */}
      <header className="flex flex-col md:flex-row items-start md:items-center justify-between border-b border-slate-800 pb-8 mb-12">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-sky-500/10 text-sky-400 rounded-lg border border-sky-500/20">
              <Bot className="w-7 h-7" />
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white">
              AI Job Hunter Co-Pilot
            </h1>
          </div>
          <p className="text-slate-400 text-sm md:text-base">
            Grounded Job Matching, Skill Gap Analysis & Human-in-the-Loop Resume Tailoring
          </p>
        </div>
        <div className="mt-4 md:mt-0 flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs text-slate-300">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          Step 3B Active — React Resume Review UI
        </div>
      </header>

      {/* Quick Launch Banner for Step 3B */}
      <div className="mb-12 p-6 bg-gradient-to-r from-sky-950/60 via-slate-900 to-indigo-950/40 border border-sky-500/30 rounded-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6 backdrop-blur shadow-xl">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-sky-500/10 text-sky-400 rounded-xl border border-sky-500/20 shrink-0">
            <FileText className="w-8 h-8" />
          </div>
          <div>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30 uppercase tracking-wider">
              Step 3B Frontend Ready
            </span>
            <h2 className="text-lg font-bold text-white mt-1">
              Resume Review & Human Confirmation UI
            </h2>
            <p className="text-xs text-slate-300 mt-1 max-w-xl leading-relaxed">
              Upload PDF/DOCX resumes, trigger AI structured extraction into an unverified draft, review and edit skills, experience, education, and target titles, and confirm to merge into verified profile.
            </p>
          </div>
        </div>

        <Link
          to="/resume-review"
          className="px-6 py-3 text-xs font-bold rounded-xl bg-sky-600 hover:bg-sky-500 text-white transition-all shadow-lg shadow-sky-950 flex items-center gap-2 shrink-0"
        >
          Launch Resume Review Flow
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Backend Health Check Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <div className="md:col-span-2 bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur">
          <h2 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
            <Database className="w-5 h-5 text-sky-400" />
            Backend Service Status
          </h2>
          {loading ? (
            <p className="text-slate-500 text-sm">Checking backend health endpoint...</p>
          ) : error ? (
            <div className="p-3 bg-red-950/40 border border-red-800/50 rounded-lg text-red-400 text-sm">
              Failed to connect to backend: {error} (Ensure backend server is running on port 8000)
            </div>
          ) : healthStatus ? (
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <span className="text-xs text-slate-500 uppercase tracking-wider block mb-1">Status</span>
                <span className="text-emerald-400 font-medium flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" /> {healthStatus.status.toUpperCase()}
                </span>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <span className="text-xs text-slate-500 uppercase tracking-wider block mb-1">Active LLM Provider</span>
                <span className="text-sky-400 font-medium capitalize">{healthStatus.active_llm_provider}</span>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <span className="text-xs text-slate-500 uppercase tracking-wider block mb-1">Environment</span>
                <span className="text-slate-300 font-medium">{healthStatus.environment}</span>
              </div>
              <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <span className="text-xs text-slate-500 uppercase tracking-wider block mb-1">Service Name</span>
                <span className="text-slate-300 font-medium truncate">{healthStatus.service}</span>
              </div>
            </div>
          ) : null}
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-6 backdrop-blur">
          <h2 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            Core Guardrails
          </h2>
          <ul className="space-y-3 text-xs text-slate-400">
            <li className="flex items-start gap-2">
              <span className="text-emerald-400">✓</span> No automated form submissions (HITL enforced).
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-400">✓</span> Grounded resume generation (Zero hallucination).
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-400">✓</span> Multi-tier job filtering & pgvector similarity.
            </li>
            <li className="flex items-start gap-2">
              <span className="text-emerald-400">✓</span> Hot-swappable Gemini / Groq / Mistral provider.
            </li>
          </ul>
        </div>
      </div>

      {/* Feature Blueprint Placeholder */}
      <section className="bg-slate-900/30 border border-slate-800/80 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-slate-200 mb-2 flex items-center gap-2">
          <Layers className="w-5 h-5 text-indigo-400" />
          System Modules Blueprint
        </h2>
        <p className="text-slate-400 text-xs mb-6">
          Project feature implementation roadmap.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          {[
            { title: "1. Profile & Resume (Step 3B)", status: "Implemented", desc: "PDF/DOCX parsing, draft review & confirmation" },
            { title: "2. Job Sources Ingest", status: "Planned", desc: "Normalized job schema & deduplication" },
            { title: "3. 3-Tier Match Engine", status: "Planned", desc: "Deterministic + pgvector + LLM" },
            { title: "4. Grounded Tailoring", status: "Planned", desc: "Fact-checked bullets & cover letters" },
          ].map((item, idx) => (
            <div key={idx} className={`p-4 rounded-lg border ${idx === 0 ? 'bg-sky-950/30 border-sky-500/40' : 'bg-slate-950/40 border-slate-800/60'}`}>
              <div className="flex items-center justify-between mb-2">
                <span className={`font-semibold ${idx === 0 ? 'text-sky-300' : 'text-slate-300'}`}>{item.title}</span>
              </div>
              <p className="text-slate-500 mb-3">{item.desc}</p>
              <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${idx === 0 ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-slate-800 text-slate-400'}`}>
                {item.status}
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
