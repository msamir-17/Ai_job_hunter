import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Bot,
  CheckCircle2,
  ShieldCheck,
  Database,
  Layers,
  ArrowRight,
  FileText,
  Briefcase,
  Kanban,
  User,
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
    <div className="max-w-6xl mx-auto px-4 py-12 animate-fade-in space-y-12">
      {/* Header Banner */}
      <header className="flex flex-col md:flex-row items-start md:items-center justify-between border-b border-slate-800 pb-8">
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
            Grounded Job Matching, Skill Gap Analysis & Human-in-the-Loop Tailoring
          </p>
        </div>
        <div className="mt-4 md:mt-0 flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs text-slate-300">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          Full End-to-End Pipeline Active
        </div>
      </header>

      {/* Feature Navigation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Candidate Profile */}
        <div className="bg-slate-900/60 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 flex flex-col justify-between space-y-4 transition-all">
          <div className="space-y-3">
            <div className="p-2.5 bg-sky-500/10 text-sky-400 rounded-xl border border-sky-500/20 w-fit">
              <User className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Verified Candidate Profile
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Maintain your verified single source of truth: skills, target titles, experience, and preferences.
            </p>
          </div>
          <Link
            to="/profile"
            className="flex items-center justify-between text-xs font-semibold text-sky-400 hover:text-sky-300 pt-2 border-t border-slate-800/80 group"
          >
            <span>View Profile</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>

        {/* Resume Review & AI Parser */}
        <div className="bg-slate-900/60 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 flex flex-col justify-between space-y-4 transition-all">
          <div className="space-y-3">
            <div className="p-2.5 bg-indigo-500/10 text-indigo-400 rounded-xl border border-indigo-500/20 w-fit">
              <FileText className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Resume Ingestion & Review
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Upload PDF/DOCX resumes, inspect AI structured extraction, and confirm before merging into verified profile facts.
            </p>
          </div>
          <Link
            to="/resume-review"
            className="flex items-center justify-between text-xs font-semibold text-indigo-400 hover:text-indigo-300 pt-2 border-t border-slate-800/80 group"
          >
            <span>Review Resumes</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>

        {/* Job Discovery & 3-Tier Matcher */}
        <div className="bg-gradient-to-br from-slate-900/90 via-slate-900/60 to-sky-950/30 border border-sky-500/30 hover:border-sky-500/50 rounded-2xl p-5 flex flex-col justify-between space-y-4 transition-all shadow-lg shadow-sky-950/20">
          <div className="space-y-3">
            <div className="p-2.5 bg-sky-500/20 text-sky-300 rounded-xl border border-sky-500/30 w-fit">
              <Briefcase className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Job Discovery & 3-Tier Match
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Ingest live jobs, run Deterministic + pgvector + LLM reasoning, view skill gaps, and tailor grounded application materials.
            </p>
          </div>
          <Link
            to="/jobs"
            className="flex items-center justify-between text-xs font-bold text-sky-300 hover:text-sky-200 pt-2 border-t border-slate-800/80 group"
          >
            <span>Explore & Match Jobs</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>

        {/* Application Pipeline Kanban */}
        <div className="bg-slate-900/60 border border-slate-800 hover:border-slate-700 rounded-2xl p-5 flex flex-col justify-between space-y-4 transition-all">
          <div className="space-y-3">
            <div className="p-2.5 bg-emerald-500/10 text-emerald-400 rounded-xl border border-emerald-500/20 w-fit">
              <Kanban className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-white tracking-tight">
              Applications Kanban Board
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Track job pipeline columns (Saved, Applied, Interviewing, Offer), review tailored docs, and safely apply via external portals.
            </p>
          </div>
          <Link
            to="/applications"
            className="flex items-center justify-between text-xs font-semibold text-emerald-400 hover:text-emerald-300 pt-2 border-t border-slate-800/80 group"
          >
            <span>Open Kanban Board</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </div>

      {/* Backend Health Check Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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
              <span className="text-emerald-400">✓</span> Swappable Gemini / Groq / Mistral provider.
            </li>
          </ul>
        </div>
      </div>

      {/* Feature Blueprint */}
      <section className="bg-slate-900/30 border border-slate-800/80 rounded-xl p-6">
        <h2 className="text-lg font-semibold text-slate-200 mb-2 flex items-center gap-2">
          <Layers className="w-5 h-5 text-indigo-400" />
          System Modules Blueprint
        </h2>
        <p className="text-slate-400 text-xs mb-6">
          Full-stack production AI application architecture.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          {[
            { title: "1. Profile & Resume", status: "Live & Verified", desc: "PDF/DOCX parsing, draft review & confirmation" },
            { title: "2. Job Sources Ingest", status: "Live & Verified", desc: "Normalized job schema, deduplication & Remotive" },
            { title: "3. 3-Tier Match Engine", status: "Live & Verified", desc: "Deterministic + pgvector + LLM LangGraph" },
            { title: "4. Grounded Tailoring", status: "Live & Verified", desc: "Fact-checked bullets, cover letters & audit" },
          ].map((item, idx) => (
            <div key={idx} className="p-4 rounded-lg border bg-slate-950/40 border-slate-800/60">
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-slate-300">{item.title}</span>
              </div>
              <p className="text-slate-500 mb-3">{item.desc}</p>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                {item.status}
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
