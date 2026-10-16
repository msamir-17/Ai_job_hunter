import React, { useState, useEffect } from 'react';
import { User, Key, Search, ShieldCheck, Cpu, Briefcase, GraduationCap, Target, Edit2, Trash2, X, Check, Trophy, Lock, ShieldAlert, Sparkles, Plus } from 'lucide-react';
import { CandidateProfileResponse } from '../types/candidateProfile';
import { ExperienceItem, EducationItem } from '../types/resume';
import { getCandidateProfile, getActiveCandidateProfile, getMyProfile, updateMyProfile, updateCandidateProfile, deleteCandidateProfile, seedMyProfileFromFacts } from '../api/candidateProfile';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/ui/Card';
import { Alert } from '../components/ui/Alert';

export const CandidateProfilePage: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const [profileIdInput, setProfileIdInput] = useState<string>('');
  const [profile, setProfile] = useState<CandidateProfileResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [showInspector, setShowInspector] = useState<boolean>(false);

  // Inline Edit State
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [editHeadline, setEditHeadline] = useState<string>('');
  const [editSummary, setEditSummary] = useState<string>('');
  const [editAchievements, setEditAchievements] = useState<string>('');
  const [editSkills, setEditSkills] = useState<string>('');
  const [editTargetTitles, setEditTargetTitles] = useState<string>('');
  const [editExperience, setEditExperience] = useState<ExperienceItem[]>([]);
  const [editEducation, setEditEducation] = useState<EducationItem[]>([]);

  useEffect(() => {
    const loadProfile = async () => {
      setLoading(true);
      setError(null);
      try {
        if (isAuthenticated) {
          const data = await getMyProfile();
          setProfile(data);
          setProfileIdInput(data.id);
        } else {
          const data = await getActiveCandidateProfile();
          setProfile(data);
          setProfileIdInput(data.id);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load profile.');
      } finally {
        setLoading(false);
      }
    };
    loadProfile();
  }, [isAuthenticated, user?.id]);

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

  const handleStartEdit = () => {
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

    setEditExperience(
      (profile.experience || []).map((exp: any) => ({
        title: exp.title || '',
        company: exp.company || '',
        location: exp.location || '',
        start_date: exp.start_date || '',
        end_date: exp.end_date || '',
        description: exp.description || '',
        achievements: Array.isArray(exp.achievements)
          ? exp.achievements
          : exp.description
          ? [exp.description]
          : [],
        technologies: Array.isArray(exp.technologies) ? exp.technologies : [],
      }))
    );

    setEditEducation(
      (profile.education || []).map((edu: any) => ({
        degree: edu.degree || '',
        institution: edu.institution || '',
        field_of_study: edu.field_of_study || '',
        start_date: edu.start_date || '',
        end_date: edu.end_date || '',
        description: edu.description || '',
      }))
    );

    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
  };

  const handleAddExperience = () => {
    setEditExperience((prev) => [
      ...prev,
      {
        title: '',
        company: '',
        location: '',
        start_date: '',
        end_date: 'Present',
        description: '',
        achievements: [],
        technologies: [],
      },
    ]);
  };

  const handleUpdateExperience = (idx: number, updatedItem: ExperienceItem) => {
    setEditExperience((prev) => prev.map((item, i) => (i === idx ? updatedItem : item)));
  };

  const handleRemoveExperience = (idx: number) => {
    setEditExperience((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleAddEducation = () => {
    setEditEducation((prev) => [
      ...prev,
      {
        degree: '',
        institution: '',
        field_of_study: '',
        start_date: '',
        end_date: '',
        description: '',
      },
    ]);
  };

  const handleUpdateEducation = (idx: number, updatedItem: EducationItem) => {
    setEditEducation((prev) => prev.map((item, i) => (i === idx ? updatedItem : item)));
  };

  const handleRemoveEducation = (idx: number) => {
    setEditEducation((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleSyncTruthVault = async () => {
    setLoading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const data = await seedMyProfileFromFacts();
      setProfile(data);
      setSuccessMsg('Profile successfully populated with verified Truth Vault facts!');
    } catch (err: any) {
      setError(err.message || 'Failed to sync with Truth Vault.');
    } finally {
      setLoading(false);
    }
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

      let updated: CandidateProfileResponse;
      const updatePayload = {
        headline: editHeadline,
        summary: finalSummary,
        skills: skillsArray,
        target_titles: targetTitlesArray,
        experience: editExperience,
        education: editEducation,
      };

      if (isAuthenticated) {
        updated = await updateMyProfile(updatePayload);
      } else {
        updated = await updateCandidateProfile(profile.id, updatePayload);
      }

      setProfile(updated);
      setIsEditing(false);
      setSuccessMsg('Profile updated successfully in PostgreSQL database (Scoped to your account)!');
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
      {/* Page Header */}
      <div className="border-b border-slate-800 pb-6 mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-emerald-500/10 text-emerald-400 rounded-lg border border-emerald-500/20">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-white">
              Verified Candidate Profile
            </h1>
            <p className="text-xs text-slate-400">
              Verified candidate facts stored in PostgreSQL (Port 5435 Source of Truth)
            </p>
          </div>
        </div>

        {/* Multi-Tenant Status Badge */}
        {isAuthenticated && user ? (
          <div className="flex items-center gap-2 bg-emerald-950/40 border border-emerald-500/30 px-3 py-1.5 rounded-xl">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <div className="text-left">
              <span className="text-xs font-bold text-emerald-300 block">{user.full_name}</span>
              <span className="text-[10px] font-mono text-emerald-400/80">Tenant: {user.email}</span>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2 bg-amber-950/40 border border-amber-500/30 px-3 py-1.5 rounded-xl text-amber-300 text-xs">
            <Lock className="w-3.5 h-3.5 text-amber-400" />
            <span>Guest Mode • Sign in to activate multi-tenancy</span>
          </div>
        )}
      </div>

      {/* UUID Inspector & Cross-Tenant Test Toolbar */}
      <div className="mb-6 flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <ShieldAlert className="w-4 h-4 text-sky-400" />
          <span>
            {isAuthenticated
              ? `Currently viewing tenant profile for ${user?.email}`
              : 'Viewing default candidate profile'}
          </span>
        </div>

        <button
          onClick={() => setShowInspector(!showInspector)}
          className="text-xs font-medium text-sky-400 hover:text-sky-300 underline underline-offset-4"
        >
          {showInspector ? 'Hide UUID Cross-Tenant Inspector' : 'Test Cross-Tenant Isolation (Inspect UUID)'}
        </button>
      </div>

      {showInspector && (
        <Card className="mb-6 border-sky-800/40 bg-sky-950/10">
          <form onSubmit={handleFetch} className="flex flex-col sm:flex-row items-center gap-3">
            <div className="relative flex-1 w-full">
              <Key className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="text"
                value={profileIdInput}
                onChange={(e) => setProfileIdInput(e.target.value)}
                placeholder="Enter Candidate Profile UUID to test 403 Forbidden cross-tenant isolation..."
                className="w-full pl-9 pr-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white font-mono placeholder-slate-600 focus:outline-none focus:border-sky-500"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full sm:w-auto px-5 py-2 text-xs font-semibold rounded-lg bg-sky-600 hover:bg-sky-500 text-white transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5"
            >
              <Search className="w-3.5 h-3.5" />
              Inspect UUID
            </button>
          </form>
          <p className="text-[11px] text-slate-500 mt-2">
            💡 <strong>Security Verification:</strong> If you are logged in as Alice and query Bob's Profile UUID, the PostgreSQL API will return <code>403 Access Forbidden</code>.
          </p>
        </Card>
      )}

      {error && <Alert variant="error" className="mb-6">{error}</Alert>}
      {successMsg && <Alert variant="success" className="mb-6">{successMsg}</Alert>}

      {profile ? (
        isEditing ? (
          /* Inline Editing Card */
          <Card
            className="border-sky-500/40 ring-1 ring-sky-500/20"
            header={
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-sky-500/10 border border-sky-500/30 text-sky-400 rounded-lg">
                    <Edit2 className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-bold text-white">Editing Candidate Profile</h3>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30">
                        Inline Edit Mode
                      </span>
                    </div>
                    <p className="text-xs font-mono text-slate-400">Profile ID: {profile.id}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleCancelEdit}
                    disabled={isSaving}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition-colors"
                    title="Cancel changes and exit edit mode"
                  >
                    <X className="w-3.5 h-3.5" />
                    <span>Cancel</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleSaveProfile}
                    disabled={isSaving}
                    className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-xs font-bold text-white transition-all disabled:opacity-50 shadow-md shadow-sky-600/30"
                    title="Save profile changes directly to PostgreSQL"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>{isSaving ? 'Saving...' : 'Save Profile'}</span>
                  </button>
                </div>
              </div>
            }
          >
            <form onSubmit={handleSaveProfile} className="space-y-6 text-xs">
              {/* Headline Field */}
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                  Headline
                </label>
                <input
                  type="text"
                  value={editHeadline}
                  onChange={(e) => setEditHeadline(e.target.value)}
                  placeholder="e.g. AI/ML Engineer & Backend Systems Developer"
                  className="w-full bg-slate-950 border border-slate-700 focus:border-sky-500 rounded-lg px-3 py-2 text-xs text-white focus:outline-none transition-colors"
                />
              </div>

              {/* Professional Summary Field */}
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                  Professional Summary
                </label>
                <textarea
                  rows={4}
                  value={editSummary}
                  onChange={(e) => setEditSummary(e.target.value)}
                  placeholder="Concise overview of your verified experience and technical strengths..."
                  className="w-full bg-slate-950 border border-slate-700 focus:border-sky-500 rounded-lg p-3 text-xs text-slate-200 focus:outline-none leading-relaxed resize-y font-sans transition-colors"
                />
              </div>

              {/* Key Achievements Field */}
              <div>
                <label className="block text-[11px] font-semibold text-amber-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                  <Trophy className="w-3.5 h-3.5 text-amber-400" />
                  Key Achievements, Certifications & Honors
                </label>
                <textarea
                  rows={3}
                  value={editAchievements}
                  onChange={(e) => setEditAchievements(e.target.value)}
                  placeholder="e.g. Architected AI Job Hunter Co-Pilot with hybrid BM25 + pgvector retrieval (NDCG@10 1.0) | Published AI paper at NeurIPS 2024"
                  className="w-full bg-slate-950 border border-amber-900/40 focus:border-amber-500 rounded-lg p-3 text-xs text-amber-100 placeholder-slate-600 focus:outline-none leading-relaxed resize-y font-sans transition-colors"
                />
              </div>

              {/* Verified Technical Skills Field */}
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                  <Cpu className="w-4 h-4 text-indigo-400" />
                  Verified Technical Skills <span className="text-slate-500 font-normal lowercase">(comma separated)</span>
                </label>
                <textarea
                  rows={3}
                  value={editSkills}
                  onChange={(e) => setEditSkills(e.target.value)}
                  placeholder="Python, PyTorch, LangChain, PostgreSQL, FastAPI..."
                  className="w-full bg-slate-950 border border-slate-700 focus:border-indigo-500 rounded-lg p-3 text-xs text-indigo-200 font-mono focus:outline-none leading-relaxed resize-y transition-colors"
                />
                {editSkills.trim() && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {editSkills.split(',').map((s) => s.trim()).filter(Boolean).map((skill, idx) => (
                      <span key={idx} className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-300 font-mono text-[10px]">
                        {skill}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Target Job Roles Field */}
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                  <Target className="w-4 h-4 text-amber-400" />
                  Target Job Roles <span className="text-slate-500 font-normal lowercase">(comma separated)</span>
                </label>
                <input
                  type="text"
                  value={editTargetTitles}
                  onChange={(e) => setEditTargetTitles(e.target.value)}
                  placeholder="AI Engineer, Generative AI Specialist, Machine Learning Engineer..."
                  className="w-full bg-slate-950 border border-slate-700 focus:border-amber-500 rounded-lg px-3 py-2 text-xs text-amber-200 focus:outline-none transition-colors"
                />
                {editTargetTitles.trim() && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {editTargetTitles.split(',').map((t) => t.trim()).filter(Boolean).map((role, idx) => (
                      <span key={idx} className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-amber-300 font-medium text-[10px]">
                        {role}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Editable Work Experience Section */}
              <div className="pt-4 border-t border-slate-800 space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-[11px] font-semibold text-sky-400 uppercase tracking-wider flex items-center gap-1.5">
                    <Briefcase className="w-4 h-4 text-sky-400" />
                    Work Experience ({editExperience.length})
                  </h4>
                  <button
                    type="button"
                    onClick={handleAddExperience}
                    className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-sky-950/60 hover:bg-sky-900/60 border border-sky-500/30 text-sky-300 text-xs font-semibold transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Experience</span>
                  </button>
                </div>

                {editExperience.length === 0 ? (
                  <p className="text-slate-500 text-xs italic">No experience records added yet. Click 'Add Experience' above.</p>
                ) : (
                  <div className="space-y-4">
                    {editExperience.map((exp, idx) => {
                      const achievementsText = Array.isArray(exp.achievements) && exp.achievements.length > 0
                        ? exp.achievements.join('\n')
                        : (exp.description || '');
                      const techText = Array.isArray(exp.technologies) ? exp.technologies.join(', ') : '';

                      return (
                        <div key={idx} className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3">
                          <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                            <span className="text-xs font-bold text-white">Experience #{idx + 1}</span>
                            <button
                              type="button"
                              onClick={() => handleRemoveExperience(idx)}
                              className="text-rose-400 hover:text-rose-300 p-1 rounded hover:bg-rose-950/40 transition-colors"
                              title="Delete experience"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div>
                              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                                Job Title / Role
                              </label>
                              <input
                                type="text"
                                value={exp.title || ''}
                                onChange={(e) => handleUpdateExperience(idx, { ...exp, title: e.target.value })}
                                placeholder="e.g. Next.js Intern or Senior AI Engineer"
                                className="w-full bg-slate-900 border border-slate-700 focus:border-sky-500 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none"
                              />
                            </div>
                            <div>
                              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                                Company
                              </label>
                              <input
                                type="text"
                                value={exp.company || ''}
                                onChange={(e) => handleUpdateExperience(idx, { ...exp, company: e.target.value })}
                                placeholder="e.g. Trex InfoTech"
                                className="w-full bg-slate-900 border border-slate-700 focus:border-sky-500 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none"
                              />
                            </div>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                            <div>
                              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                                Location
                              </label>
                              <input
                                type="text"
                                value={exp.location || ''}
                                onChange={(e) => handleUpdateExperience(idx, { ...exp, location: e.target.value })}
                                placeholder="e.g. Mumbai, India or Remote"
                                className="w-full bg-slate-900 border border-slate-700 focus:border-sky-500 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none"
                              />
                            </div>
                            <div>
                              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                                Start Date
                              </label>
                              <input
                                type="text"
                                value={exp.start_date || ''}
                                onChange={(e) => handleUpdateExperience(idx, { ...exp, start_date: e.target.value })}
                                placeholder="e.g. Jul 2025"
                                className="w-full bg-slate-900 border border-slate-700 focus:border-sky-500 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none"
                              />
                            </div>
                            <div>
                              <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                                End Date
                              </label>
                              <input
                                type="text"
                                value={exp.end_date || ''}
                                onChange={(e) => handleUpdateExperience(idx, { ...exp, end_date: e.target.value })}
                                placeholder="e.g. Aug 2025 or Present"
                                className="w-full bg-slate-900 border border-slate-700 focus:border-sky-500 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none"
                              />
                            </div>
                          </div>

                          <div>
                            <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                              Responsibilities & Key Achievements <span className="text-slate-500 font-normal lowercase">(one bullet point per line)</span>
                            </label>
                            <textarea
                              rows={3}
                              value={achievementsText}
                              onChange={(e) => {
                                const lines = e.target.value.split('\n');
                                handleUpdateExperience(idx, {
                                  ...exp,
                                  description: e.target.value,
                                  achievements: lines.filter((l) => l.trim().length > 0),
                                });
                              }}
                              placeholder="Built full-stack web applications with Next.js and REST APIs&#10;Built API-driven automation pipelines handling end-to-end data flow..."
                              className="w-full bg-slate-900 border border-slate-700 focus:border-sky-500 rounded-lg p-2.5 text-xs text-slate-200 focus:outline-none leading-relaxed resize-y font-sans"
                            />
                          </div>

                          <div>
                            <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                              Technologies & Tools <span className="text-slate-500 font-normal lowercase">(comma separated)</span>
                            </label>
                            <input
                              type="text"
                              value={techText}
                              onChange={(e) => {
                                const techs = e.target.value.split(',').map((t) => t.trim()).filter(Boolean);
                                handleUpdateExperience(idx, { ...exp, technologies: techs });
                              }}
                              placeholder="Next.js, REST APIs, TypeScript..."
                              className="w-full bg-slate-900 border border-slate-700 focus:border-sky-500 rounded-lg px-2.5 py-1.5 text-xs text-sky-200 font-mono focus:outline-none"
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Editable Education Section */}
              <div className="pt-4 border-t border-slate-800 space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                    <GraduationCap className="w-4 h-4 text-emerald-400" />
                    Education ({editEducation.length})
                  </h4>
                  <button
                    type="button"
                    onClick={handleAddEducation}
                    className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-950/60 hover:bg-emerald-900/60 border border-emerald-500/30 text-emerald-300 text-xs font-semibold transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Education</span>
                  </button>
                </div>

                {editEducation.length === 0 ? (
                  <p className="text-slate-500 text-xs italic">No education records added yet. Click 'Add Education' above.</p>
                ) : (
                  <div className="space-y-4">
                    {editEducation.map((edu, idx) => (
                      <div key={idx} className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3">
                        <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                          <span className="text-xs font-bold text-white">Education #{idx + 1}</span>
                          <button
                            type="button"
                            onClick={() => handleRemoveEducation(idx)}
                            className="text-rose-400 hover:text-rose-300 p-1 rounded hover:bg-rose-950/40 transition-colors"
                            title="Delete education"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          <div>
                            <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                              Degree / Certificate
                            </label>
                            <input
                              type="text"
                              value={edu.degree || ''}
                              onChange={(e) => handleUpdateEducation(idx, { ...edu, degree: e.target.value })}
                              placeholder="e.g. Bachelor of Computer Science"
                              className="w-full bg-slate-900 border border-slate-700 focus:border-emerald-500 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none"
                            />
                          </div>
                          <div>
                            <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                              Field of Study / Major
                            </label>
                            <input
                              type="text"
                              value={edu.field_of_study || ''}
                              onChange={(e) => handleUpdateEducation(idx, { ...edu, field_of_study: e.target.value })}
                              placeholder="e.g. AIML or Computer Science"
                              className="w-full bg-slate-900 border border-slate-700 focus:border-emerald-500 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none"
                            />
                          </div>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                          <div>
                            <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                              Institution / University
                            </label>
                            <input
                              type="text"
                              value={edu.institution || ''}
                              onChange={(e) => handleUpdateEducation(idx, { ...edu, institution: e.target.value })}
                              placeholder="e.g. Viva Institute of Technology"
                              className="w-full bg-slate-900 border border-slate-700 focus:border-emerald-500 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none"
                            />
                          </div>
                          <div>
                            <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                              Start Date
                            </label>
                            <input
                              type="text"
                              value={edu.start_date || ''}
                              onChange={(e) => handleUpdateEducation(idx, { ...edu, start_date: e.target.value })}
                              placeholder="e.g. Jan 2023"
                              className="w-full bg-slate-900 border border-slate-700 focus:border-emerald-500 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none"
                            />
                          </div>
                          <div>
                            <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                              End Date
                            </label>
                            <input
                              type="text"
                              value={edu.end_date || ''}
                              onChange={(e) => handleUpdateEducation(idx, { ...edu, end_date: e.target.value })}
                              placeholder="e.g. Dec 2026 or Graduated"
                              className="w-full bg-slate-900 border border-slate-700 focus:border-emerald-500 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none"
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Bottom Actions */}
              <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-2.5">
                <button
                  type="button"
                  onClick={handleCancelEdit}
                  disabled={isSaving}
                  className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSaving}
                  className="px-5 py-2 rounded-lg text-xs font-bold bg-sky-600 hover:bg-sky-500 text-white transition-all disabled:opacity-50 flex items-center gap-1.5 shadow-md shadow-sky-600/30"
                >
                  <Check className="w-4 h-4" />
                  <span>{isSaving ? 'Saving...' : 'Save Profile'}</span>
                </button>
              </div>
            </form>
          </Card>
        ) : (
          /* Read-Only Profile Card */
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
                  onClick={handleSyncTruthVault}
                  disabled={loading}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white transition-colors shadow disabled:opacity-50"
                  title="Populate profile with verified facts from Truth Vault"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Sync Truth Vault</span>
                </button>

                <button
                  onClick={handleStartEdit}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-xs font-semibold text-white transition-colors shadow"
                  title="Edit candidate profile fields inline"
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
                  <div className="space-y-3">
                    <p className="text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                      {profile.summary.includes('Key Achievements & Certifications:')
                        ? profile.summary.split('Key Achievements & Certifications:')[0].trim()
                        : profile.summary}
                    </p>
                    {profile.summary.includes('Key Achievements & Certifications:') && (
                      <div className="bg-amber-950/20 border border-amber-500/20 p-3 rounded-lg">
                        <h5 className="text-[10px] font-bold text-amber-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                          <Trophy className="w-3.5 h-3.5 text-amber-400" />
                          Key Achievements, Certifications & Honors
                        </h5>
                        <p className="text-amber-200/90 leading-relaxed text-xs">
                          {profile.summary.split('Key Achievements & Certifications:')[1].trim()}
                        </p>
                      </div>
                    )}
                  </div>
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
                    {profile.experience.map((exp: any, idx: number) => {
                      const achievementsList: string[] = Array.isArray(exp.achievements) && exp.achievements.length > 0
                        ? exp.achievements
                        : exp.description ? [exp.description] : [];
                      const techList: string[] = Array.isArray(exp.technologies) ? exp.technologies : [];

                      return (
                        <div key={idx} className="p-4 bg-slate-950/60 rounded-xl border border-slate-800 space-y-2">
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                            <div>
                              <span className="font-bold text-white text-xs">{exp.title || 'Role'}</span>
                              {exp.company && <span className="text-sky-300 font-medium text-xs"> at {exp.company}</span>}
                              {exp.location && <span className="text-[11px] text-slate-500"> • {exp.location}</span>}
                            </div>
                            <span className="text-[11px] font-mono text-slate-400">
                              {exp.start_date || ''}{exp.start_date && exp.end_date ? ' - ' : ''}{exp.end_date || ''}
                            </span>
                          </div>

                          {/* Achievements Bullet Points */}
                          {achievementsList.length > 0 && (
                            <ul className="space-y-1.5 pt-1">
                              {achievementsList.map((ach: string, aIdx: number) => (
                                <li key={aIdx} className="text-slate-300 text-xs leading-relaxed flex items-start gap-2">
                                  <span className="text-sky-400 mt-0.5 select-none font-bold">•</span>
                                  <span>{ach}</span>
                                </li>
                              ))}
                            </ul>
                          )}

                          {/* Technologies Chips */}
                          {techList.length > 0 && (
                            <div className="flex flex-wrap gap-1 pt-1">
                              {techList.map((tech: string, tIdx: number) => (
                                <span key={tIdx} className="px-2 py-0.5 rounded bg-sky-950/40 border border-sky-800/40 text-sky-300 text-[10px] font-mono">
                                  {tech}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}
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
                        <span className="text-[10px] font-mono text-slate-500">
                          {edu.start_date || ''}{edu.start_date && edu.end_date ? ' - ' : ''}{edu.end_date || ''}
                        </span>
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
        )
      ) : (
        <Card className="text-center py-12 text-slate-500 text-xs">
          Enter a Candidate Profile UUID above to view verified profile records.
        </Card>
      )}
    </div>
  );
};

