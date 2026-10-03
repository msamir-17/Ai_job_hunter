import React from 'react';
import { X, CheckCircle2, AlertTriangle, ShieldAlert, Cpu, Sparkles, FileText, BookmarkPlus } from 'lucide-react';
import { Job } from '../../types/job';
import { PipelineRunResponse } from '../../types/matching';
import { MatchScoreBadge } from './MatchScoreBadge';
import { SkillPillList } from './SkillPillList';

interface MatchDetailModalProps {
  job: Job;
  pipelineResult: PipelineRunResponse | null;
  isOpen: boolean;
  onClose: () => void;
  onOpenTailoring: () => void;
  onTrackApplication: () => void;
  isTracking?: boolean;
}

export const MatchDetailModal: React.FC<MatchDetailModalProps> = ({
  job,
  pipelineResult,
  isOpen,
  onClose,
  onOpenTailoring,
  onTrackApplication,
  isTracking = false,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl my-8">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4 bg-slate-950/60">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold text-white tracking-tight">{job.title}</h2>
              {pipelineResult && <MatchScoreBadge score={pipelineResult.llm_score} size="md" />}
            </div>
            <p className="text-sm text-slate-400 mt-0.5">
              {job.company} • {job.location || (job.is_remote ? 'Remote' : 'Location Unspecified')}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto">
          {/* 3-Tier Pipeline Breakdown */}
          {pipelineResult ? (
            <div className="space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                3-Tier Multi-Stage Evaluation
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Stage 1: Deterministic */}
                <div
                  className={`p-4 rounded-xl border ${
                    pipelineResult.passed_deterministic
                      ? 'bg-emerald-950/20 border-emerald-500/30'
                      : 'bg-red-950/20 border-red-500/30'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="p-1 rounded bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300">
                      Stage 1
                    </span>
                    <span className="text-xs font-semibold text-white">Deterministic Rules</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    {pipelineResult.passed_deterministic ? (
                      <span className="text-emerald-400 text-xs font-medium flex items-center gap-1">
                        <CheckCircle2 className="w-4 h-4" /> Passed Filters
                      </span>
                    ) : (
                      <span className="text-red-400 text-xs font-medium flex items-center gap-1">
                        <ShieldAlert className="w-4 h-4" /> Disqualified
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-2">
                    Work mode, minimum experience & title alignment.
                  </p>
                </div>

                {/* Stage 2: pgvector */}
                <div className="p-4 rounded-xl border bg-sky-950/20 border-sky-500/30">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="p-1 rounded bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300">
                      Stage 2
                    </span>
                    <span className="text-xs font-semibold text-white">pgvector Semantic</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <Cpu className="w-4 h-4 text-sky-400" />
                    <span className="text-sky-300 font-bold text-sm">
                      {pipelineResult.vector_score !== null && pipelineResult.vector_score !== undefined
                        ? `${Math.round(pipelineResult.vector_score * 100)}% Similarity`
                        : 'Bypassed'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-2">
                    384-dimensional dense cosine similarity search.
                  </p>
                </div>

                {/* Stage 3: LLM Gap Analysis */}
                <div className="p-4 rounded-xl border bg-indigo-950/20 border-indigo-500/30">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="p-1 rounded bg-slate-900 border border-slate-800 text-xs font-mono text-slate-300">
                      Stage 3
                    </span>
                    <span className="text-xs font-semibold text-white">LLM Gap Analysis</span>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <Sparkles className="w-4 h-4 text-indigo-400" />
                    <span className="text-indigo-300 font-bold text-sm">
                      {pipelineResult.llm_score !== null && pipelineResult.llm_score !== undefined
                        ? `${Math.round(pipelineResult.llm_score)}/100 Score`
                        : 'Pending / Bypassed'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-2">
                    Zero-hallucination verified profile reasoning.
                  </p>
                </div>
              </div>

              {/* Skills Breakdown */}
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
                <h4 className="text-xs font-bold text-slate-300 mb-3">Skill Gap Assessment</h4>
                <SkillPillList
                  matchedSkills={pipelineResult.matched_skills}
                  missingSkills={pipelineResult.missing_skills}
                  maxDisplay={20}
                />
              </div>

              {/* LLM Recommendation & Summary */}
              {pipelineResult.analysis_summary && (
                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-300">AI Evaluation Summary:</span>
                    {pipelineResult.recommendation && (
                      <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-sky-500/10 text-sky-300 border border-sky-500/30">
                        {pipelineResult.recommendation}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {pipelineResult.analysis_summary}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="p-6 text-center border border-dashed border-slate-800 rounded-xl">
              <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto mb-2" />
              <p className="text-sm text-slate-300 font-medium">Pipeline Not Yet Run</p>
              <p className="text-xs text-slate-500 mt-1">
                Run the 3-Tier Match Engine on this job to see deterministic qualification, vector similarity, and LLM skill gap report.
              </p>
            </div>
          )}

          {/* Job Requirements & Description Excerpt */}
          <div className="border-t border-slate-800 pt-4 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Job Requirements
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {job.requirements.map((req, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-300 border border-slate-700"
                >
                  {req}
                </span>
              ))}
            </div>

            <div className="mt-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">
                Description Excerpt
              </h4>
              <p className="text-xs text-slate-400 line-clamp-4 leading-relaxed bg-slate-950/40 p-3 rounded-lg border border-slate-800">
                {job.description}
              </p>
            </div>
          </div>
        </div>

        {/* Modal Footer Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-slate-800 px-6 py-4 bg-slate-950/60">
          <div className="text-xs text-slate-400">
            Source:{' '}
            <span className="font-mono text-slate-300 capitalize">{job.source}</span>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              onClick={onTrackApplication}
              disabled={isTracking}
              className="flex-1 sm:flex-initial flex items-center justify-center gap-2 px-4 py-2 text-xs font-medium rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors disabled:opacity-50"
            >
              <BookmarkPlus className="w-4 h-4 text-sky-400" />
              {isTracking ? 'Saving...' : 'Track in Kanban'}
            </button>

            <button
              onClick={onOpenTailoring}
              className="flex-1 sm:flex-initial flex items-center justify-center gap-2 px-5 py-2 text-xs font-semibold rounded-xl bg-sky-600 hover:bg-sky-500 text-white transition-colors shadow-lg shadow-sky-950"
            >
              <FileText className="w-4 h-4" />
              Tailor Resume & Cover Letter
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
