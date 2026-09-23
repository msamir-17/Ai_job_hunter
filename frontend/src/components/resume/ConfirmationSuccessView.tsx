import React from 'react';
import { CheckCircle2, User, UploadCloud, ShieldCheck, Briefcase, GraduationCap, Cpu, Target } from 'lucide-react';
import { CandidateProfileResponse } from '../../types/candidateProfile';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Link } from 'react-router-dom';

interface ConfirmationSuccessViewProps {
  profile: CandidateProfileResponse;
  onUploadAnother: () => void;
}

export const ConfirmationSuccessView: React.FC<ConfirmationSuccessViewProps> = ({
  profile,
  onUploadAnother,
}) => {
  return (
    <div className="space-y-6">
      <Card className="border-emerald-500/30 bg-emerald-950/20 text-center py-8">
        <div className="inline-flex p-3 bg-emerald-500/10 text-emerald-400 rounded-full border border-emerald-500/30 mb-4">
          <CheckCircle2 className="w-10 h-10" />
        </div>
        <h2 className="text-xl font-bold text-white mb-2">
          Profile Updated Successfully!
        </h2>
        <p className="text-xs text-emerald-200/90 max-w-lg mx-auto mb-6 leading-relaxed">
          Your reviewed resume information has been atomically merged into your verified candidate profile. Existing candidate facts were preserved.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-3">
          <Link
            to="/profile"
            className="px-5 py-2 text-xs font-semibold rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors flex items-center gap-2"
          >
            <User className="w-4 h-4 text-sky-400" />
            View Candidate Profile
          </Link>

          <button
            onClick={onUploadAnother}
            className="px-5 py-2 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition-colors flex items-center gap-2"
          >
            <UploadCloud className="w-4 h-4" />
            Upload Another Resume
          </button>
        </div>
      </Card>

      {/* Merged Verified Profile Snapshot */}
      <Card header={
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            Verified Candidate Profile Snapshot
          </h3>
          <Badge variant="verified">VERIFIED SOURCE OF TRUTH</Badge>
        </div>
      }>
        <div className="space-y-4 text-xs">
          <div>
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
              Headline
            </span>
            <p className="text-slate-200 font-medium">{profile.headline || 'No headline specified'}</p>
          </div>

          {profile.summary && (
            <div>
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                Summary
              </span>
              <p className="text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                {profile.summary}
              </p>
            </div>
          )}

          {profile.skills && profile.skills.length > 0 && (
            <div>
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-2 flex items-center gap-1">
                <Cpu className="w-3.5 h-3.5 text-indigo-400" />
                Verified Skills ({profile.skills.length})
              </span>
              <div className="flex flex-wrap gap-1.5">
                {profile.skills.map((skill: any, idx: number) => (
                  <span
                    key={idx}
                    className="px-2.5 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-300 font-mono text-[11px]"
                  >
                    {typeof skill === 'string' ? skill : skill.name || JSON.stringify(skill)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {profile.experience && profile.experience.length > 0 && (
            <div>
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-2 flex items-center gap-1">
                <Briefcase className="w-3.5 h-3.5 text-sky-400" />
                Verified Work Experience ({profile.experience.length})
              </span>
              <div className="space-y-2">
                {profile.experience.map((exp: any, idx: number) => (
                  <div key={idx} className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                    <div className="flex items-center justify-between font-medium text-slate-200">
                      <span>{exp.title || 'Role'} {exp.company && `@ ${exp.company}`}</span>
                      <span className="text-[10px] text-slate-500">{exp.start_date || ''} - {exp.end_date || ''}</span>
                    </div>
                    {exp.description && <p className="text-slate-400 text-[11px] mt-1">{exp.description}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {profile.education && profile.education.length > 0 && (
            <div>
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-2 flex items-center gap-1">
                <GraduationCap className="w-3.5 h-3.5 text-emerald-400" />
                Verified Education ({profile.education.length})
              </span>
              <div className="space-y-2">
                {profile.education.map((edu: any, idx: number) => (
                  <div key={idx} className="p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                    <div className="flex items-center justify-between font-medium text-slate-200">
                      <span>{edu.degree || 'Degree'} {edu.institution && `@ ${edu.institution}`}</span>
                      <span className="text-[10px] text-slate-500">{edu.start_date || ''} - {edu.end_date || ''}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {profile.target_titles && profile.target_titles.length > 0 && (
            <div>
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-2 flex items-center gap-1">
                <Target className="w-3.5 h-3.5 text-amber-400" />
                Target Job Titles ({profile.target_titles.length})
              </span>
              <div className="flex flex-wrap gap-1.5">
                {profile.target_titles.map((title: string, idx: number) => (
                  <span key={idx} className="px-2.5 py-0.5 rounded bg-slate-950 border border-slate-800 text-amber-300 font-medium text-[11px]">
                    {title}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};
