import React, { useState, useEffect } from 'react';
import {
  Briefcase,
  Search,
  RotateCw,
  ChevronRight,
  BookmarkPlus,
  CheckCircle2,
  FileText,
  MapPin,
  Building,
  Download,
  Filter,
  X,
  Globe,
  Clock,
  Award,
  ThumbsDown,
  RotateCcw,
  Sparkles,
  ExternalLink,
  Plus,
} from 'lucide-react';
import { Job } from '../types/job';
import { CandidateProfileResponse } from '../types/candidateProfile';
import { PipelineRunResponse } from '../types/matching';
import { FeedbackResponse } from '../types/feedback';
import { CustomJDTailoringResponse } from '../types/tailoring';
import { listJobs, ingestJobs } from '../api/jobs';
import { getActiveCandidateProfile } from '../api/candidateProfile';
import {
  runMatchingPipeline,
  getCandidateJobMatches,
} from '../api/matching';
import { createApplication, listApplications } from '../api/applications';
import { discardJobApi, listFeedbackApi, deleteFeedbackApi } from '../api/feedback';
import { MatchScoreBadge } from '../components/matching/MatchScoreBadge';
import { SkillPillList } from '../components/matching/SkillPillList';
import { MatchDetailModal } from '../components/matching/MatchDetailModal';
import { TailoringWorkspaceModal } from '../components/tailoring/TailoringWorkspaceModal';
import { CustomJDPasteModal } from '../components/tailoring/CustomJDPasteModal';
import { DiscardReasonModal } from '../components/matching/DiscardReasonModal';
import { WorkerQueueMonitor } from '../components/matching/WorkerQueueMonitor';
import { QuickAddJobModal } from '../components/jobs/QuickAddJobModal';
import { formatRelativeTime } from '../utils/formatTime';


function getJobExperienceCategory(job: Job): 'entry' | 'mid' | 'senior' {
  const titleLower = (job.title || '').toLowerCase();
  const descLower = (job.description || '').toLowerCase();
  const reqsText = (job.requirements || []).join(' ').toLowerCase();
  const fullText = `${titleLower} ${descLower} ${reqsText}`;

  if (
    /\b(senior|sr\.|iii|iv|v|lead|staff|principal|architect|director|head|manager)\b/i.test(titleLower) ||
    /\b([5-9]|1[0-5])\+?\s*(years?|yrs?)\b/i.test(fullText)
  ) {
    return 'senior';
  }

  if (
    /\b(junior|jr\.|entry|associate|intern|trainee|fresher|graduate)\b/i.test(titleLower) ||
    /\b([0-2])\s*-\s*([1-2])\s*(years?|yrs?)\b/i.test(fullText) ||
    /\b(0|1)\+?\s*(years?|yrs?)\b/i.test(fullText)
  ) {
    return 'entry';
  }

  return 'mid';
}

export const JobDiscoveryPage: React.FC = () => {
  // Candidate Profile
  const [profile, setProfile] = useState<CandidateProfileResponse | null>(null);
  const [isLoadingProfile, setIsLoadingProfile] = useState<boolean>(true);

  // Jobs state
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isLoadingJobs, setIsLoadingJobs] = useState<boolean>(false);
  const [jobError, setJobError] = useState<string | null>(null);

  // Ingestion state
  const [isIngesting, setIsIngesting] = useState<boolean>(false);
  const [ingestionBanner, setIngestionBanner] = useState<string | null>(null);

  // Match cache state
  const [matchesByJobId, setMatchesByJobId] = useState<Record<string, PipelineRunResponse>>({});
  const [analyzingJobIds, setAnalyzingJobIds] = useState<Record<string, boolean>>({});

  // Applications tracking state
  const [trackedJobIds, setTrackedJobIds] = useState<Record<string, string>>({});
  const [isTrackingJobId, setIsTrackingJobId] = useState<Record<string, boolean>>({});

  // Discard / Rocchio Feedback state
  const [discardsByJobId, setDiscardsByJobId] = useState<Record<string, FeedbackResponse>>({});
  const [selectedJobForDiscard, setSelectedJobForDiscard] = useState<Job | null>(null);
  const [isDiscardModalOpen, setIsDiscardModalOpen] = useState<boolean>(false);
  const [isSubmittingDiscard, setIsSubmittingDiscard] = useState<boolean>(false);
  const [feedbackAlert, setFeedbackAlert] = useState<string | null>(null);

  // Filter states
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [locationQuery, setLocationQuery] = useState<string>('');
  const [workType, setWorkType] = useState<'all' | 'remote' | 'onsite'>('all');
  const [employmentType, setEmploymentType] = useState<'all' | 'full-time' | 'contract' | 'part-time'>('all');
  const [experienceLevel, setExperienceLevel] = useState<'all' | 'entry' | 'mid' | 'senior'>('all');
  const [sourceFilter, setSourceFilter] = useState<string>('all');
  const [hideDiscarded, setHideDiscarded] = useState<boolean>(false);

  // Modals state
  const [selectedJobForModal, setSelectedJobForModal] = useState<Job | null>(null);
  const [isMatchModalOpen, setIsMatchModalOpen] = useState<boolean>(false);
  const [isTailorModalOpen, setIsTailorModalOpen] = useState<boolean>(false);
  const [isCustomJDModalOpen, setIsCustomJDModalOpen] = useState<boolean>(false);
  const [isQuickAddModalOpen, setIsQuickAddModalOpen] = useState<boolean>(false);
  const [customTailoringData, setCustomTailoringData] = useState<CustomJDTailoringResponse | null>(null);

  const handleCustomJDTailored = (data: CustomJDTailoringResponse) => {
    const virtualJob: Job = {
      id: data.job_id || `custom_${Date.now()}`,
      title: data.job_title,
      company: data.company_name,
      description: data.recruiter_audit.recruiter_notes || 'Custom pasted job description',
      location: 'External / Remote',
      is_remote: true,
      source: 'custom_paste',
      requirements: (data.recruiter_audit.gap_table || []).map((g) => g.recommended_action),
      created_at: new Date().toISOString(),
    };
    setSelectedJobForModal(virtualJob);
    setCustomTailoringData(data);
    setIsTailorModalOpen(true);
  };

  useEffect(() => {
    loadCandidateProfile();
    loadJobs();
  }, []);

  const loadCandidateProfile = async () => {
    setIsLoadingProfile(true);
    try {
      const p = await getActiveCandidateProfile();
      setProfile(p);
      if (p) {
        loadExistingMatches(p.id);
        loadUserApplications(p.user_id);
        loadUserFeedback(p.id);
      }
    } catch (err: any) {
      console.warn('Could not load active profile:', err.message);
    } finally {
      setIsLoadingProfile(false);
    }
  };

  const loadJobs = async () => {
    setIsLoadingJobs(true);
    setJobError(null);
    try {
      const data = await listJobs({ limit: 100 });
      setJobs(data);
    } catch (err: any) {
      setJobError(err.message || 'Failed to fetch jobs.');
    } finally {
      setIsLoadingJobs(false);
    }
  };

  const loadExistingMatches = async (candidateId: string) => {
    try {
      const matches = await getCandidateJobMatches(candidateId);
      const map: Record<string, PipelineRunResponse> = {};
      matches.forEach((m) => {
        map[m.job_id] = {
          id: m.id,
          candidate_profile_id: m.candidate_profile_id,
          job_id: m.job_id,
          passed_deterministic: m.passed_deterministic,
          vector_score: m.vector_score,
          llm_score: m.llm_score,
          matched_skills: m.matched_skills || [],
          missing_skills: m.missing_skills || [],
          analysis_summary: m.analysis_summary,
          overall_status: m.status,
          current_stage: 'completed',
        };
      });
      setMatchesByJobId(map);
    } catch (err) {
      console.error('Could not load existing matches:', err);
    }
  };

  const loadUserApplications = async (userId?: string) => {
    try {
      const apps = await listApplications(userId);
      const map: Record<string, string> = {};
      apps.forEach((app) => {
        if (app.job_id) {
          map[app.job_id] = app.id;
        }
      });
      setTrackedJobIds(map);
    } catch (err) {
      console.error('Could not load applications:', err);
    }
  };

  const loadUserFeedback = async (candidateId: string) => {
    try {
      const list = await listFeedbackApi(candidateId);
      const map: Record<string, FeedbackResponse> = {};
      list.forEach((f) => {
        if (f.action === 'discard') {
          map[f.job_id] = f;
        }
      });
      setDiscardsByJobId(map);
    } catch (err) {
      console.error('Could not load feedback history:', err);
    }
  };

  const handleOpenDiscard = (job: Job) => {
    setSelectedJobForDiscard(job);
    setIsDiscardModalOpen(true);
  };

  const handleConfirmDiscard = async (reasonCode: string, notes?: string, dislikedSkill?: string) => {
    if (!selectedJobForDiscard) return;
    setIsSubmittingDiscard(true);
    setFeedbackAlert(null);
    try {
      const res = await discardJobApi({
        job_id: selectedJobForDiscard.id,
        candidate_profile_id: profile?.id,
        reason_code: reasonCode,
        notes,
        disliked_skill: dislikedSkill,
      });
      setDiscardsByJobId((prev) => ({
        ...prev,
        [selectedJobForDiscard.id]: res,
      }));
      setFeedbackAlert(
        `Job "${selectedJobForDiscard.title}" marked as discarded.`
      );
      setIsDiscardModalOpen(false);
      setSelectedJobForDiscard(null);
    } catch (err: any) {
      setFeedbackAlert(`Failed to discard job: ${err.message}`);
    } finally {
      setIsSubmittingDiscard(false);
    }
  };

  const handleUndoDiscard = async (jobId: string) => {
    const feedback = discardsByJobId[jobId];
    if (!feedback) return;
    try {
      await deleteFeedbackApi(feedback.id);
      setDiscardsByJobId((prev) => {
        const copy = { ...prev };
        delete copy[jobId];
        return copy;
      });
      setFeedbackAlert('Discard undone. Job restored.');
    } catch (err: any) {
      setFeedbackAlert(`Failed to undo discard: ${err.message}`);
    }
  };

  const handleLoadJobs = async () => {
    setIsIngesting(true);
    setIngestionBanner(null);
    let totalIngested = 0;

    try {
      try {
        const resGreenhouse = await ingestJobs({ source: 'greenhouse', limit: 20 });
        totalIngested += resGreenhouse.new_ingested;
      } catch (err) {}

      try {
        const resLever = await ingestJobs({ source: 'lever', limit: 20 });
        totalIngested += resLever.new_ingested;
      } catch (err) {}

      try {
        const resAdzuna = await ingestJobs({ source: 'adzuna', limit: 15 });
        totalIngested += resAdzuna.new_ingested;
      } catch (err) {}

      try {
        const resRemotive = await ingestJobs({ source: 'remotive', limit: 15 });
        totalIngested += resRemotive.new_ingested;
      } catch (err) {}

      if (totalIngested === 0) {
        try {
          await ingestJobs({ source: 'manual' });
        } catch (err) {}
      }

      await loadJobs();
      setIngestionBanner(`Successfully loaded latest job listings.`);
    } catch (err: any) {
      setIngestionBanner(`Failed to load jobs: ${err.message}`);
    } finally {
      setIsIngesting(false);
    }
  };

  const handleRunPipeline = async (job: Job) => {
    if (!profile) return;
    setAnalyzingJobIds((prev) => ({ ...prev, [job.id]: true }));
    try {
      const result = await runMatchingPipeline(profile.id, job.id);
      setMatchesByJobId((prev) => ({ ...prev, [job.id]: result }));
    } catch (err: any) {
      console.error('Failed to run match pipeline:', err);
    } finally {
      setAnalyzingJobIds((prev) => ({ ...prev, [job.id]: false }));
    }
  };

  const handleTrackApplication = async (job: Job) => {
    if (!profile) return;
    setIsTrackingJobId((prev) => ({ ...prev, [job.id]: true }));
    try {
      let match = matchesByJobId[job.id];
      if (!match || !match.id) {
        match = await runMatchingPipeline(profile.id, job.id);
        setMatchesByJobId((prev) => ({ ...prev, [job.id]: match }));
      }
      if (!match.id) {
        throw new Error('Unable to create job match record for application.');
      }
      const scoreNotes = match.llm_score != null ? `Match score: ${Math.round(match.llm_score)}%` : undefined;
      const newApp = await createApplication({
        job_match_id: match.id,
        user_id: profile.user_id,
        status: 'saved',
        notes: scoreNotes,
      });
      setTrackedJobIds((prev) => ({ ...prev, [job.id]: newApp.id }));
    } catch (err: any) {
      console.error('Failed to track application:', err);
    } finally {
      setIsTrackingJobId((prev) => ({ ...prev, [job.id]: false }));
    }
  };

  // Filtered jobs
  const filteredJobs = (jobs || []).filter((job) => {
    if (!job) return false;
    if (hideDiscarded && discardsByJobId[job.id]) return false;
    if (workType === 'remote' && !job.is_remote) return false;
    if (workType === 'onsite' && job.is_remote) return false;
    if (sourceFilter !== 'all' && (job.source || '').toLowerCase() !== sourceFilter.toLowerCase()) return false;

    if (experienceLevel !== 'all') {
      const cat = getJobExperienceCategory(job);
      if (experienceLevel === 'entry' && cat !== 'entry') return false;
      if (experienceLevel === 'mid' && cat !== 'mid') return false;
      if (experienceLevel === 'senior' && cat !== 'senior') return false;
    }

    if (locationQuery.trim()) {
      const loc = (job.location || '').toLowerCase();
      if (!loc.includes(locationQuery.toLowerCase().trim())) return false;
    }

    if (employmentType !== 'all') {
      const fullText = `${job.title} ${job.description} ${(job.requirements || []).join(' ')}`.toLowerCase();
      if (employmentType === 'contract' && !fullText.includes('contract') && !fullText.includes('freelance')) return false;
      if (employmentType === 'full-time' && !fullText.includes('full-time') && !fullText.includes('full time')) return false;
      if (employmentType === 'part-time' && !fullText.includes('part-time') && !fullText.includes('part time')) return false;
    }

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      const matchTitle = (job.title || '').toLowerCase().includes(query);
      const matchCompany = (job.company || '').toLowerCase().includes(query);
      const reqs = job.requirements || [];
      const matchReq = reqs.some((r) => r && r.toLowerCase().includes(query));
      if (!matchTitle && !matchCompany && !matchReq) return false;
    }
    return true;
  });

  const hasActiveFilters =
    searchQuery.trim() !== '' ||
    locationQuery.trim() !== '' ||
    workType !== 'all' ||
    employmentType !== 'all' ||
    experienceLevel !== 'all' ||
    sourceFilter !== 'all' ||
    hideDiscarded;

  const clearAllFilters = () => {
    setSearchQuery('');
    setLocationQuery('');
    setWorkType('all');
    setEmploymentType('all');
    setExperienceLevel('all');
    setSourceFilter('all');
    setHideDiscarded(false);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">
            Jobs
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Discover opportunities, analyze skill matches, and tailor application materials.
          </p>
        </div>

        {/* Ingestion & Custom JD Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsQuickAddModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition-all"
            title="Import custom job via ATS URL (Greenhouse, Lever) or paste text"
          >
            <Plus className="w-3.5 h-3.5" />
            + Import Job / URL
          </button>
          <button
            onClick={() => setIsCustomJDModalOpen(true)}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition-all"
            title="Paste any external Job Description to tailor resume, audit gaps, and generate cold message"
          >
            <Sparkles className="w-3.5 h-3.5" />
            + Paste External JD
          </button>
          <button
            onClick={handleLoadJobs}
            disabled={isIngesting || isLoadingJobs}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white transition-colors disabled:opacity-50"
            title="Load live jobs from connected API sources"
          >
            <Download className={`w-3.5 h-3.5 ${isIngesting ? 'animate-spin' : ''}`} />
            {isIngesting ? 'Loading...' : 'Load Jobs'}
          </button>
          <button
            onClick={loadJobs}
            disabled={isLoadingJobs}
            className="p-1.5 rounded-lg text-slate-600 hover:text-slate-900 bg-white hover:bg-slate-50 border border-slate-200 transition-colors"
            title="Refresh current jobs list"
          >
            <RotateCw className={`w-4 h-4 ${isLoadingJobs ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Background Worker Daemon & Pipeline Queue Monitor */}
      <WorkerQueueMonitor onCycleTriggered={loadJobs} />

      {/* Feedback Status Alert */}
      {feedbackAlert && (
        <div className="p-3 bg-slate-100 border border-slate-200 rounded-lg text-xs text-slate-700 flex items-center justify-between">
          <span>{feedbackAlert}</span>
          <button
            onClick={() => setFeedbackAlert(null)}
            className="text-slate-400 hover:text-slate-600 p-0.5"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Ingestion Status Banner */}
      {ingestionBanner && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-800 flex items-center justify-between">
          <span>{ingestionBanner}</span>
          <button
            onClick={() => setIngestionBanner(null)}
            className="text-slate-400 hover:text-slate-600 p-0.5"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Candidate Profile Context Banner */}
      {profile ? (
        <div className="p-4 bg-white border border-slate-200 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm">
          <div className="space-y-1">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-blue-600">
              Active Candidate Profile
            </span>
            <h3 className="text-sm font-semibold text-slate-900">
              {profile.headline || 'Candidate Profile'}
            </h3>
            <p className="text-xs text-slate-500 line-clamp-1 max-w-lg">
              {profile.summary || 'Verified profile data stored in PostgreSQL'}
            </p>
            <div className="flex flex-wrap gap-1 mt-1">
              {(profile.skills || []).slice(0, 8).map((s, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 rounded text-[10px] bg-slate-100 text-slate-700 border border-slate-200"
                >
                  {s}
                </span>
              ))}
              {(profile.skills || []).length > 8 && (
                <span className="text-[10px] text-slate-400 font-mono">
                  +{(profile.skills || []).length - 8} more
                </span>
              )}
            </div>
          </div>

          <div className="text-xs text-slate-500 sm:text-right shrink-0">
            <div>
              Target Roles:{' '}
              <span className="text-slate-800 font-medium">
                {(profile.target_titles || []).slice(0, 2).join(', ') || 'Tech'}
              </span>
            </div>
            <div className="text-[11px] text-slate-400 font-mono mt-0.5">
              ID: {profile.id.slice(0, 8)}...
            </div>
          </div>
        </div>
      ) : isLoadingProfile ? (
        <div className="p-4 bg-white border border-slate-200 rounded-xl text-xs text-slate-400 italic">
          Loading profile context...
        </div>
      ) : (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800">
          No profile found. Please upload a resume or create your profile in the Profile tab.
        </div>
      )}

      {/* Comprehensive Filter Section */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 sm:p-5 space-y-3 shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
              Filters & Search
            </h3>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-500">
              Showing <strong className="text-slate-900 font-semibold">{filteredJobs.length}</strong> of{' '}
              <strong className="text-slate-700">{jobs.length}</strong> jobs
            </span>
            {hasActiveFilters && (
              <button
                onClick={clearAllFilters}
                className="flex items-center gap-1 text-[11px] font-medium text-red-600 hover:text-red-800 bg-red-50 hover:bg-red-100 px-2 py-0.5 rounded border border-red-200 transition-colors"
              >
                <X className="w-3 h-3" />
                Clear
              </button>
            )}
          </div>
        </div>

        {/* Inputs & Dropdowns Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-2.5">
          {/* Keyword Search Input */}
          <div className="lg:col-span-2 relative">
            <Search className="absolute left-3 top-2.5 w-3.5 h-3.5 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Role, company, or tech stack..."
              className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500 font-sans"
            />
          </div>

          {/* Location Filter Input */}
          <div className="relative">
            <MapPin className="absolute left-3 top-2.5 w-3.5 h-3.5 text-slate-400" />
            <input
              type="text"
              value={locationQuery}
              onChange={(e) => setLocationQuery(e.target.value)}
              placeholder="Location..."
              className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500 font-sans"
            />
          </div>

          {/* Experience Level Dropdown */}
          <div className="relative">
            <Award className="absolute left-3 top-2.5 w-3.5 h-3.5 text-slate-400" />
            <select
              value={experienceLevel}
              onChange={(e) => setExperienceLevel(e.target.value as any)}
              className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-700 focus:outline-none focus:border-blue-500 appearance-none cursor-pointer"
            >
              <option value="all">All Levels</option>
              <option value="entry">Entry (0-2 Yrs)</option>
              <option value="mid">Mid (2-5 Yrs)</option>
              <option value="senior">Senior (5+ Yrs)</option>
            </select>
          </div>

          {/* Work Type Dropdown */}
          <div className="relative">
            <Globe className="absolute left-3 top-2.5 w-3.5 h-3.5 text-slate-400" />
            <select
              value={workType}
              onChange={(e) => setWorkType(e.target.value as any)}
              className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-700 focus:outline-none focus:border-blue-500 appearance-none cursor-pointer"
            >
              <option value="all">All Locations</option>
              <option value="remote">Remote Only</option>
              <option value="onsite">On-site / Office</option>
            </select>
          </div>

          {/* Employment Type Dropdown */}
          <div className="relative">
            <Clock className="absolute left-3 top-2.5 w-3.5 h-3.5 text-slate-400" />
            <select
              value={employmentType}
              onChange={(e) => setEmploymentType(e.target.value as any)}
              className="w-full bg-white border border-slate-300 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-700 focus:outline-none focus:border-blue-500 appearance-none cursor-pointer"
            >
              <option value="all">All Types</option>
              <option value="full-time">Full-time</option>
              <option value="contract">Contract</option>
              <option value="part-time">Part-time</option>
            </select>
          </div>
        </div>

        {/* Quick-Select Badges Rows */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-100">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] font-medium text-slate-500">Source:</span>
            {[
              { id: 'all', label: 'All' },
              { id: 'greenhouse', label: 'Greenhouse' },
              { id: 'lever', label: 'Lever' },
              { id: 'adzuna', label: 'Adzuna' },
              { id: 'remotive', label: 'Remotive' },
              { id: 'manual', label: 'Manual/Direct' },
            ].map((src) => (
              <button
                key={src.id}
                onClick={() => setSourceFilter(src.id)}
                className={`px-2 py-0.5 rounded text-xs font-medium border transition-colors ${
                  sourceFilter === src.id
                    ? 'bg-blue-50 text-blue-700 border-blue-300'
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                }`}
              >
                {src.label}
              </button>
            ))}
          </div>

          {/* Hide Discarded Checkbox Toggle */}
          <label className="flex items-center gap-1.5 text-xs text-slate-600 cursor-pointer">
            <input
              type="checkbox"
              checked={hideDiscarded}
              onChange={(e) => setHideDiscarded(e.target.checked)}
              className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            <span>Hide Discarded ({Object.keys(discardsByJobId).length})</span>
          </label>
        </div>
      </div>

      {/* Jobs Grid */}
      {isLoadingJobs ? (
        <div className="py-20 text-center space-y-2">
          <RotateCw className="w-6 h-6 text-slate-400 animate-spin mx-auto" />
          <p className="text-xs text-slate-500">Loading jobs...</p>
        </div>
      ) : jobError ? (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-xs text-red-600">
          {jobError}
        </div>
      ) : filteredJobs.length === 0 ? (
        <div className="py-16 text-center border border-dashed border-slate-300 rounded-xl space-y-2 bg-white">
          <Briefcase className="w-8 h-8 text-slate-400 mx-auto" />
          <p className="text-sm font-semibold text-slate-700">No Jobs Found</p>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Try adjusting your search filters or click "Load Jobs" above to import live job postings.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {filteredJobs.map((job) => {
            const match = matchesByJobId[job.id];
            const isAnalyzing = analyzingJobIds[job.id];
            const isTracked = !!trackedJobIds[job.id];
            const isTracking = isTrackingJobId[job.id];
            const isDiscarded = !!discardsByJobId[job.id];

            return (
              <div
                key={job.id}
                className={`bg-white border rounded-xl p-5 shadow-sm hover:shadow transition-shadow flex flex-col justify-between space-y-3 ${
                  isDiscarded
                    ? 'border-slate-200 opacity-60 bg-slate-50'
                    : 'border-slate-200'
                }`}
              >
                {/* Job Card Header */}
                <div>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="text-[15px] font-semibold text-slate-900 leading-snug">
                        {job.title}
                      </h3>
                      <div className="flex items-center gap-1.5 text-xs text-slate-500 mt-1">
                        <span className="flex items-center gap-1 font-medium text-slate-700">
                          <Building className="w-3.5 h-3.5 text-slate-400" />
                          {job.company}
                        </span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5 text-slate-400" />
                          {job.location || (job.is_remote ? 'Remote' : 'Location N/A')}
                        </span>
                      </div>

                      {/* Freshness & Origin Timestamps */}
                      <div className="flex flex-wrap items-center gap-2 mt-1.5 text-[11px] text-slate-500">
                        {job.posted_at && (
                          <span
                            className="flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-medium border border-emerald-100"
                            title={`Original posting date: ${new Date(job.posted_at).toLocaleString()}`}
                          >
                            <Clock className="w-3 h-3 text-emerald-600" />
                            Posted {formatRelativeTime(job.posted_at)}
                          </span>
                        )}
                        {job.created_at && (
                          <span
                            className="flex items-center gap-1 text-slate-500"
                            title={`Ingested into system: ${new Date(job.created_at).toLocaleString()}`}
                          >
                            Added {formatRelativeTime(job.created_at)}
                          </span>
                        )}
                      </div>
                    </div>

                    {match ? (
                      <MatchScoreBadge score={match.llm_score} size="md" />
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-100 text-slate-600 border border-slate-200">
                        {job.source}
                      </span>
                    )}
                  </div>

                  {/* Requirements Tags */}
                  <div className="flex flex-wrap gap-1 mt-2.5">
                    {(job.requirements || []).slice(0, 5).map((req, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 rounded text-[11px] bg-slate-100 text-slate-700 border border-slate-200"
                      >
                        {req}
                      </span>
                    ))}
                    {(job.requirements || []).length > 5 && (
                      <span className="text-[10px] text-slate-400 font-mono py-0.5">
                        +{(job.requirements || []).length - 5}
                      </span>
                    )}
                  </div>

                  {/* Skills breakdown */}
                  {match && (
                    <div className="mt-3 pt-2.5 border-t border-slate-100">
                      <SkillPillList
                        matchedSkills={match.matched_skills}
                        missingSkills={match.missing_skills}
                        maxDisplay={4}
                      />
                    </div>
                  )}
                </div>

                {/* Card Actions */}
                <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    {/* Direct ATS Apply / Source Links */}
                    {(job.apply_url || job.url) && (
                      <a
                        href={job.apply_url || job.url || '#'}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white transition-all shadow-sm"
                        title="Open direct job application page"
                      >
                        <span>Apply</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                    {job.source_url && job.source_url !== (job.apply_url || job.url) && (
                      <a
                        href={job.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-[11px] font-medium text-slate-500 hover:text-slate-800 transition-colors"
                        title="View job posting details"
                      >
                        <span>Details</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}

                    {match ? (
                      <button
                        onClick={() => {
                          setSelectedJobForModal(job);
                          setIsMatchModalOpen(true);
                        }}
                        className="flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-800 transition-colors"
                      >
                        <span>Match Breakdown</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    ) : (
                      <button
                        onClick={() => handleRunPipeline(job)}
                        disabled={isAnalyzing}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white transition-colors disabled:opacity-50"
                      >
                        <RotateCw className={`w-3.5 h-3.5 ${isAnalyzing ? 'animate-spin' : ''}`} />
                        {isAnalyzing ? 'Analyzing...' : 'Analyze Match'}
                      </button>
                    )}
                  </div>

                  <div className="flex items-center gap-1.5">
                    {/* Tailor Docs Button */}
                    <button
                      onClick={() => {
                        setSelectedJobForModal(job);
                        setIsTailorModalOpen(true);
                      }}
                      className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition-colors"
                      title="Tailor grounded resume bullets and cover letter"
                    >
                      <FileText className="w-3.5 h-3.5 text-slate-500" />
                      <span>Tailor</span>
                    </button>

                    {/* Track in Kanban Button */}
                    <button
                      onClick={() => handleTrackApplication(job)}
                      disabled={isTracked || isTracking}
                      className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                        isTracked
                          ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                          : 'bg-white hover:bg-slate-50 text-slate-700 border border-slate-200'
                      }`}
                    >
                      {isTracked ? (
                        <>
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                          <span>Tracked</span>
                        </>
                      ) : (
                        <>
                          <BookmarkPlus className="w-3.5 h-3.5 text-slate-500" />
                          <span>{isTracking ? 'Saving...' : 'Track'}</span>
                        </>
                      )}
                    </button>

                    {/* Discard Action */}
                    {isDiscarded ? (
                      <div className="flex items-center gap-1 bg-slate-100 border border-slate-200 px-2 py-1 rounded-md text-slate-600 text-[11px]">
                        <span className="capitalize">
                          {discardsByJobId[job.id]?.reason_code?.replace(/_/g, ' ')}
                        </span>
                        <button
                          onClick={() => handleUndoDiscard(job.id)}
                          className="p-0.5 hover:bg-slate-200 rounded transition-colors text-slate-400 hover:text-slate-700"
                          title="Undo Discard"
                        >
                          <RotateCcw className="w-3 h-3" />
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => handleOpenDiscard(job)}
                        className="flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-red-600 hover:bg-red-50 border border-transparent hover:border-red-200 transition-colors"
                        title="Discard job"
                      >
                        <ThumbsDown className="w-3.5 h-3.5" />
                        <span>Discard</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Match Detail Modal */}
      {selectedJobForModal && (
        <MatchDetailModal
          job={selectedJobForModal}
          pipelineResult={matchesByJobId[selectedJobForModal.id] || null}
          isOpen={isMatchModalOpen}
          onClose={() => setIsMatchModalOpen(false)}
          onOpenTailoring={() => {
            setIsMatchModalOpen(false);
            setIsTailorModalOpen(true);
          }}
          onTrackApplication={() => handleTrackApplication(selectedJobForModal)}
          isTracking={isTrackingJobId[selectedJobForModal.id]}
        />
      )}

      {/* Tailoring Workspace Modal */}
      {selectedJobForModal && profile && (
        <TailoringWorkspaceModal
          candidateProfileId={profile.id}
          job={selectedJobForModal}
          applicationId={trackedJobIds[selectedJobForModal.id] || null}
          isOpen={isTailorModalOpen}
          initialCustomData={customTailoringData}
          onClose={() => {
            setIsTailorModalOpen(false);
            setCustomTailoringData(null);
          }}
          onSavedToApplication={() => {
            if (profile) loadUserApplications(profile.user_id);
          }}
        />
      )}

      {/* Custom External JD Paste Modal */}
      <CustomJDPasteModal
        isOpen={isCustomJDModalOpen}
        onClose={() => setIsCustomJDModalOpen(false)}
        onSuccess={handleCustomJDTailored}
      />

      {/* Quick Add Custom Job Modal (URL or Paste) */}
      <QuickAddJobModal
        isOpen={isQuickAddModalOpen}
        onClose={() => setIsQuickAddModalOpen(false)}
        onJobAdded={() => loadJobs()}
      />

      {/* Discard Reason Modal */}
      {selectedJobForDiscard && (
        <DiscardReasonModal
          job={selectedJobForDiscard}
          isOpen={isDiscardModalOpen}
          onClose={() => {
            setIsDiscardModalOpen(false);
            setSelectedJobForDiscard(null);
          }}
          onConfirm={handleConfirmDiscard}
          isSubmitting={isSubmittingDiscard}
        />
      )}
    </div>
  );
};
