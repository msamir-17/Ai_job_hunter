import React, { useState, useEffect } from 'react';
import {
  Briefcase,
  Search,
  Sparkles,
  RotateCw,
  ChevronRight,
  BookmarkPlus,
  CheckCircle2,
  FileText,
  MapPin,
  Building,
  Download,
} from 'lucide-react';
import { Job } from '../types/job';
import { CandidateProfileResponse } from '../types/candidateProfile';
import { PipelineRunResponse } from '../types/matching';
import { listJobs, ingestJobs } from '../api/jobs';
import { listCandidateProfiles } from '../api/candidateProfile';
import {
  runMatchingPipeline,
  getCandidateJobMatches,
} from '../api/matching';
import { createApplication, listApplications } from '../api/applications';
import { MatchScoreBadge } from '../components/matching/MatchScoreBadge';
import { SkillPillList } from '../components/matching/SkillPillList';
import { MatchDetailModal } from '../components/matching/MatchDetailModal';
import { TailoringWorkspaceModal } from '../components/tailoring/TailoringWorkspaceModal';

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

  // Applications state
  const [trackedJobIds, setTrackedJobIds] = useState<Record<string, string>>({}); // jobId -> applicationId
  const [isTrackingJobId, setIsTrackingJobId] = useState<Record<string, boolean>>({});

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [remoteOnly, setRemoteOnly] = useState<boolean>(false);

  // Active Modals
  const [selectedJobForModal, setSelectedJobForModal] = useState<Job | null>(null);
  const [isMatchModalOpen, setIsMatchModalOpen] = useState<boolean>(false);
  const [isTailorModalOpen, setIsTailorModalOpen] = useState<boolean>(false);

  // Fetch initial profile & jobs
  useEffect(() => {
    loadProfileAndInitialData();
  }, []);

  const loadProfileAndInitialData = async () => {
    setIsLoadingProfile(true);
    try {
      const profiles = await listCandidateProfiles(1);
      const p = profiles.length > 0 ? profiles[0] : null;
      setProfile(p);

      // Load jobs
      await loadJobs();

      // If profile exists, load existing matches & tracked applications
      if (p) {
        loadStoredMatches(p.id);
        loadUserApplications(p.user_id);
      }
    } catch (err: any) {
      console.error('Failed to load profile/jobs:', err);
    } finally {
      setIsLoadingProfile(false);
    }
  };

  const loadJobs = async () => {
    setIsLoadingJobs(true);
    setJobError(null);
    try {
      const jobList = await listJobs({ limit: 100 });
      setJobs(jobList);
    } catch (err: any) {
      setJobError(err.message || 'Failed to load jobs');
    } finally {
      setIsLoadingJobs(false);
    }
  };

  const loadStoredMatches = async (candidateProfileId: string) => {
    try {
      const stored = await getCandidateJobMatches(candidateProfileId);
      const map: Record<string, PipelineRunResponse> = {};
      stored.forEach((m) => {
        map[m.job_id] = {
          candidate_profile_id: m.candidate_profile_id,
          job_id: m.job_id,
          passed_deterministic: m.passed_deterministic,
          deterministic_status: m.passed_deterministic ? 'shortlisted' : 'rejected',
          vector_score: m.vector_score,
          llm_score: m.llm_score,
          matched_skills: m.matched_skills,
          missing_skills: m.missing_skills,
          analysis_summary: m.analysis_summary,
          overall_status: m.status,
          current_stage: 'completed',
        };
      });
      setMatchesByJobId((prev) => ({ ...prev, ...map }));
    } catch (err) {
      console.error('Could not load stored matches:', err);
    }
  };

  const loadUserApplications = async (userId: string) => {
    try {
      const apps = await listApplications(userId);
      const map: Record<string, string> = {};
      apps.forEach((a) => {
        if (a.job_id) {
          map[a.job_id] = a.id;
        }
      });
      setTrackedJobIds(map);
    } catch (err) {
      console.error('Could not load applications:', err);
    }
  };

  const handleIngest = async (source: 'remotive' | 'manual') => {
    setIsIngesting(true);
    setIngestionBanner(null);
    try {
      const res = await ingestJobs({ source, limit: 15 });
      setIngestionBanner(
        `Successfully ingested ${res.new_ingested} new jobs from ${source} (${res.duplicates_skipped} duplicates skipped).`
      );
      await loadJobs();
    } catch (err: any) {
      setIngestionBanner(`Ingestion failed: ${err.message}`);
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
      console.error('Pipeline error:', err);
    } finally {
      setAnalyzingJobIds((prev) => ({ ...prev, [job.id]: false }));
    }
  };

  const handleTrackApplication = async (job: Job) => {
    if (!profile) return;

    setIsTrackingJobId((prev) => ({ ...prev, [job.id]: true }));
    try {
      // Find or trigger a match record ID
      const existingMatch = matchesByJobId[job.id];
      let jobMatchId: string | null = null;

      if (existingMatch) {
        // Find existing match row
        const stored = await getCandidateJobMatches(profile.id);
        const found = stored.find((m) => m.job_id === job.id);
        if (found) jobMatchId = found.id;
      }

      if (!jobMatchId) {
        // Run pipeline first to ensure JobMatch exists
        const res = await runMatchingPipeline(profile.id, job.id);
        setMatchesByJobId((prev) => ({ ...prev, [job.id]: res }));
        const stored = await getCandidateJobMatches(profile.id);
        const found = stored.find((m) => m.job_id === job.id);
        if (found) jobMatchId = found.id;
      }

      if (jobMatchId) {
        const app = await createApplication({
          user_id: profile.user_id,
          job_match_id: jobMatchId,
          status: 'saved',
        });
        setTrackedJobIds((prev) => ({ ...prev, [job.id]: app.id }));
      }
    } catch (err: any) {
      console.error('Failed to track application:', err);
    } finally {
      setIsTrackingJobId((prev) => ({ ...prev, [job.id]: false }));
    }
  };

  // Filtered jobs
  const filteredJobs = jobs.filter((job) => {
    if (remoteOnly && !job.is_remote) return false;
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      const matchTitle = job.title.toLowerCase().includes(query);
      const matchCompany = job.company.toLowerCase().includes(query);
      const matchReq = job.requirements.some((r) => r.toLowerCase().includes(query));
      if (!matchTitle && !matchCompany && !matchReq) return false;
    }
    return true;
  });

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-sky-500/10 text-sky-400 rounded-lg border border-sky-500/20">
              <Briefcase className="w-6 h-6" />
            </div>
            <h1 className="text-2xl font-extrabold tracking-tight text-white">
              Job Discovery & 3-Tier Matcher
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Ingest normalized job listings, execute deterministic filters + pgvector + LLM reasoning, and tailor grounded application documents.
          </p>
        </div>

        {/* Ingestion Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleIngest('remotive')}
            disabled={isIngesting}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors disabled:opacity-50 shadow"
          >
            <Download className="w-3.5 h-3.5" />
            {isIngesting ? 'Ingesting...' : 'Ingest Remotive Jobs'}
          </button>
          <button
            onClick={() => handleIngest('manual')}
            disabled={isIngesting}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors disabled:opacity-50"
          >
            Load Manual Jobs
          </button>
          <button
            onClick={loadJobs}
            disabled={isLoadingJobs}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors"
            title="Refresh jobs"
          >
            <RotateCw className={`w-4 h-4 ${isLoadingJobs ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Ingestion Status Banner */}
      {ingestionBanner && (
        <div className="p-3 bg-indigo-950/40 border border-indigo-500/30 rounded-xl text-xs text-indigo-200 flex items-center justify-between">
          <span>{ingestionBanner}</span>
          <button
            onClick={() => setIngestionBanner(null)}
            className="text-slate-400 hover:text-white"
          >
            ✕
          </button>
        </div>
      )}

      {/* Candidate Profile Context Banner */}
      {profile ? (
        <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-sky-400">
              Active Candidate Profile
            </span>
            <h3 className="text-sm font-bold text-white">
              {profile.headline || 'Verified Candidate Profile'}
            </h3>
            <p className="text-xs text-slate-400 line-clamp-1 max-w-lg">
              {profile.summary || 'Verified profile data stored in PostgreSQL'}
            </p>
            <div className="flex flex-wrap gap-1 mt-1">
              {(profile.skills || []).slice(0, 8).map((s, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 border border-slate-700"
                >
                  {s}
                </span>
              ))}
              {(profile.skills || []).length > 8 && (
                <span className="text-[10px] text-slate-500 font-mono">
                  +{(profile.skills || []).length - 8} more
                </span>
              )}
            </div>
          </div>

          <div className="text-xs text-slate-400 sm:text-right shrink-0">
            <div>
              Target Roles:{' '}
              <span className="text-slate-200 font-medium">
                {(profile.target_titles || []).slice(0, 2).join(', ') || 'General Tech'}
              </span>
            </div>
            <div className="text-[11px] text-slate-500 font-mono mt-0.5">
              ID: {profile.id.slice(0, 8)}...
            </div>
          </div>
        </div>
      ) : isLoadingProfile ? (
        <div className="p-4 bg-slate-900/30 border border-slate-800 rounded-xl text-xs text-slate-500 italic">
          Loading candidate profile context...
        </div>
      ) : (
        <div className="p-4 bg-amber-950/20 border border-amber-800/40 rounded-xl text-xs text-amber-300">
          No candidate profile found. Please upload a resume or create your profile in Candidate Profile page first.
        </div>
      )}

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by role, company, or tech stack..."
            className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"
          />
        </div>

        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={remoteOnly}
              onChange={(e) => setRemoteOnly(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-sky-600 focus:ring-0"
            />
            <span>Remote Only</span>
          </label>

          <span className="text-xs text-slate-500">
            Showing <strong className="text-slate-300">{filteredJobs.length}</strong> jobs
          </span>
        </div>
      </div>

      {/* Jobs Grid */}
      {isLoadingJobs ? (
        <div className="py-20 text-center space-y-3">
          <RotateCw className="w-8 h-8 text-sky-400 animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading ingested jobs from database...</p>
        </div>
      ) : jobError ? (
        <div className="p-4 bg-red-950/30 border border-red-800/40 rounded-xl text-xs text-red-300">
          {jobError}
        </div>
      ) : filteredJobs.length === 0 ? (
        <div className="py-16 text-center border border-dashed border-slate-800 rounded-2xl space-y-3">
          <Briefcase className="w-10 h-10 text-slate-600 mx-auto" />
          <p className="text-sm font-semibold text-slate-300">No Jobs Found</p>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Try adjusting your search filters or click "Ingest Remotive Jobs" above to import live remote software jobs.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredJobs.map((job) => {
            const match = matchesByJobId[job.id];
            const isAnalyzing = analyzingJobIds[job.id];
            const isTracked = !!trackedJobIds[job.id];
            const isTracking = isTrackingJobId[job.id];

            return (
              <div
                key={job.id}
                className="bg-slate-900/60 border border-slate-800 hover:border-slate-700 rounded-xl p-5 shadow-lg flex flex-col justify-between space-y-4 transition-all"
              >
                {/* Job Card Header */}
                <div>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="text-base font-bold text-white tracking-tight leading-snug">
                        {job.title}
                      </h3>
                      <div className="flex items-center gap-2 text-xs text-slate-400 mt-1">
                        <span className="flex items-center gap-1 font-medium text-slate-300">
                          <Building className="w-3.5 h-3.5 text-slate-500" />
                          {job.company}
                        </span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5 text-slate-500" />
                          {job.location || (job.is_remote ? 'Remote' : 'Location N/A')}
                        </span>
                      </div>
                    </div>

                    {match ? (
                      <MatchScoreBadge score={match.llm_score} size="md" />
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-400 border border-slate-700">
                        {job.source}
                      </span>
                    )}
                  </div>

                  {/* Requirements Tags */}
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {job.requirements.slice(0, 5).map((req, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 rounded text-[11px] bg-slate-950 text-slate-300 border border-slate-800"
                      >
                        {req}
                      </span>
                    ))}
                    {job.requirements.length > 5 && (
                      <span className="text-[10px] text-slate-500 font-mono py-0.5">
                        +{job.requirements.length - 5}
                      </span>
                    )}
                  </div>

                  {/* Inline Matched/Missing Skills breakdown if analyzed */}
                  {match && (
                    <div className="mt-3 pt-3 border-t border-slate-800/80">
                      <SkillPillList
                        matchedSkills={match.matched_skills}
                        missingSkills={match.missing_skills}
                        maxDisplay={4}
                      />
                    </div>
                  )}
                </div>

                {/* Card Actions */}
                <div className="pt-3 border-t border-slate-800 flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    {/* Pipeline trigger or detail view */}
                    {match ? (
                      <button
                        onClick={() => {
                          setSelectedJobForModal(job);
                          setIsMatchModalOpen(true);
                        }}
                        className="flex items-center gap-1 text-xs font-semibold text-sky-400 hover:text-sky-300 transition-colors"
                      >
                        <span>Match Breakdown</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    ) : (
                      <button
                        onClick={() => handleRunPipeline(job)}
                        disabled={isAnalyzing}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white transition-colors disabled:opacity-50 shadow"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        {isAnalyzing ? 'Analyzing 3 Stages...' : 'Analyze Match'}
                      </button>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    {/* Tailor Docs Button */}
                    <button
                      onClick={() => {
                        setSelectedJobForModal(job);
                        setIsTailorModalOpen(true);
                      }}
                      className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
                      title="Tailor grounded resume bullets and cover letter"
                    >
                      <FileText className="w-3.5 h-3.5 text-indigo-400" />
                      <span>Tailor</span>
                    </button>

                    {/* Track in Kanban Button */}
                    <button
                      onClick={() => handleTrackApplication(job)}
                      disabled={isTracked || isTracking}
                      className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                        isTracked
                          ? 'bg-emerald-950/40 text-emerald-300 border border-emerald-500/30'
                          : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700'
                      }`}
                    >
                      {isTracked ? (
                        <>
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Tracked</span>
                        </>
                      ) : (
                        <>
                          <BookmarkPlus className="w-3.5 h-3.5 text-sky-400" />
                          <span>{isTracking ? 'Saving...' : 'Track'}</span>
                        </>
                      )}
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
          onClose={() => setIsTailorModalOpen(false)}
          onSavedToApplication={() => {
            if (profile) loadUserApplications(profile.user_id);
          }}
        />
      )}
    </div>
  );
};
