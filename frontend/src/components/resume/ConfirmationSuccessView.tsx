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
      <Card className="border-emerald-200 bg-emerald-50/60 text-center py-8">
        <div className="inline-flex p-2.5 bg-emerald-100 text-emerald-700 rounded-full mb-3">
          <CheckCircle2 className="w-8 h-8" />
        </div>
        <h2 className="text-lg font-bold text-emerald-900 mb-1">
          Profile Updated Successfully
        </h2>
        <p className="text-xs text-emerald-800 max-w-md mx-auto mb-5 leading-relaxed">
          Your reviewed resume facts have been saved to your verified candidate profile.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-2">
          <Link
            to="/profile"
            className="px-4 py-2 text-xs font-medium rounded-lg bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 transition-colors flex items-center gap-1.5"
          >
            <User className="w-3.5 h-3.5 text-slate-500" />
            View Profile
          </Link>

          <button
            onClick={onUploadAnother}
            className="px-4 py-2 text-xs font-medium rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition-colors flex items-center gap-1.5"
          >
            <UploadCloud className="w-3.5 h-3.5" />
            Upload Another
          </button>
        </div>
      </Card>

      {/* Merged Verified Profile Snapshot */}
      <Card header={
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-slate-800 uppercase tracking-wide flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            Verified Profile Snapshot
          </h3>
          <Badge variant="verified">VERIFIED</Badge>
        </div>
      }>
        <div className="space-y-4 text-xs">
          <div>
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
              Headline
            </span>
            <p className="text-slate-900 font-medium">{profile.headline || 'No headline specified'}</p>
          </div>

          {profile.summary && (
            <div>
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                Summary
              </span>
              <p className="text-slate-700 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-200">
                {profile.summary}
              </p>
            </div>
          )}

          {profile.skills && profile.skills.length > 0 && (
            <div>
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-2 flex items-center gap-1">
                <Cpu className="w-3.5 h-3.5 text-blue-600" />
                Verified Skills ({profile.skills.length})
              </span>
              <div className="flex flex-wrap gap-1.5">
                {profile.skills.map((skill: any, idx: number) => (
                  <span
                    key={idx}
                    className="px-2.5 py-0.5 rounded bg-blue-50 border border-blue-200 text-blue-700 font-mono text-[11px]"
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
                <Briefcase className="w-3.5 h-3.5 text-slate-500" />
                Work Experience ({profile.experience.length})
              </span>
              <div className="space-y-2">
                {profile.experience.map((exp: any, idx: number) => (
                  <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <div className="flex items-center justify-between font-medium text-slate-800">
                      <span>{exp.title || 'Role'} {exp.company && `at ${exp.company}`}</span>
                      <span className="text-[10px] text-slate-400 font-mono">{exp.start_date || ''} – {exp.end_date || ''}</span>
                    </div>
                    {exp.description && <p className="text-slate-600 text-[11px] mt-1">{exp.description}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {profile.education && profile.education.length > 0 && (
            <div>
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-2 flex items-center gap-1">
                <GraduationCap className="w-3.5 h-3.5 text-slate-500" />
                Education ({profile.education.length})
              </span>
              <div className="space-y-2">
                {profile.education.map((edu: any, idx: number) => (
                  <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                    <div className="flex items-center justify-between font-medium text-slate-800">
                      <span>{edu.degree || 'Degree'} {edu.institution && `at ${edu.institution}`}</span>
                      <span className="text-[10px] text-slate-400 font-mono">{edu.start_date || ''} – {edu.end_date || ''}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {profile.target_titles && profile.target_titles.length > 0 && (
            <div>
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-2 flex items-center gap-1">
                <Target className="w-3.5 h-3.5 text-slate-500" />
                Target Job Titles ({profile.target_titles.length})
              </span>
              <div className="flex flex-wrap gap-1.5">
                {profile.target_titles.map((title: string, idx: number) => (
                  <span key={idx} className="px-2.5 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-700 font-medium text-[11px]">
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
