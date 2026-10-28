import React, { useState, useEffect } from 'react';
import {
  Briefcase,
  Search,
  RotateCw,
  BookmarkPlus,
  MapPin,
  Download,
  X,
  Clock,
  Award,
  RotateCcw,
  Sparkles,
  ExternalLink,
  Plus,
  LayoutGrid,
  Columns,
  Check,
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

const INDIAN_LOCATIONS_REGEX = /\b(india|bengaluru|bangalore|mumbai|delhi|hyderabad|pune|chennai|noida|gurugram|gurgaon|kolkata|ahmedabad|jaipur|kochi|chandigarh|indore|trivandrum|kerala|karnataka|maharashtra|telangana|tamil nadu|mh|ka|ts|gj|wb|mp)\b/i;

function matchesLocation(jobLoc: string | undefined | null, query: string): boolean {
  if (!query || !query.trim()) return true;
  const q = query.trim().toLowerCase();
  const loc = (jobLoc || '').toLowerCase();
  if (!loc) return q === 'india';

  if (q === 'india') {
    return loc.includes('india') || INDIAN_LOCATIONS_REGEX.test(loc);
  }
  if (q === 'delhi') {
    return loc.includes('delhi') || loc.includes('noida') || loc.includes('gurgaon') || loc.includes('gurugram') || loc.includes('ncr');
  }
  if (q === 'bengaluru') {
    return loc.includes('bengaluru') || loc.includes('bangalore') || loc.includes('ka');
  }
  if (q === 'mumbai') {
    return loc.includes('mumbai') || loc.includes('navi mumbai') || loc.includes('mh');
  }
  if (q === 'pune') {
    return loc.includes('pune') || loc.includes('pimpri') || loc.includes('mh');
  }
  if (q === 'hyderabad') {
    return loc.includes('hyderabad') || loc.includes('ts') || loc.includes('telangana');
  }
  if (q === 'chennai') {
    return loc.includes('chennai') || loc.includes('tamil nadu');
  }
  if (q === 'noida') {
    return loc.includes('noida') || loc.includes('gurgaon') || loc.includes('gurugram') || loc.includes('delhi');
  }
  return loc.includes(q);
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
  const [workType, setWorkType] = useState<'all' | 'remote' | 'hybrid' | 'onsite'>('all');
  const [employmentType, setEmploymentType] = useState<'all' | 'full-time' | 'contract' | 'part-time'>('all');
  const [experienceLevel, setExperienceLevel] = useState<'all' | 'entry' | 'mid' | 'senior'>('all');
  const [sourceFilter, setSourceFilter] = useState<string>('all');
  const [hideDiscarded, setHideDiscarded] = useState<boolean>(false);

  // View mode & selection state for LinkedIn-style Master-Detail Split View
  const [viewMode, setViewMode] = useState<'split' | 'grid'>('split');
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

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
      const queryTerm = searchQuery.trim() || (profile?.target_titles?.[0]) || 'Software Engineer';
      let locTerm = locationQuery.trim();
      if (!locTerm || locTerm.toLowerCase() === 'remote') {
        locTerm = 'India';
      }
      const isRemoteParam = workType === 'remote' ? true : workType === 'onsite' ? false : undefined;
      const jobTypeParam = employmentType !== 'all' ? employmentType : undefined;

      // Ingest live LinkedIn jobs
      try {
        const resLinkedIn = await ingestJobs({
          source: 'linkedin',
          limit: 15,
          search_term: queryTerm,
          location: locTerm,
          is_remote: isRemoteParam,
          job_type: jobTypeParam,
        });
        totalIngested += resLinkedIn.new_ingested;
      } catch (err) {}

      // Ingest live Indeed jobs
      try {
        const resIndeed = await ingestJobs({
          source: 'indeed',
          limit: 15,
          search_term: queryTerm,
          location: locTerm,
          is_remote: isRemoteParam,
          job_type: jobTypeParam,
        });
        totalIngested += resIndeed.new_ingested;
      } catch (err) {}

      try {
        const resGreenhouse = await ingestJobs({ source: 'greenhouse', limit: 15 });
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

    const fullJobText = `${job.title} ${job.location || ''} ${job.description || ''}`.toLowerCase();
    const isJobHybrid = fullJobText.includes('hybrid');
    const isJobRemote = job.is_remote || fullJobText.includes('remote') || fullJobText.includes('work from home');

    if (workType === 'remote' && (!isJobRemote || isJobHybrid)) return false;
    if (workType === 'hybrid' && !isJobHybrid) return false;
    if (workType === 'onsite' && (isJobRemote || isJobHybrid)) return false;

    if (sourceFilter !== 'all' && (job.source || '').toLowerCase() !== sourceFilter.toLowerCase()) return false;

    if (experienceLevel !== 'all') {
      const cat = getJobExperienceCategory(job);
      if (experienceLevel === 'entry' && cat !== 'entry') return false;
      if (experienceLevel === 'mid' && cat !== 'mid') return false;
      if (experienceLevel === 'senior' && cat !== 'senior') return false;
    }

    if (locationQuery.trim()) {
      if (!matchesLocation(job.location, locationQuery)) return false;
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

  // Synchronize selected job for master-detail split view
  useEffect(() => {
    if (filteredJobs.length > 0) {
      if (!selectedJobId || !filteredJobs.some((j) => j.id === selectedJobId)) {
        setSelectedJobId(filteredJobs[0].id);
      }
    } else {
      setSelectedJobId(null);
    }
  }, [filteredJobs, selectedJobId]);

  const activeJob = filteredJobs.find((j) => j.id === selectedJobId) || filteredJobs[0] || null;
  const activeMatch = activeJob ? matchesByJobId[activeJob.id] : null;

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

  const TRENDING_KEYWORDS = ['AI/ML', 'Gen AI', 'LLM', 'Backend', 'Python', 'FastAPI', 'React', 'DevOps'];

  return (
    <div className="max-w-7xl mx-auto px-3 sm:px-6 py-6 space-y-4">
      {/* LinkedIn Screenshot 3 Style: Candidate Preferences & Header Banner */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-4 sm:p-5 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          {/* Avatar with #OPENTOWORK ring badge */}
          <div className="relative shrink-0">
            <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-blue-600 via-indigo-600 to-sky-500 p-0.5 ring-2 ring-emerald-500 shadow-sm flex items-center justify-center text-white font-bold text-lg">
              {profile?.headline ? profile.headline.charAt(0).toUpperCase() : 'M'}
            </div>
            <span className="absolute -bottom-1 -right-1 bg-emerald-600 text-white text-[8px] font-bold px-1.5 py-0.2 rounded-full border border-white tracking-wider">
              #OPEN
            </span>
          </div>

          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <h1 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight">
                Jobs based on your preferences
              </h1>
              <span className="text-[10px] text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full font-semibold">
                ✓ Verified
              </span>
            </div>
            <p className="text-xs text-slate-500 line-clamp-1 max-w-2xl font-normal">
              {isLoadingProfile
                ? 'Loading preferences from profile...'
                : `${(profile?.target_titles || []).slice(0, 4).join(' or ') || 'Software Engineer or AI/ML Engineer'}, on-site, hybrid or remote in India`}
            </p>
          </div>
        </div>

        {/* Global Action CTAs */}
        <div className="flex items-center gap-2 shrink-0 w-full sm:w-auto justify-end">
          <button
            onClick={() => setIsQuickAddModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition-all"
            title="Import custom job via ATS URL (Greenhouse, Lever) or paste text"
          >
            <Plus className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">+ Import Job / URL</span>
            <span className="sm:hidden">+ Import</span>
          </button>
          <button
            onClick={() => setIsCustomJDModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition-all"
            title="Paste any external Job Description to tailor resume, audit gaps, and generate cold message"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">+ Paste JD</span>
            <span className="sm:hidden">Paste</span>
          </button>
          <button
            onClick={handleLoadJobs}
            disabled={isIngesting || isLoadingJobs}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-[#0a66c2] hover:bg-[#004182] text-white shadow-sm transition-all disabled:opacity-50"
            title="Load live jobs from connected API sources (LinkedIn, Indeed, etc.)"
          >
            <Download className={`w-3.5 h-3.5 ${isIngesting ? 'animate-spin' : ''}`} />
            {isIngesting ? 'Loading...' : 'Load Live Jobs'}
          </button>
          <button
            onClick={loadJobs}
            disabled={isLoadingJobs}
            className="p-1.5 rounded-xl text-slate-600 hover:text-slate-900 bg-white hover:bg-slate-50 border border-slate-200 shadow-sm transition-colors"
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
        <div className="p-3 bg-slate-100 border border-slate-200 rounded-xl text-xs text-slate-700 flex items-center justify-between shadow-sm">
          <span>{feedbackAlert}</span>
          <button onClick={() => setFeedbackAlert(null)} className="text-slate-400 hover:text-slate-600 p-0.5">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Ingestion Status Banner */}
      {ingestionBanner && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-800 flex items-center justify-between shadow-sm">
          <span>{ingestionBanner}</span>
          <button onClick={() => setIngestionBanner(null)} className="text-slate-400 hover:text-slate-600 p-0.5">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* LinkedIn Screenshot 2 Style: Search & Filters Bar */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-sm space-y-3">
        {/* Search Inputs & View Mode Switch Row */}
        <div className="flex flex-col md:flex-row items-center gap-2.5">
          {/* Keyword Search */}
          <div className="flex-1 relative w-full">
            <Search className="absolute left-3.5 top-2.5 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by title, skill, or company (e.g. Python, AI/ML, Full Stack)..."
              className="w-full bg-slate-50/70 hover:bg-white focus:bg-white border border-slate-200 focus:border-[#0a66c2] rounded-xl pl-10 pr-4 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none transition-all shadow-inner"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Location Input */}
          <div className="w-full md:w-64 relative">
            <MapPin className="absolute left-3.5 top-2.5 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={locationQuery}
              onChange={(e) => setLocationQuery(e.target.value)}
              placeholder="City, State, or India..."
              className="w-full bg-slate-50/70 hover:bg-white focus:bg-white border border-slate-200 focus:border-[#0a66c2] rounded-xl pl-10 pr-4 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none transition-all shadow-inner"
            />
            {locationQuery && (
              <button
                onClick={() => setLocationQuery('')}
                className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* View Mode Toggle Button */}
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl shrink-0 self-end md:self-auto">
            <button
              onClick={() => setViewMode('split')}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                viewMode === 'split'
                  ? 'bg-white text-[#0a66c2] shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
              title="Split View (LinkedIn Style Master-Detail)"
            >
              <Columns className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Split View</span>
            </button>
            <button
              onClick={() => setViewMode('grid')}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                viewMode === 'grid'
                  ? 'bg-white text-[#0a66c2] shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
              title="Grid View (2-Column Cards)"
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Grid View</span>
            </button>
          </div>
        </div>

        {/* Quick Tech Keyword Chips (LinkedIn Screenshot 2 style) */}
        <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mr-1">Trending:</span>
          {TRENDING_KEYWORDS.map((chip) => {
            const isChipActive = searchQuery.toLowerCase() === chip.toLowerCase();
            return (
              <button
                key={chip}
                onClick={() => setSearchQuery(isChipActive ? '' : chip)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                  isChipActive
                    ? 'bg-[#0a66c2] text-white shadow-sm ring-1 ring-[#0a66c2]'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                {chip}
              </button>
            );
          })}
        </div>

        {/* Filter Badges & Toggles Row */}
        <div className="space-y-2 pt-2 border-t border-slate-100 text-xs">
          <div className="flex flex-wrap items-center justify-between gap-2">
            {/* Sources Filter */}
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="text-[11px] font-semibold text-slate-500">Source:</span>
              {[
                { id: 'all', label: 'All' },
                { id: 'linkedin', label: 'LinkedIn', color: 'text-[#0a66c2]' },
                { id: 'indeed', label: 'Indeed', color: 'text-indigo-600' },
                { id: 'greenhouse', label: 'Greenhouse' },
                { id: 'lever', label: 'Lever' },
                { id: 'adzuna', label: 'Adzuna' },
                { id: 'remotive', label: 'Remotive' },
                { id: 'manual', label: 'Direct/ATS' },
              ].map((src) => (
                <button
                  key={src.id}
                  onClick={() => setSourceFilter(src.id)}
                  className={`px-2.5 py-0.5 rounded-full text-xs font-medium border transition-colors ${
                    sourceFilter === src.id
                      ? 'bg-blue-50 text-[#0a66c2] border-[#0a66c2]/40 font-semibold shadow-sm'
                      : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  {src.label}
                </button>
              ))}
            </div>

            {/* Clear & Hide Discarded Controls */}
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-1.5 text-xs text-slate-600 cursor-pointer">
                <input
                  type="checkbox"
                  checked={hideDiscarded}
                  onChange={(e) => setHideDiscarded(e.target.checked)}
                  className="rounded border-slate-300 text-[#0a66c2] focus:ring-[#0a66c2]"
                />
                <span>Hide Discarded ({Object.keys(discardsByJobId).length})</span>
              </label>

              {hasActiveFilters && (
                <button
                  onClick={clearAllFilters}
                  className="flex items-center gap-1 text-[11px] font-medium text-red-600 hover:text-red-800 bg-red-50 hover:bg-red-100 px-2 py-0.5 rounded-full border border-red-200 transition-colors"
                >
                  <X className="w-3 h-3" />
                  Clear All
                </button>
              )}
            </div>
          </div>

          {/* Region & Work Mode Pills Row */}
          <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-100/60">
            {/* Geographic Region Pills */}
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="text-[11px] font-semibold text-slate-500">Region:</span>
              {[
                { id: 'India', label: '🇮🇳 All India' },
                { id: 'Bengaluru', label: 'Bengaluru' },
                { id: 'Mumbai', label: 'Mumbai' },
                { id: 'Hyderabad', label: 'Hyderabad' },
                { id: 'Pune', label: 'Pune' },
                { id: 'Delhi', label: 'Delhi/NCR' },
                { id: 'Chennai', label: 'Chennai' },
                { id: 'Noida', label: 'Noida/Gurgaon' },
              ].map((loc) => {
                const isActive = locationQuery.toLowerCase() === loc.id.toLowerCase();
                return (
                  <button
                    key={loc.id}
                    onClick={() => setLocationQuery(isActive ? '' : loc.id)}
                    className={`px-2.5 py-0.5 rounded-full text-[11px] font-medium border transition-colors ${
                      isActive
                        ? 'bg-emerald-50 text-emerald-800 border-emerald-300 font-semibold shadow-sm'
                        : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    {loc.label}
                  </button>
                );
              })}
            </div>

            {/* Work Mode Arrangement Pills */}
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="text-[11px] font-semibold text-slate-500">Mode:</span>
              {[
                { id: 'all', label: 'All Modes' },
                { id: 'remote', label: '🏠 Remote' },
                { id: 'hybrid', label: '🏢 Hybrid' },
                { id: 'onsite', label: '🏢 On-site' },
              ].map((mode) => (
                <button
                  key={mode.id}
                  onClick={() => setWorkType(mode.id as any)}
                  className={`px-2.5 py-0.5 rounded-full text-[11px] font-medium border transition-colors ${
                    workType === mode.id
                      ? 'bg-purple-50 text-purple-700 border-purple-300 font-semibold shadow-sm'
                      : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  {mode.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Main Jobs Section: Loading, Error, Empty, or Jobs View */}
      {isLoadingJobs ? (
        <div className="py-24 text-center space-y-3 bg-white border border-slate-200 rounded-2xl">
          <RotateCw className="w-8 h-8 text-[#0a66c2] animate-spin mx-auto" />
          <p className="text-sm font-semibold text-slate-700">Loading live opportunities...</p>
          <p className="text-xs text-slate-400">Fetching listings from LinkedIn, Indeed, Greenhouse & Lever</p>
        </div>
      ) : jobError ? (
        <div className="p-4 bg-red-50 border border-red-200 rounded-2xl text-xs text-red-600">
          {jobError}
        </div>
      ) : filteredJobs.length === 0 ? (
        <div className="py-20 text-center border border-dashed border-slate-300 rounded-2xl space-y-3 bg-white shadow-sm">
          <Briefcase className="w-10 h-10 text-slate-400 mx-auto" />
          <h3 className="text-sm font-bold text-slate-800">No Jobs Found Matching Criteria</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Try adjusting your search terms, changing the location/mode filters, or click "Load Live Jobs" to import fresh postings.
          </p>
          <button
            onClick={clearAllFilters}
            className="px-4 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
          >
            Reset All Filters
          </button>
        </div>
      ) : viewMode === 'split' ? (
        /* ========================================================================= */
        /* LINKEDIN SCREENSHOT 2: SPLIT VIEW (MASTER-DETAIL 2-COLUMN LAYOUT)         */
        /* ========================================================================= */
        <div className="flex flex-col lg:flex-row gap-4 items-start">
          {/* Left Column: Job List (42% Width) */}
          <div className="w-full lg:w-[42%] space-y-2.5">
            <div className="flex items-center justify-between px-1 text-xs text-slate-500 font-medium">
              <span>
                Showing <strong className="text-slate-900 font-bold">{filteredJobs.length}</strong> of{' '}
                <strong>{jobs.length}</strong> jobs
              </span>
              <span>Sorted by Most Recent</span>
            </div>

            <div className="max-h-[calc(100vh-220px)] overflow-y-auto pr-1 space-y-2">
              {filteredJobs.map((job) => {
                const isSelected = activeJob?.id === job.id;
                const match = matchesByJobId[job.id];
                const isTracked = !!trackedJobIds[job.id];
                const isDiscarded = !!discardsByJobId[job.id];

                // Company Avatar Initial
                const initial = (job.company || 'C').charAt(0).toUpperCase();

                return (
                  <div
                    key={job.id}
                    onClick={() => setSelectedJobId(job.id)}
                    className={`p-4 rounded-xl border transition-all cursor-pointer relative flex gap-3.5 ${
                      isSelected
                        ? 'bg-blue-50/50 border-[#0a66c2] shadow-sm ring-1 ring-[#0a66c2]/30'
                        : isDiscarded
                        ? 'bg-slate-50 border-slate-200 opacity-60'
                        : 'bg-white hover:bg-slate-50/80 border-slate-200/90 shadow-sm'
                    }`}
                  >
                    {/* Company Initial Square Icon (LinkedIn style) */}
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-slate-100 to-slate-200 border border-slate-200 flex items-center justify-center shrink-0 text-slate-700 font-bold text-sm shadow-inner">
                      {initial}
                    </div>

                    {/* Job Card Content */}
                    <div className="flex-1 min-w-0 pr-6">
                      <h3
                        className={`text-sm font-bold leading-snug line-clamp-1 transition-colors ${
                          isSelected ? 'text-[#0a66c2]' : 'text-slate-900 hover:text-[#0a66c2]'
                        }`}
                      >
                        {job.title}
                      </h3>

                      <p className="text-xs text-slate-600 font-medium mt-0.5 truncate">
                        {job.company}
                      </p>

                      <div className="flex items-center gap-1.5 text-[11px] text-slate-500 mt-1 truncate">
                        <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
                        <span className="truncate">{job.location || 'India'}</span>
                        {job.is_remote && (
                          <span className="text-[10px] text-purple-700 bg-purple-50 px-1.5 py-0.2 rounded font-semibold shrink-0">
                            Remote
                          </span>
                        )}
                        {(job.title + ' ' + (job.location || '') + ' ' + (job.description || '')).toLowerCase().includes('hybrid') && (
                          <span className="text-[10px] text-blue-700 bg-blue-50 px-1.5 py-0.2 rounded font-semibold shrink-0">
                            Hybrid
                          </span>
                        )}
                      </div>

                      {/* Card Footer Badges */}
                      <div className="flex flex-wrap items-center gap-1.5 mt-2.5">
                        {/* Source Tag with LinkedIn brand styling */}
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                            job.source === 'linkedin'
                              ? 'bg-blue-100 text-[#0a66c2]'
                              : job.source === 'indeed'
                              ? 'bg-indigo-100 text-indigo-700'
                              : job.source === 'greenhouse'
                              ? 'bg-emerald-100 text-emerald-800'
                              : job.source === 'lever'
                              ? 'bg-purple-100 text-purple-700'
                              : 'bg-slate-100 text-slate-600'
                          }`}
                        >
                          {job.source}
                        </span>

                        {job.posted_at && (
                          <span className="text-[10px] text-slate-400 flex items-center gap-0.5">
                            <Clock className="w-2.5 h-2.5" />
                            {formatRelativeTime(job.posted_at)}
                          </span>
                        )}

                        {match && (
                          <MatchScoreBadge score={match.llm_score} size="sm" showLabel={false} />
                        )}

                        {isTracked && (
                          <span className="text-[10px] text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded font-semibold flex items-center gap-0.5">
                            <Check className="w-2.5 h-2.5" /> Tracked
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Quick Discard (X) or Undo Discard button */}
                    {isDiscarded ? (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleUndoDiscard(job.id);
                        }}
                        className="absolute top-3 right-3 text-amber-600 hover:text-amber-800 p-1 hover:bg-amber-50 rounded-full transition-colors"
                        title="Undo Discard"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                      </button>
                    ) : (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenDiscard(job);
                        }}
                        className="absolute top-3 right-3 text-slate-400 hover:text-slate-600 p-1 hover:bg-slate-100 rounded-full transition-colors"
                        title="Dismiss / Discard this job"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Sticky Detail & AI Qualifications Panel (58% Width) */}
          <div className="w-full lg:w-[58%] sticky top-4">
            {activeJob ? (
              <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm max-h-[calc(100vh-140px)] overflow-y-auto space-y-5">
                {/* Header: Company & Title */}
                <div className="border-b border-slate-100 pb-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                          {activeJob.company}
                        </span>
                        <span className="text-slate-300">•</span>
                        <span className="text-xs text-slate-400">
                          {activeJob.posted_at ? `Posted ${formatRelativeTime(activeJob.posted_at)}` : 'Recently listed'}
                        </span>
                      </div>
                      <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight leading-snug">
                        {activeJob.title}
                      </h2>
                      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 pt-1">
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5 text-slate-400" />
                          {activeJob.location || 'India'}
                        </span>
                        <span>•</span>
                        <span className="font-semibold text-slate-700">
                          {activeJob.is_remote ? 'Remote' : 'On-site'}
                        </span>
                        <span>•</span>
                        <span className="text-slate-600">Full-time</span>
                      </div>
                    </div>

                    {/* Source Pill */}
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider shrink-0 ${
                        activeJob.source === 'linkedin'
                          ? 'bg-blue-50 text-[#0a66c2] border border-[#0a66c2]/30'
                          : activeJob.source === 'indeed'
                          ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                          : 'bg-slate-100 text-slate-700 border border-slate-200'
                      }`}
                    >
                      {activeJob.source}
                    </span>
                  </div>

                  {/* Primary CTA Buttons (Screenshot 2 style) */}
                  <div className="flex flex-wrap items-center gap-2.5 pt-4">
                    {/* Apply Directly */}
                    {(activeJob.apply_url || activeJob.url) && (
                      <a
                        href={activeJob.apply_url || activeJob.url || '#'}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1.5 px-5 py-2 rounded-full text-xs font-bold bg-[#0a66c2] hover:bg-[#004182] text-white shadow-sm transition-all"
                        title="Open direct job application link"
                      >
                        <span>Apply Directly</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}

                    {/* Track in Kanban */}
                    <button
                      onClick={() => handleTrackApplication(activeJob)}
                      disabled={trackedJobIds[activeJob.id] != null || isTrackingJobId[activeJob.id]}
                      className={`flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-semibold border transition-all ${
                        trackedJobIds[activeJob.id]
                          ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                          : 'bg-white hover:bg-slate-50 text-slate-700 border-slate-300 shadow-sm'
                      }`}
                    >
                      {trackedJobIds[activeJob.id] ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-600" />
                          <span>Saved to Tracker</span>
                        </>
                      ) : (
                        <>
                          <BookmarkPlus className="w-3.5 h-3.5 text-slate-500" />
                          <span>{isTrackingJobId[activeJob.id] ? 'Saving...' : 'Save Job'}</span>
                        </>
                      )}
                    </button>

                    {/* Tailor Resume Button */}
                    <button
                      onClick={() => {
                        setSelectedJobForModal(activeJob);
                        setIsTailorModalOpen(true);
                      }}
                      className="flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition-all"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>⚡ Tailor Resume</span>
                    </button>

                    {/* Run / View Analysis */}
                    {activeMatch ? (
                      <button
                        onClick={() => {
                          setSelectedJobForModal(activeJob);
                          setIsMatchModalOpen(true);
                        }}
                        className="flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-semibold bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 transition-colors"
                      >
                        <Award className="w-3.5 h-3.5 text-amber-600" />
                        <span>Match Audit</span>
                      </button>
                    ) : (
                      <button
                        onClick={() => handleRunPipeline(activeJob)}
                        disabled={analyzingJobIds[activeJob.id]}
                        className="flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors disabled:opacity-50"
                      >
                        <RotateCw className={`w-3.5 h-3.5 ${analyzingJobIds[activeJob.id] ? 'animate-spin' : ''}`} />
                        <span>{analyzingJobIds[activeJob.id] ? 'Analyzing...' : 'Analyze Match'}</span>
                      </button>
                    )}
                  </div>
                </div>

                {/* ========================================================= */}
                {/* LINKEDIN SCREENSHOT 2: AI QUALIFICATIONS & MATCH AUDIT CARD */}
                {/* ========================================================= */}
                <div className="p-4 sm:p-5 rounded-2xl bg-gradient-to-br from-slate-50 via-white to-blue-50/30 border border-slate-200 shadow-sm space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-bold text-slate-900">
                          {activeMatch && activeMatch.llm_score != null && activeMatch.llm_score >= 70
                            ? '✨ Your profile and resume are a strong match!'
                            : activeMatch
                            ? 'Your profile and resume are missing some required qualifications'
                            : 'Evaluate qualifications with Gemini AI'}
                        </h4>
                      </div>
                      <p className="text-xs text-slate-500 leading-relaxed">
                        {activeMatch?.analysis_summary ||
                          'Compare candidate verified skills, experiences, and requirements deterministically.'}
                      </p>
                    </div>

                    {/* Score or Avatar Badge */}
                    <div className="shrink-0">
                      {activeMatch && activeMatch.llm_score != null ? (
                        <MatchScoreBadge score={activeMatch.llm_score} size="lg" />
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-blue-100 text-[#0a66c2] flex items-center justify-center font-bold text-xs">
                          AI
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Matched vs Missing Skills breakdown */}
                  {activeMatch && (
                    <div className="pt-2 border-t border-slate-100 space-y-2">
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span className="text-[11px] font-semibold text-emerald-700">Matched Skills:</span>
                        {(activeMatch.matched_skills || []).length > 0 ? (
                          (activeMatch.matched_skills || []).map((s, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-800 border border-emerald-200"
                            >
                              ✓ {s}
                            </span>
                          ))
                        ) : (
                          <span className="text-[11px] text-slate-400 italic">None detected</span>
                        )}
                      </div>

                      {(activeMatch.missing_skills || []).length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span className="text-[11px] font-semibold text-amber-700">Missing Gaps:</span>
                          {(activeMatch.missing_skills || []).map((s, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-50 text-amber-800 border border-amber-200"
                            >
                              + {s}
                            </span>
                          ))}
                        </div>
                      )}

                      <div className="pt-2 flex items-center gap-2">
                        <button
                          onClick={() => {
                            setSelectedJobForModal(activeJob);
                            setIsMatchModalOpen(true);
                          }}
                          className="flex items-center gap-1 text-xs font-bold text-[#0a66c2] hover:underline"
                        >
                          <Sparkles className="w-3.5 h-3.5" />
                          <span>Show full match details</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* About the Job Description */}
                <div className="space-y-3 pt-2">
                  <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
                    About the job
                  </h3>

                  {activeJob.requirements && activeJob.requirements.length > 0 && (
                    <div className="space-y-1.5">
                      <h4 className="text-xs font-semibold text-slate-700">Required Skills & Technologies:</h4>
                      <div className="flex flex-wrap gap-1.5">
                        {activeJob.requirements.map((req, idx) => (
                          <span
                            key={idx}
                            className="px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200"
                          >
                            {req}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="text-xs text-slate-700 leading-relaxed whitespace-pre-wrap font-sans bg-slate-50/50 p-4 rounded-xl border border-slate-100">
                    {activeJob.description || 'No raw job description provided by source.'}
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-12 text-center bg-white border border-slate-200 rounded-2xl text-slate-400">
                Select a job from the list to view full details
              </div>
            )}
          </div>
        </div>
      ) : (
        /* ========================================================================= */
        /* GRID VIEW (ALTERNATIVE 2-COLUMN CARDS)                                    */
        /* ========================================================================= */
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {filteredJobs.map((job) => {
            const match = matchesByJobId[job.id];
            const isTracked = !!trackedJobIds[job.id];
            const isTracking = isTrackingJobId[job.id];
            const isDiscarded = !!discardsByJobId[job.id];

            return (
              <div
                key={job.id}
                className={`bg-white border rounded-2xl p-5 shadow-sm hover:shadow transition-shadow flex flex-col justify-between space-y-3 ${
                  isDiscarded ? 'border-slate-200 opacity-60 bg-slate-50' : 'border-slate-200'
                }`}
              >
                <div>
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-0.5">
                      <h3 className="text-[15px] font-bold text-slate-900 leading-snug">
                        {job.title}
                      </h3>
                      <div className="flex items-center gap-1.5 text-xs text-slate-500">
                        <span className="font-semibold text-slate-700">{job.company}</span>
                        <span>•</span>
                        <span>{job.location || 'India'}</span>
                      </div>
                    </div>

                    {match ? (
                      <MatchScoreBadge score={match.llm_score} size="md" />
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600 uppercase">
                        {job.source}
                      </span>
                    )}
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {(job.apply_url || job.url) && (
                      <a
                        href={job.apply_url || job.url || '#'}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-1.5 rounded-full text-xs font-bold bg-[#0a66c2] text-white hover:bg-[#004182]"
                      >
                        Apply
                      </a>
                    )}
                    <button
                      onClick={() => {
                        setSelectedJobForModal(job);
                        setIsTailorModalOpen(true);
                      }}
                      className="px-3 py-1.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 hover:bg-indigo-100"
                    >
                      Tailor
                    </button>
                  </div>
                  <div className="flex items-center gap-2">
                    {isDiscarded ? (
                      <button
                        onClick={() => handleUndoDiscard(job.id)}
                        className="flex items-center gap-1 text-xs text-amber-600 hover:text-amber-800"
                        title="Undo Discard"
                      >
                        <RotateCcw className="w-3 h-3" />
                        <span>Restore</span>
                      </button>
                    ) : (
                      <button
                        onClick={() => handleOpenDiscard(job)}
                        className="text-xs text-slate-400 hover:text-slate-600"
                        title="Discard"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    )}
                    <button
                      onClick={() => handleTrackApplication(job)}
                      disabled={isTracked || isTracking}
                      className="text-xs text-slate-500 hover:text-slate-800"
                    >
                      {isTracked ? 'Tracked' : 'Save'}
                    </button>
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
