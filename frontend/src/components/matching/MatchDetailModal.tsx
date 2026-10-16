import React from 'react';
import { X, CheckCircle2, AlertTriangle, ShieldAlert, Cpu, FileText, BookmarkPlus } from 'lucide-react';
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm overflow-y-auto">
      <div className="bg-white border border-slate-200 rounded-xl w-full max-w-3xl overflow-hidden shadow-xl my-8">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4 bg-white">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-bold text-slate-900">{job.title}</h2>
              {pipelineResult && <MatchScoreBadge score={pipelineResult.llm_score} size="md" />}
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              {job.company} • {job.location || (job.is_remote ? 'Remote' : 'Location Unspecified')}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 space-y-5 max-h-[75vh] overflow-y-auto">
          {/* 3-Tier Pipeline Breakdown */}
          {pipelineResult ? (
            <div className="space-y-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Evaluation Breakdown
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {/* Stage 1: Deterministic */}
                <div
                  className={`p-3.5 rounded-lg border ${
                    pipelineResult.passed_deterministic
                      ? 'bg-emerald-50 border-emerald-200'
                      : 'bg-red-50 border-red-200'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="px-1.5 py-0.5 rounded bg-white border border-slate-200 text-[10px] font-mono text-slate-600">
                      Stage 1
                    </span>
                    <span className="text-xs font-semibold text-slate-800">Deterministic</span>
                  </div>
                  <div className="flex items-center gap-1.5 mt-1">
                    {pipelineResult.passed_deterministic ? (
                      <span className="text-emerald-700 text-xs font-medium flex items-center gap-1">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Passed Rules
                      </span>
                    ) : (
                      <span className="text-red-700 text-xs font-medium flex items-center gap-1">
                        <ShieldAlert className="w-4 h-4 text-red-600" /> Disqualified
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1.5">
                    Location, experience level & role fit.
                  </p>
                </div>

                {/* Stage 2: pgvector */}
                <div className="p-3.5 rounded-lg border bg-blue-50 border-blue-200">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="px-1.5 py-0.5 rounded bg-white border border-slate-200 text-[10px] font-mono text-slate-600">
                      Stage 2
                    </span>
                    <span className="text-xs font-semibold text-slate-800">pgvector Semantic</span>
                  </div>
                  <div className="flex items-center gap-1.5 mt-1">
                    <Cpu className="w-4 h-4 text-blue-600" />
                    <span className="text-blue-800 font-semibold text-xs">
                      {pipelineResult.vector_score !== null && pipelineResult.vector_score !== undefined
                        ? `${Math.round(pipelineResult.vector_score * 100)}% Similarity`
                        : 'Bypassed'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1.5">
                    Cosine dense embedding match.
                  </p>
                </div>

                {/* Stage 3: LLM Gap Analysis */}
                <div className="p-3.5 rounded-lg border bg-slate-50 border-slate-200">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="px-1.5 py-0.5 rounded bg-white border border-slate-200 text-[10px] font-mono text-slate-600">
                      Stage 3
                    </span>
                    <span className="text-xs font-semibold text-slate-800">Skill Reasoning</span>
                  </div>
                  <div className="flex items-center gap-1.5 mt-1">
                    <CheckCircle2 className="w-4 h-4 text-blue-600" />
                    <span className="text-slate-800 font-semibold text-xs">
                      {pipelineResult.llm_score !== null && pipelineResult.llm_score !== undefined
                        ? `${Math.round(pipelineResult.llm_score)}/100 Score`
                        : 'Pending'}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1.5">
                    Grounded fact comparison.
                  </p>
                </div>
              </div>

              {/* Skills Breakdown */}
              <div className="p-4 rounded-lg bg-slate-50 border border-slate-200">
                <h4 className="text-xs font-semibold text-slate-700 mb-2">Skill Gap Assessment</h4>
                <SkillPillList
                  matchedSkills={pipelineResult.matched_skills}
                  missingSkills={pipelineResult.missing_skills}
                  maxDisplay={20}
                />
              </div>

              {/* Summary */}
              {pipelineResult.analysis_summary && (
                <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-slate-800">Assessment Summary:</span>
                    {pipelineResult.recommendation && (
                      <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-blue-50 text-blue-700 border border-blue-200">
                        {pipelineResult.recommendation}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {pipelineResult.analysis_summary}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="p-6 text-center border border-dashed border-slate-300 rounded-lg">
              <AlertTriangle className="w-6 h-6 text-amber-500 mx-auto mb-2" />
              <p className="text-xs font-semibold text-slate-700">Pipeline Not Yet Run</p>
              <p className="text-xs text-slate-500 mt-0.5">
                Run the 3-Tier Match Engine on this job to see deterministic qualification, vector similarity, and skill gaps.
              </p>
            </div>
          )}

          {/* Job Requirements */}
          <div className="border-t border-slate-100 pt-4 space-y-2">
            <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Requirements
            </h4>
            <div className="flex flex-wrap gap-1">
              {job.requirements.map((req, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-700 border border-slate-200"
                >
                  {req}
                </span>
              ))}
            </div>

            <div className="mt-2.5">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">
                Description Excerpt
              </h4>
              <p className="text-xs text-slate-600 line-clamp-4 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-200">
                {job.description}
              </p>
            </div>
          </div>
        </div>

        {/* Modal Footer Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-slate-100 px-6 py-3.5 bg-slate-50">
          <div className="text-xs text-slate-500">
            Source:{' '}
            <span className="font-mono text-slate-700 capitalize">{job.source}</span>
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button
              onClick={onTrackApplication}
              disabled={isTracking}
              className="flex-1 sm:flex-initial flex items-center justify-center gap-1.5 px-3.5 py-1.5 text-xs font-medium rounded-lg bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition-colors disabled:opacity-50"
            >
              <BookmarkPlus className="w-3.5 h-3.5 text-slate-500" />
              <span>{isTracking ? 'Saving...' : 'Track Application'}</span>
            </button>

            <button
              onClick={onOpenTailoring}
              className="flex-1 sm:flex-initial flex items-center justify-center gap-1.5 px-4 py-1.5 text-xs font-medium rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Tailor Documents</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
