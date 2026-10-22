import React, { useState, useEffect } from 'react';
import {
  Key,
  Search,
  Cpu,
  Briefcase,
  GraduationCap,
  Target,
  Edit2,
  Trash2,
  Check,
  Trophy,
  Lock,
  Plus,
  RefreshCw,
} from 'lucide-react';
import { CandidateProfileResponse } from '../types/candidateProfile';
import { ExperienceItem, EducationItem } from '../types/resume';
import {
  getCandidateProfile,
  getActiveCandidateProfile,
  getMyProfile,
  updateMyProfile,
  updateCandidateProfile,
  deleteCandidateProfile,
  seedMyProfileFromFacts,
} from '../api/candidateProfile';
import { useAuth } from '../context/AuthContext';
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

    setEditSkills(
      (profile.skills || [])
        .map((s: any) => (typeof s === 'string' ? s : s.name || ''))
        .join(', ')
    );
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
      setSuccessMsg('Profile populated from verified source of truth.');
    } catch (err: any) {
      setError(err.message || 'Failed to sync with verified profile.');
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

      const updatePayload = {
        headline: editHeadline,
        summary: finalSummary,
        skills: skillsArray,
        target_titles: targetTitlesArray,
        experience: editExperience,
        education: editEducation,
      };

      let updated: CandidateProfileResponse;
      if (isAuthenticated) {
        updated = await updateMyProfile(updatePayload);
      } else {
        updated = await updateCandidateProfile(profile.id, updatePayload);
      }

      setProfile(updated);
      setIsEditing(false);
      setSuccessMsg('Profile updated successfully.');
    } catch (err: any) {
      setError(err.message || 'Failed to update profile.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteProfile = async () => {
    if (!profile) return;
    if (!window.confirm('Are you sure you want to delete this profile? This action cannot be undone.')) {
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
      <div className="border-b border-slate-200 pb-5 mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">
            Candidate Profile
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Verified candidate facts and credentials
          </p>
        </div>

        {/* Tenant Status */}
        {isAuthenticated && user ? (
          <div className="flex items-center gap-2 bg-slate-100 border border-slate-200 px-3 py-1.5 rounded-lg">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <div className="text-left text-xs">
              <span className="font-semibold text-slate-800">{user.full_name}</span>
              <span className="text-slate-400 ml-1.5">({user.email})</span>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 bg-slate-100 border border-slate-200 px-3 py-1.5 rounded-lg text-slate-600 text-xs">
            <Lock className="w-3.5 h-3.5 text-slate-400" />
            <span>Guest Mode — sign in to save your personal profile</span>
          </div>
        )}
      </div>

      {/* Inspector / UUID Toolbar */}
      <div className="mb-6 flex flex-col sm:flex-row items-center justify-between gap-3 bg-white p-3 rounded-lg border border-slate-200 text-xs">
        <span className="text-slate-600">
          {isAuthenticated
            ? `Viewing profile for ${user?.email}`
            : 'Viewing default profile'}
        </span>

        <button
          onClick={() => setShowInspector(!showInspector)}
          className="text-xs text-blue-600 hover:text-blue-800 font-medium"
        >
          {showInspector ? 'Hide UUID Inspector' : 'Inspect by UUID'}
        </button>
      </div>

      {showInspector && (
        <div className="mb-6 bg-white border border-slate-200 rounded-lg p-4 space-y-2">
          <form onSubmit={handleFetch} className="flex flex-col sm:flex-row items-center gap-2">
            <div className="relative flex-1 w-full">
              <Key className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={profileIdInput}
                onChange={(e) => setProfileIdInput(e.target.value)}
                placeholder="Enter Candidate Profile UUID..."
                className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-900 font-mono placeholder-slate-400 focus:outline-none focus:border-blue-500"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full sm:w-auto px-4 py-2 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-900 text-white transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5"
            >
              <Search className="w-3.5 h-3.5" />
              Inspect
            </button>
          </form>
          <p className="text-[11px] text-slate-500">
            Tenant isolation check: querying another user's UUID will return a 403 Forbidden response.
          </p>
        </div>
      )}

      {error && <Alert variant="error" className="mb-6">{error}</Alert>}
      {successMsg && <Alert variant="success" className="mb-6">{successMsg}</Alert>}

      {profile ? (
        isEditing ? (
          /* Inline Editing Card */
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4 mb-5">
              <div>
                <h3 className="text-base font-semibold text-slate-900">Edit Profile</h3>
                <p className="text-xs font-mono text-slate-400 mt-0.5">ID: {profile.id}</p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleCancelEdit}
                  disabled={isSaving}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-xs font-medium text-slate-600 transition-colors"
                >
                  Cancel
                </button>

                <button
                  type="button"
                  onClick={handleSaveProfile}
                  disabled={isSaving}
                  className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-xs font-medium text-white transition-colors disabled:opacity-50 flex items-center gap-1.5"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>{isSaving ? 'Saving...' : 'Save Profile'}</span>
                </button>
              </div>
            </div>

            <form onSubmit={handleSaveProfile} className="space-y-5 text-xs">
              {/* Headline */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Headline
                </label>
                <input
                  type="text"
                  value={editHeadline}
                  onChange={(e) => setEditHeadline(e.target.value)}
                  placeholder="e.g. AI/ML Engineer & Backend Systems Developer"
                  className="w-full bg-white border border-slate-300 focus:border-blue-500 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none transition-colors"
                />
              </div>

              {/* Professional Summary */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Professional Summary
                </label>
                <textarea
                  rows={4}
                  value={editSummary}
                  onChange={(e) => setEditSummary(e.target.value)}
                  placeholder="Concise overview of your verified experience and technical strengths..."
                  className="w-full bg-white border border-slate-300 focus:border-blue-500 rounded-lg p-3 text-xs text-slate-900 focus:outline-none leading-relaxed resize-y font-sans transition-colors"
                />
              </div>

              {/* Key Achievements */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center gap-1.5">
                  <Trophy className="w-3.5 h-3.5 text-amber-500" />
                  Key Achievements & Certifications
                </label>
                <textarea
                  rows={3}
                  value={editAchievements}
                  onChange={(e) => setEditAchievements(e.target.value)}
                  placeholder="e.g. Published paper at NeurIPS 2024 | AWS Certified Solutions Architect"
                  className="w-full bg-white border border-slate-300 focus:border-blue-500 rounded-lg p-3 text-xs text-slate-900 placeholder-slate-400 focus:outline-none leading-relaxed resize-y font-sans transition-colors"
                />
              </div>

              {/* Verified Technical Skills */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-blue-600" />
                  Technical Skills <span className="text-slate-400 font-normal lowercase">(comma separated)</span>
                </label>
                <textarea
                  rows={3}
                  value={editSkills}
                  onChange={(e) => setEditSkills(e.target.value)}
                  placeholder="Python, PyTorch, LangChain, PostgreSQL, FastAPI..."
                  className="w-full bg-white border border-slate-300 focus:border-blue-500 rounded-lg p-3 text-xs text-slate-900 font-mono focus:outline-none leading-relaxed resize-y transition-colors"
                />
                {editSkills.trim() && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {editSkills.split(',').map((s) => s.trim()).filter(Boolean).map((skill, idx) => (
                      <span key={idx} className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-mono text-[11px]">
                        {skill}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Target Job Roles */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1 flex items-center gap-1.5">
                  <Target className="w-3.5 h-3.5 text-slate-600" />
                  Target Job Roles <span className="text-slate-400 font-normal lowercase">(comma separated)</span>
                </label>
                <input
                  type="text"
                  value={editTargetTitles}
                  onChange={(e) => setEditTargetTitles(e.target.value)}
                  placeholder="AI Engineer, Machine Learning Engineer, Python Developer..."
                  className="w-full bg-white border border-slate-300 focus:border-blue-500 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none transition-colors"
                />
                {editTargetTitles.trim() && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {editTargetTitles.split(',').map((t) => t.trim()).filter(Boolean).map((role, idx) => (
                      <span key={idx} className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 text-[11px] font-medium">
                        {role}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Editable Work Experience Section */}
              <div className="pt-4 border-t border-slate-200 space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wide flex items-center gap-1.5">
                    <Briefcase className="w-3.5 h-3.5 text-slate-500" />
                    Work Experience ({editExperience.length})
                  </h4>
                  <button
                    type="button"
                    onClick={handleAddExperience}
                    className="flex items-center gap-1 px-2.5 py-1 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-medium transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Experience</span>
                  </button>
                </div>

                {editExperience.length === 0 ? (
                  <p className="text-slate-400 text-xs italic">No experience records added yet.</p>
                ) : (
                  <div className="space-y-3">
                    {editExperience.map((exp, idx) => {
                      const achievementsText = Array.isArray(exp.achievements) && exp.achievements.length > 0
                        ? exp.achievements.join('\n')
                        : (exp.description || '');
                      const techText = Array.isArray(exp.technologies) ? exp.technologies.join(', ') : '';

                      return (
                        <div key={idx} className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-3">
                          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                            <span className="text-xs font-semibold text-slate-700">Role #{idx + 1}</span>
                            <button
                              type="button"
                              onClick={() => handleRemoveExperience(idx)}
                              className="text-red-500 hover:text-red-700 p-1 rounded hover:bg-red-50 transition-colors"
                              title="Delete experience"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div>
                              <label className="block text-[11px] font-medium text-slate-600 mb-1">
                                Job Title
                              </label>
                              <input
                                type="text"
                                value={exp.title || ''}
                                onChange={(e) => handleUpdateExperience(idx, { ...exp, title: e.target.value })}
                                placeholder="e.g. Senior Software Engineer"
                                className="w-full bg-white border border-slate-300 focus:border-blue-500 rounded-lg px-2.5 py-1.5 text-xs text-slate-900 focus:outline-none"
                              />
                            </div>
                            <div>
                              <label className="block text-[11px] font-medium text-slate-600 mb-1">
                                Company
                              </label>
                              <input
                                type="text"
                                value={exp.company || ''}
                                onChange={(e) => handleUpdateExperience(idx, { ...exp, company: e.target.value })}
                                placeholder="e.g. Acme Inc."
                                className="w-full bg-white border border-slate-300 focus:border-blue-500 rounded-lg px-2.5 py-1.5 text-xs text-slate-900 focus:outline-none"
                              />
                            </div>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                            <div>
                              <label className="block text-[11px] font-medium text-slate-600 mb-1">
                                Location
                              </label>
                              <input
                                type="text"
                                value={exp.location || ''}
                                onChange={(e) => handleUpdateExperience(idx, { ...exp, location: e.target.value })}
                                placeholder="e.g. New York, NY / Remote"
                                className="w-full bg-white border border-slate-300 focus:border-blue-500 rounded-lg px-2.5 py-1.5 text-xs text-slate-900 focus:outline-none"
                              />
                            </div>
                            <div>
                              <label className="block text-[11px] font-medium text-slate-600 mb-1">
                                Start Date
                              </label>
                              <input
                                type="text"
                                value={exp.start_date || ''}
                                onChange={(e) => handleUpdateExperience(idx, { ...exp, start_date: e.target.value })}
                                placeholder="e.g. Jan 2023"
                                className="w-full bg-white border border-slate-300 focus:border-blue-500 rounded-lg px-2.5 py-1.5 text-xs text-slate-900 focus:outline-none"
                              />
                            </div>
                            <div>
                              <label className="block text-[11px] font-medium text-slate-600 mb-1">
                                End Date
                              </label>
                              <input
                                type="text"
                                value={exp.end_date || ''}
                                onChange={(e) => handleUpdateExperience(idx, { ...exp, end_date: e.target.value })}
                                placeholder="e.g. Present"
                                className="w-full bg-white border border-slate-300 focus:border-blue-500 rounded-lg px-2.5 py-1.5 text-xs text-slate-900 focus:outline-none"
                              />
                            </div>
                          </div>

                          <div>
                            <label className="block text-[11px] font-medium text-slate-600 mb-1">
                              Responsibilities & Key Achievements <span className="text-slate-400 font-normal lowercase">(one per line)</span>
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
                              placeholder="Led architecture redesign for core microservices&#10;Reduced latency by 40%..."
                              className="w-full bg-white border border-slate-300 focus:border-blue-500 rounded-lg p-2.5 text-xs text-slate-900 focus:outline-none leading-relaxed resize-y font-sans"
                            />
                          </div>

                          <div>
                            <label className="block text-[11px] font-medium text-slate-600 mb-1">
                              Technologies <span className="text-slate-400 font-normal lowercase">(comma separated)</span>
                            </label>
                            <input
                              type="text"
                              value={techText}
                              onChange={(e) => {
                                const techs = e.target.value.split(',').map((t) => t.trim()).filter(Boolean);
                                handleUpdateExperience(idx, { ...exp, technologies: techs });
                              }}
                              placeholder="React, TypeScript, Node.js..."
                              className="w-full bg-white border border-slate-300 focus:border-blue-500 rounded-lg px-2.5 py-1.5 text-xs text-slate-900 font-mono focus:outline-none"
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Editable Education Section */}
              <div className="pt-4 border-t border-slate-200 space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wide flex items-center gap-1.5">
                    <GraduationCap className="w-3.5 h-3.5 text-slate-500" />
                    Education ({editEducation.length})
                  </h4>
                  <button
                    type="button"
                    onClick={handleAddEducation}
                    className="flex items-center gap-1 px-2.5 py-1 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-medium transition-colors"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Education</span>
                  </button>
                </div>

                {editEducation.length === 0 ? (
                  <p className="text-slate-400 text-xs italic">No education records added yet.</p>
                ) : (
                  <div className="space-y-3">
                    {editEducation.map((edu, idx) => (
                      <div key={idx} className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-3">
                        <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                          <span className="text-xs font-semibold text-slate-700">Education #{idx + 1}</span>
                          <button
                            type="button"
                            onClick={() => handleRemoveEducation(idx)}
                            className="text-red-500 hover:text-red-700 p-1 rounded hover:bg-red-50 transition-colors"
                            title="Delete education"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                          <div>
                            <label className="block text-[11px] font-medium text-slate-600 mb-1">
                              Degree
                            </label>
                            <input
                              type="text"
                              value={edu.degree || ''}
                              onChange={(e) => handleUpdateEducation(idx, { ...edu, degree: e.target.value })}
                              placeholder="e.g. Bachelor of Science"
                              className="w-full bg-white border border-slate-300 focus:border-blue-500 rounded-lg px-2.5 py-1.5 text-xs text-slate-900 focus:outline-none"
                            />
                          </div>
                          <div>
                            <label className="block text-[11px] font-medium text-slate-600 mb-1">
                              Field of Study
                            </label>
                            <input
                              type="text"
                              value={edu.field_of_study || ''}
                              onChange={(e) => handleUpdateEducation(idx, { ...edu, field_of_study: e.target.value })}
                              placeholder="e.g. Computer Science"
                              className="w-full bg-white border border-slate-300 focus:border-blue-500 rounded-lg px-2.5 py-1.5 text-xs text-slate-900 focus:outline-none"
                            />
                          </div>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                          <div>
                            <label className="block text-[11px] font-medium text-slate-600 mb-1">
                              Institution
                            </label>
                            <input
                              type="text"
                              value={edu.institution || ''}
                              onChange={(e) => handleUpdateEducation(idx, { ...edu, institution: e.target.value })}
                              placeholder="e.g. Stanford University"
                              className="w-full bg-white border border-slate-300 focus:border-blue-500 rounded-lg px-2.5 py-1.5 text-xs text-slate-900 focus:outline-none"
                            />
                          </div>
                          <div>
                            <label className="block text-[11px] font-medium text-slate-600 mb-1">
                              Start Date
                            </label>
                            <input
                              type="text"
                              value={edu.start_date || ''}
                              onChange={(e) => handleUpdateEducation(idx, { ...edu, start_date: e.target.value })}
                              placeholder="e.g. Sep 2019"
                              className="w-full bg-white border border-slate-300 focus:border-blue-500 rounded-lg px-2.5 py-1.5 text-xs text-slate-900 focus:outline-none"
                            />
                          </div>
                          <div>
                            <label className="block text-[11px] font-medium text-slate-600 mb-1">
                              End Date
                            </label>
                            <input
                              type="text"
                              value={edu.end_date || ''}
                              onChange={(e) => handleUpdateEducation(idx, { ...edu, end_date: e.target.value })}
                              placeholder="e.g. Jun 2023"
                              className="w-full bg-white border border-slate-300 focus:border-blue-500 rounded-lg px-2.5 py-1.5 text-xs text-slate-900 focus:outline-none"
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Bottom Actions */}
              <div className="pt-4 border-t border-slate-200 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={handleCancelEdit}
                  disabled={isSaving}
                  className="px-4 py-2 rounded-lg text-xs font-medium text-slate-600 hover:text-slate-800 bg-white border border-slate-200 hover:bg-slate-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSaving}
                  className="px-4 py-2 rounded-lg text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white transition-colors disabled:opacity-50 flex items-center gap-1.5"
                >
                  <Check className="w-3.5 h-3.5" />
                  <span>{isSaving ? 'Saving...' : 'Save Profile'}</span>
                </button>
              </div>
            </form>
          </div>
        ) : (
          /* Read-Only Profile Card */
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
              <div>
                <h2 className="text-lg font-bold text-slate-900">{profile.headline || 'Candidate Profile'}</h2>
                <p className="text-xs font-mono text-slate-400 mt-0.5">ID: {profile.id}</p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleSyncTruthVault}
                  disabled={loading}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-xs font-medium text-slate-700 transition-colors disabled:opacity-50"
                  title="Populate profile from verified facts"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                  <span>Sync Facts</span>
                </button>

                <button
                  onClick={handleStartEdit}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-xs font-medium text-white transition-colors"
                  title="Edit profile"
                >
                  <Edit2 className="w-3.5 h-3.5" />
                  <span>Edit Profile</span>
                </button>

                <button
                  onClick={handleDeleteProfile}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-red-200 hover:bg-red-50 text-red-600 text-xs font-medium transition-colors"
                  title="Delete profile"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Delete</span>
                </button>
              </div>
            </div>

            {/* Summary */}
            {profile.summary && (
              <div>
                <h4 className="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-2">
                  Professional Summary
                </h4>
                <div className="space-y-3">
                  <p className="text-slate-700 leading-relaxed bg-slate-50 p-3.5 rounded-lg border border-slate-200 text-xs">
                    {profile.summary.includes('Key Achievements & Certifications:')
                      ? profile.summary.split('Key Achievements & Certifications:')[0].trim()
                      : profile.summary}
                  </p>
                  {profile.summary.includes('Key Achievements & Certifications:') && (
                    <div className="bg-amber-50 border border-amber-200 p-3.5 rounded-lg">
                      <h5 className="text-[11px] font-semibold text-amber-800 uppercase tracking-wide mb-1 flex items-center gap-1.5">
                        <Trophy className="w-3.5 h-3.5 text-amber-600" />
                        Key Achievements & Certifications
                      </h5>
                      <p className="text-amber-900 leading-relaxed text-xs">
                        {profile.summary.split('Key Achievements & Certifications:')[1].trim()}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Skills */}
            {profile.skills && profile.skills.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-blue-600" />
                  Technical Skills ({profile.skills.length})
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {profile.skills.map((skill: any, idx: number) => (
                    <span key={idx} className="px-2.5 py-1 rounded bg-blue-50 text-blue-700 border border-blue-200 font-mono text-[11px]">
                      {typeof skill === 'string' ? skill : skill.name || JSON.stringify(skill)}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Work Experience */}
            {profile.experience && profile.experience.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                  <Briefcase className="w-3.5 h-3.5 text-slate-500" />
                  Work Experience ({profile.experience.length})
                </h4>
                <div className="space-y-3">
                  {profile.experience.map((exp: any, idx: number) => {
                    const achievementsList: string[] = Array.isArray(exp.achievements) && exp.achievements.length > 0
                      ? exp.achievements
                      : exp.description ? [exp.description] : [];
                    const techList: string[] = Array.isArray(exp.technologies) ? exp.technologies : [];

                    return (
                      <div key={idx} className="p-4 bg-slate-50 rounded-lg border border-slate-200 space-y-2">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                          <div>
                            <span className="font-semibold text-slate-900 text-xs">{exp.title || 'Role'}</span>
                            {exp.company && <span className="text-slate-600 font-medium text-xs"> at {exp.company}</span>}
                            {exp.location && <span className="text-[11px] text-slate-400"> • {exp.location}</span>}
                          </div>
                          <span className="text-[11px] font-mono text-slate-500">
                            {exp.start_date || ''}{exp.start_date && exp.end_date ? ' – ' : ''}{exp.end_date || ''}
                          </span>
                        </div>

                        {achievementsList.length > 0 && (
                          <ul className="space-y-1 pt-1">
                            {achievementsList.map((ach: string, aIdx: number) => (
                              <li key={aIdx} className="text-slate-600 text-xs leading-relaxed flex items-start gap-2">
                                <span className="text-slate-400 mt-0.5 select-none font-bold">•</span>
                                <span>{ach}</span>
                              </li>
                            ))}
                          </ul>
                        )}

                        {techList.length > 0 && (
                          <div className="flex flex-wrap gap-1 pt-1">
                            {techList.map((tech: string, tIdx: number) => (
                              <span key={tIdx} className="px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-600 text-[10px] font-mono">
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

            {/* Education */}
            {profile.education && profile.education.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                  <GraduationCap className="w-3.5 h-3.5 text-slate-500" />
                  Education ({profile.education.length})
                </h4>
                <div className="space-y-2">
                  {profile.education.map((edu: any, idx: number) => (
                    <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between">
                      <div>
                        <span className="font-semibold text-slate-900 text-xs">{edu.degree || 'Degree'} {edu.field_of_study && `in ${edu.field_of_study}`}</span>
                        {edu.institution && <p className="text-slate-500 text-[11px]">{edu.institution}</p>}
                      </div>
                      <span className="text-[11px] font-mono text-slate-400">
                        {edu.start_date || ''}{edu.start_date && edu.end_date ? ' – ' : ''}{edu.end_date || ''}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Target Job Roles */}
            {profile.target_titles && profile.target_titles.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                  <Target className="w-3.5 h-3.5 text-slate-500" />
                  Target Job Roles ({profile.target_titles.length})
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {profile.target_titles.map((title: string, idx: number) => (
                    <span key={idx} className="px-2.5 py-1 rounded bg-slate-100 text-slate-700 border border-slate-200 font-medium text-[11px]">
                      {title}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl text-center py-12 text-slate-400 text-xs">
          No profile loaded. Sign in or enter a Candidate Profile UUID above.
        </div>
      )}
    </div>
  );
};
