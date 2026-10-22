import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  CheckCircle2,
  FileUp,
  Target,
  Download,
  Sparkles,
  ShieldCheck,
  Lock,
  ExternalLink,
  User,
  Terminal,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { AuthModal } from '../components/auth/AuthModal';

interface HealthData {
  status: string;
  service: string;
  environment: string;
  active_llm_provider: string;
}

export const Home: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [healthStatus, setHealthStatus] = useState<HealthData | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(true);
  const [showDevPanel, setShowDevPanel] = useState<boolean>(false);

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setHealthStatus(data);
        setHealthLoading(false);
      })
      .catch((err) => {
        console.warn('Backend health check error:', err);
        setHealthLoading(false);
      });
  }, []);

  const handleGetStarted = () => {
    if (user) {
      navigate('/jobs');
    } else {
      navigate('/jobs');
    }
  };

  const isDev = import.meta.env.DEV;

  return (
    <div className="min-h-screen flex flex-col justify-between">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12 lg:py-16 space-y-20">

        {/* 1. HERO SECTION */}
        <section className="text-center space-y-6 pt-4 sm:pt-8 max-w-3xl mx-auto">
          {/* Subtle badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200/60 text-blue-700 text-xs font-semibold tracking-wide shadow-sm">
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            <span>Fact-Grounded Job Hunting</span>
          </div>

          {/* Headline */}
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-slate-900 tracking-tight leading-[1.18]">
            Apply smarter. Tailor every resume to the job,{' '}
            <span className="text-blue-600 underline decoration-blue-200 decoration-wavy underline-offset-4">
              truthfully
            </span>
            .
          </h1>

          {/* Subtext */}
          <p className="text-base sm:text-lg text-slate-600 leading-relaxed max-w-2xl mx-auto font-normal">
            Find matching jobs, see your skill gaps, and get a resume tailored only from facts you’ve verified.
          </p>

          {/* Hero CTAs */}
          <div className="flex flex-wrap items-center justify-center gap-3 pt-3">
            <button
              onClick={handleGetStarted}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-medium text-sm shadow-sm hover:shadow transition-all group"
            >
              <span>Get Started</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </button>

            {!user ? (
              <button
                onClick={() => setIsAuthModalOpen(true)}
                className="inline-flex items-center justify-center gap-1.5 px-4 py-3 rounded-lg bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 font-medium text-sm transition-colors"
              >
                <span>Sign In</span>
              </button>
            ) : (
              <Link
                to="/profile"
                className="inline-flex items-center justify-center gap-1.5 px-4 py-3 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium text-sm transition-colors"
              >
                <User className="w-4 h-4 text-slate-500" />
                <span>My Profile</span>
              </Link>
            )}
          </div>

          {/* If user is logged in: Quick Status Strip */}
          {user && (
            <div className="pt-4">
              <div className="inline-flex items-center gap-3 px-4 py-2 bg-emerald-50/80 border border-emerald-200 rounded-lg text-xs text-emerald-800">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span>
                  Signed in as <strong>{user.full_name || user.email}</strong>. Ready to discover and tailor jobs.
                </span>
                <Link
                  to="/applications"
                  className="font-semibold text-emerald-900 hover:underline flex items-center gap-0.5"
                >
                  View Kanban <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            </div>
          )}
        </section>

        {/* 2. HOW IT WORKS (3 steps with icons) */}
        <section className="space-y-8">
          <div className="text-center space-y-2">
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              How it works
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 max-w-xl mx-auto">
              Three clear steps from your current resume to tailored, truthful applications.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative">
            {/* Step 1 */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs flex flex-col justify-between hover:border-blue-200 transition-colors">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
                    <FileUp className="w-5 h-5" />
                  </div>
                  <span className="text-xs font-bold text-slate-400">01</span>
                </div>
                <h3 className="text-sm font-semibold text-slate-900 leading-snug">
                  Upload your resume and confirm your profile
                </h3>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Upload your existing resume. Review what was extracted and confirm your skills and experience so every application is built on truth.
                </p>
              </div>
              <div className="pt-4 mt-4 border-t border-slate-100">
                <Link
                  to="/resume-review"
                  className="text-xs font-medium text-blue-600 hover:text-blue-700 flex items-center gap-1 group"
                >
                  <span>Upload resume</span>
                  <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                </Link>
              </div>
            </div>

            {/* Step 2 */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs flex flex-col justify-between hover:border-indigo-200 transition-colors">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
                    <Target className="w-5 h-5" />
                  </div>
                  <span className="text-xs font-bold text-slate-400">02</span>
                </div>
                <h3 className="text-sm font-semibold text-slate-900 leading-snug">
                  See jobs ranked by fit, with matched and missing skills
                </h3>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Browse live roles or paste any external job description. Inspect exact skill overlap and gaps before spending time applying.
                </p>
              </div>
              <div className="pt-4 mt-4 border-t border-slate-100">
                <Link
                  to="/jobs"
                  className="text-xs font-medium text-indigo-600 hover:text-indigo-700 flex items-center gap-1 group"
                >
                  <span>Explore matching jobs</span>
                  <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                </Link>
              </div>
            </div>

            {/* Step 3 */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs flex flex-col justify-between hover:border-emerald-200 transition-colors">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-lg bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
                    <Download className="w-5 h-5" />
                  </div>
                  <span className="text-xs font-bold text-slate-400">03</span>
                </div>
                <h3 className="text-sm font-semibold text-slate-900 leading-snug">
                  Download a tailored resume and cover letter, then review before you apply
                </h3>
                <p className="text-xs text-slate-500 leading-relaxed">
                  Generate targeted bullets and cover letters strictly from verified facts. Download polished ATS PDFs and review before submission.
                </p>
              </div>
              <div className="pt-4 mt-4 border-t border-slate-100">
                <Link
                  to="/applications"
                  className="text-xs font-medium text-emerald-600 hover:text-emerald-700 flex items-center gap-1 group"
                >
                  <span>Track applications</span>
                  <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* 3. FEATURES (3 Benefit Cards - No Tech Jargon) */}
        <section className="space-y-8">
          <div className="text-center space-y-2">
            <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
              Built for truthful, confident job hunting
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 max-w-xl mx-auto">
              Focus on real career fit with complete transparency at every stage.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Feature 1 */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-3 hover:shadow-xs transition-shadow">
              <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600">
                <CheckCircle2 className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-bold text-slate-900">
                Match scores you can understand
              </h3>
              <p className="text-xs font-medium text-blue-700">
                Skills matched vs. missing
              </p>
              <p className="text-xs text-slate-500 leading-relaxed">
                Clear, honest fit ratings without mystery algorithms. You always see the exact keywords and skills that matched and what is missing.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-3 hover:shadow-xs transition-shadow">
              <div className="w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600">
                <Sparkles className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-bold text-slate-900">
                Tailored, not invented
              </h3>
              <p className="text-xs font-medium text-indigo-700">
                Every bullet comes from your verified facts
              </p>
              <p className="text-xs text-slate-500 leading-relaxed">
                We never fabricate experience, exaggerate metrics, or invent past companies. Every tailored bullet point is directly grounded in your verified history.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-3 hover:shadow-xs transition-shadow">
              <div className="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-600">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <h3 className="text-sm font-bold text-slate-900">
                You stay in control
              </h3>
              <p className="text-xs font-medium text-emerald-700">
                Review everything before you apply
              </p>
              <p className="text-xs text-slate-500 leading-relaxed">
                Zero automated submissions. We never apply to positions behind your back. You inspect, edit, and approve every document and application link.
              </p>
            </div>
          </div>
        </section>

        {/* 4. TRUST LINE */}
        <section className="bg-slate-50 border border-slate-200 rounded-xl p-6 sm:p-8 text-center space-y-3 max-w-2xl mx-auto shadow-xs">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-white border border-slate-200 text-slate-600 shadow-xs mb-1">
            <Lock className="w-5 h-5 text-slate-700" />
          </div>
          <h3 className="text-sm sm:text-base font-semibold text-slate-800">
            Your resume data stays private. You can delete it anytime.
          </h3>
          <p className="text-xs text-slate-500 leading-relaxed max-w-lg mx-auto">
            Your documents are scoped strictly to your account and never shared or sold. You can export or permanently delete your account and all stored records whenever you choose.
          </p>
          <div className="pt-2">
            <Link
              to="/profile"
              className="text-xs font-medium text-slate-600 hover:text-slate-900 underline underline-offset-4 decoration-slate-300"
            >
              Manage privacy & profile settings →
            </Link>
          </div>
        </section>

      </div>

      {/* 5. FOOTER WITH DISCRETE STATUS DOT & GITHUB LINK */}
      <footer className="border-t border-slate-200 bg-white mt-16 py-8">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          
          {/* Brand & Rights */}
          <div className="flex items-center gap-3">
            <span className="font-bold text-slate-800 tracking-tight">HireIQ</span>
            <span className="text-slate-300">•</span>
            <span>Grounded Career Co-Pilot</span>
            <span className="text-slate-300">•</span>
            <span>Human-in-the-loop</span>
          </div>

          {/* Links & Discrete Status Dot */}
          <div className="flex items-center gap-5">
            {/* Discrete Operational Status Dot */}
            <div className="flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full ${
                  healthStatus?.status === 'ok' ? 'bg-emerald-500' : healthLoading ? 'bg-amber-400' : 'bg-slate-400'
                }`}
                title="System Health"
              />
              <span className="text-slate-600 font-medium">
                {healthLoading
                  ? 'Checking status...'
                  : healthStatus?.status === 'ok'
                  ? 'All systems operational'
                  : 'Operational'}
              </span>

              {/* Developer Toggle (Only visible in DEV or on click) */}
              {isDev && (
                <button
                  onClick={() => setShowDevPanel(!showDevPanel)}
                  className="p-1 text-slate-400 hover:text-slate-600 rounded transition-colors"
                  title="Developer Diagnostics"
                >
                  <Terminal className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            <span className="text-slate-300">|</span>

            {/* GitHub Repo */}
            <a
              href="https://github.com/msamir-17/Ai_job_hunter"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-slate-500 hover:text-slate-800 transition-colors"
            >
              <span>GitHub</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>

        {/* Optional Collapsible Developer Diagnostic Tray (DEV ONLY) */}
        {isDev && showDevPanel && healthStatus && (
          <div className="max-w-5xl mx-auto px-4 sm:px-6 mt-4 pt-4 border-t border-slate-100">
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-[11px] text-slate-600 flex flex-wrap items-center justify-between gap-4 font-mono">
              <div className="flex items-center gap-4">
                <span><strong>Service:</strong> {healthStatus.service}</span>
                <span><strong>Env:</strong> {healthStatus.environment}</span>
                <span><strong>Provider:</strong> {healthStatus.active_llm_provider}</span>
              </div>
              <span className="text-slate-400">Dev Mode Diagnostics</span>
            </div>
          </div>
        )}
      </footer>

      {/* Auth Modal Trigger */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
      />
    </div>
  );
};
