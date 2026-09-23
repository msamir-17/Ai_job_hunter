import React, { useState } from 'react';
import { User, Key, Search, ShieldCheck, Cpu, Briefcase, GraduationCap, Target } from 'lucide-react';
import { CandidateProfileResponse } from '../types/candidateProfile';
import { getCandidateProfile } from '../api/candidateProfile';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Alert } from '../components/ui/Alert';

export const CandidateProfilePage: React.FC = () => {
  const [profileIdInput, setProfileIdInput] = useState<string>('');
  const [profile, setProfile] = useState<CandidateProfileResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleFetch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profileIdInput.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getCandidateProfile(profileIdInput.trim());
      setProfile(data);
    } catch (err: any) {
      setError(err.message || 'Candidate profile not found.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="border-b border-slate-800 pb-6 mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg border border-emerald-500/20">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-white">
              Verified Candidate Profile
            </h1>
            <p className="text-xs text-slate-400">
              Verified candidate facts stored in PostgreSQL (Source of Truth)
            </p>
          </div>
        </div>
      </div>

      <Card className="mb-8">
        <form onSubmit={handleFetch} className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Key className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              value={profileIdInput}
              onChange={(e) => setProfileIdInput(e.target.value)}
              placeholder="Enter Candidate Profile UUID to inspect..."
              className="w-full pl-9 pr-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white font-mono placeholder-slate-600 focus:outline-none focus:border-sky-500"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full sm:w-auto px-5 py-2 text-xs font-semibold rounded-lg bg-sky-600 hover:bg-sky-500 text-white transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5"
          >
            <Search className="w-3.5 h-3.5" />
            Fetch Verified Profile
          </button>
        </form>
      </Card>

      {error && <Alert variant="error" className="mb-8">{error}</Alert>}

      {profile ? (
        <Card header={
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-slate-950 border border-slate-800 text-emerald-400 rounded-lg">
                <User className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">{profile.headline || 'Candidate Profile'}</h3>
                <p className="text-xs font-mono text-slate-400">Profile ID: {profile.id}</p>
              </div>
            </div>
            <Badge variant="verified">VERIFIED PROFILE</Badge>
          </div>
        }>
          <div className="space-y-6 text-xs">
            {profile.summary && (
              <div>
                <h4 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1">
                  Professional Summary
                </h4>
                <p className="text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                  {profile.summary}
                </p>
              </div>
            )}

            {profile.skills && profile.skills.length > 0 && (
              <div>
                <h4 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Cpu className="w-4 h-4 text-indigo-400" />
                  Verified Technical Skills ({profile.skills.length})
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {profile.skills.map((skill: any, idx: number) => (
                    <span key={idx} className="px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-slate-200 font-mono text-[11px]">
                      {typeof skill === 'string' ? skill : skill.name || JSON.stringify(skill)}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {profile.experience && profile.experience.length > 0 && (
              <div>
                <h4 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Briefcase className="w-4 h-4 text-sky-400" />
                  Verified Work Experience ({profile.experience.length})
                </h4>
                <div className="space-y-3">
                  {profile.experience.map((exp: any, idx: number) => (
                    <div key={idx} className="p-4 bg-slate-950/60 rounded-xl border border-slate-800">
                      <div className="flex items-center justify-between font-bold text-white text-xs mb-1">
                        <span>{exp.title || 'Role'} {exp.company && <span className="text-slate-400 font-normal">at {exp.company}</span>}</span>
                        <span className="text-[11px] font-mono text-slate-500">{exp.start_date || ''} - {exp.end_date || ''}</span>
                      </div>
                      {exp.location && <p className="text-[11px] text-slate-500 mb-2">{exp.location}</p>}
                      {exp.description && <p className="text-slate-300 text-xs mb-2 leading-relaxed">{exp.description}</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {profile.education && profile.education.length > 0 && (
              <div>
                <h4 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <GraduationCap className="w-4 h-4 text-emerald-400" />
                  Verified Education ({profile.education.length})
                </h4>
                <div className="space-y-2">
                  {profile.education.map((edu: any, idx: number) => (
                    <div key={idx} className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 flex items-center justify-between">
                      <div>
                        <span className="font-bold text-white">{edu.degree || 'Degree'} {edu.field_of_study && `in ${edu.field_of_study}`}</span>
                        {edu.institution && <p className="text-slate-400 text-[11px]">{edu.institution}</p>}
                      </div>
                      <span className="text-[10px] font-mono text-slate-500">{edu.start_date || ''} - {edu.end_date || ''}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {profile.target_titles && profile.target_titles.length > 0 && (
              <div>
                <h4 className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Target className="w-4 h-4 text-amber-400" />
                  Target Job Roles ({profile.target_titles.length})
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {profile.target_titles.map((title: string, idx: number) => (
                    <span key={idx} className="px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-amber-300 font-medium text-[11px]">
                      {title}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Card>
      ) : (
        <Card className="text-center py-12 text-slate-500 text-xs">
          Enter a Candidate Profile UUID above to view verified profile records.
        </Card>
      )}
    </div>
  );
};
