import React, { useState, useEffect } from 'react';
import { User, Key, Search, ShieldCheck, Cpu, Briefcase, GraduationCap, Target, Edit2, Trash2, X, Check, Trophy } from 'lucide-react';
import { CandidateProfileResponse } from '../types/candidateProfile';
import { getCandidateProfile, getActiveCandidateProfile, updateCandidateProfile, deleteCandidateProfile } from '../api/candidateProfile';
import { Card } from '../components/ui/Card';
import { Alert } from '../components/ui/Alert';

export const CandidateProfilePage: React.FC = () => {
  const [profileIdInput, setProfileIdInput] = useState<string>('');
  const [profile, setProfile] = useState<CandidateProfileResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Edit Modal State
  const [isEditModalOpen, setIsEditModalOpen] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [editHeadline, setEditHeadline] = useState<string>('');
  const [editSummary, setEditSummary] = useState<string>('');
  const [editAchievements, setEditAchievements] = useState<string>('');
  const [editSkills, setEditSkills] = useState<string>('');
  const [editTargetTitles, setEditTargetTitles] = useState<string>('');

  useEffect(() => {
    const fetchActive = async () => {
      setLoading(true);
      try {
        const data = await getActiveCandidateProfile();
        setProfile(data);
        setProfileIdInput(data.id);
      } catch (err: any) {
        // Silent catch if backend active profile fails
      } finally {
        setLoading(false);
      }
    };
    fetchActive();
  }, []);

  const handleFetch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profileIdInput.trim()) return;
    setLoading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const data = await getCandidateProfile(profileIdInput.trim());
      setProfile(data);
    } catch (err: any) {
      setError(err.message || 'Candidate profile not found.');
    } finally {
      setLoading(false);
    }
  };

  const openEditModal = () => {
    if (!profile) return;
    setEditHeadline(profile.headline || '');

    const rawSummary = profile.summary || '';
    if (rawSummary.includes('Key Achievements & Certifications:')) {
      const parts = rawSummary.split('Key Achievements & Certifications:');
      setEditSummary(parts[0].trim());
      setEditAchievements(parts[1].trim());
    } else {
      setEditSummary(rawSummary);
      setEditAchievements('');
    }

    setEditSkills((profile.skills || []).map((s: any) => (typeof s === 'string' ? s : s.name || '')).join(', '));
    setEditTargetTitles((profile.target_titles || []).join(', '));
    setIsEditModalOpen(true);
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile) return;
    setIsSaving(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const skillsArray = editSkills
        .split(',')
        .map((s) => s.trim())
        .filter((s) => s.length > 0);

      const targetTitlesArray = editTargetTitles
        .split(',')
        .map((t) => t.trim())
        .filter((t) => t.length > 0);

      let finalSummary = editSummary.trim();
      if (editAchievements.trim()) {
        finalSummary = `${finalSummary}\n\nKey Achievements & Certifications:\n${editAchievements.trim()}`;
      }

      const updated = await updateCandidateProfile(profile.id, {
        headline: editHeadline,
        summary: finalSummary,
        skills: skillsArray,
        target_titles: targetTitlesArray,
      });

      setProfile(updated);
      setIsEditModalOpen(false);
      setSuccessMsg('Profile updated successfully with achievements in PostgreSQL database!');
    } catch (err: any) {
      setError(err.message || 'Failed to update profile.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteProfile = async () => {
    if (!profile) return;
    if (!window.confirm('Are you sure you want to delete this Candidate Profile from PostgreSQL? This action cannot be undone.')) {
      return;
    }
    setLoading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      await deleteCandidateProfile(profile.id);
      setProfile(null);
      setProfileIdInput('');
      setSuccessMsg('Candidate profile deleted successfully.');
    } catch (err: any) {
      setError(err.message || 'Failed to delete profile.');
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

      {error && <Alert variant="error" className="mb-6">{error}</Alert>}
      {successMsg && <Alert variant="success" className="mb-6">{successMsg}</Alert>}

      {profile ? (
        <Card header={
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-slate-950 border border-slate-800 text-emerald-400 rounded-lg">
                <User className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">{profile.headline || 'Candidate Profile'}</h3>
                <p className="text-xs font-mono text-slate-400">Profile ID: {profile.id}</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={openEditModal}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-xs font-semibold text-white transition-colors shadow"
                title="Edit candidate profile fields"
              >
                <Edit2 className="w-3.5 h-3.5" />
                <span>Edit Profile</span>
              </button>

              <button
                onClick={handleDeleteProfile}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border border-rose-500/30 text-xs font-semibold transition-colors"
                title="Delete candidate profile"
              >
                <Trash2 className="w-3.5 h-3.5 text-rose-400" />
                <span>Delete</span>
              </button>
            </div>
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

      {/* Edit Profile Modal */}
      {isEditModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Edit2 className="w-5 h-5 text-sky-400" />
                <h3 className="text-base font-bold text-white">Edit Candidate Profile</h3>
              </div>
              <button
                onClick={() => setIsEditModalOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSaveProfile} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-300 mb-1">Headline</label>
                <input
                  type="text"
                  value={editHeadline}
                  onChange={(e) => setEditHeadline(e.target.value)}
                  placeholder="e.g. Senior Python & AI/ML Engineer"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1">Professional Summary</label>
                <textarea
                  rows={3}
                  value={editSummary}
                  onChange={(e) => setEditSummary(e.target.value)}
                  placeholder="Concise overview of your verified experience and technical strengths..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-sky-500 resize-none font-sans"
                />
              </div>

              <div>
                <label className="block font-semibold text-amber-300 mb-1 flex items-center gap-1.5">
                  <Trophy className="w-3.5 h-3.5 text-amber-400" />
                  Key Achievements, Certifications & Honors
                </label>
                <textarea
                  rows={3}
                  value={editAchievements}
                  onChange={(e) => setEditAchievements(e.target.value)}
                  placeholder="e.g. Published AI paper at NeurIPS 2024 | AWS Certified Solutions Architect | Hackathon Winner"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-amber-200 placeholder-slate-600 focus:outline-none focus:border-amber-500/50 resize-none font-sans"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1">
                  Verified Skills <span className="text-slate-500 font-normal">(Comma separated)</span>
                </label>
                <input
                  type="text"
                  value={editSkills}
                  onChange={(e) => setEditSkills(e.target.value)}
                  placeholder="Python, PyTorch, PostgreSQL, FastAPI..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-sky-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-300 mb-1">
                  Target Job Roles <span className="text-slate-500 font-normal">(Comma separated)</span>
                </label>
                <input
                  type="text"
                  value={editTargetTitles}
                  onChange={(e) => setEditTargetTitles(e.target.value)}
                  placeholder="AI Engineer, ML Engineer, Python Developer..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-sky-500"
                />
              </div>

              <div className="pt-3 border-t border-slate-800 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsEditModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white bg-slate-950 border border-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSaving}
                  className="px-5 py-2 rounded-xl text-xs font-bold bg-sky-600 hover:bg-sky-500 text-white transition-all disabled:opacity-50 flex items-center gap-1.5 shadow-lg shadow-sky-600/20"
                >
                  <Check className="w-4 h-4" />
                  {isSaving ? 'Saving...' : 'Save Profile'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

