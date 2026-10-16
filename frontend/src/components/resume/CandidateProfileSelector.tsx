import React, { useState, useEffect } from 'react';
import { User, Key, Plus, CheckCircle, AlertCircle, RefreshCw, Zap } from 'lucide-react';
import { CandidateProfileResponse } from '../../types/candidateProfile';
import { getCandidateProfile, createCandidateProfile, getActiveCandidateProfile } from '../../api/candidateProfile';
import { Card } from '../ui/Card';
import { Alert } from '../ui/Alert';

interface CandidateProfileSelectorProps {
  currentProfile: CandidateProfileResponse | null;
  onProfileSelect: (profile: CandidateProfileResponse) => void;
}

export const CandidateProfileSelector: React.FC<CandidateProfileSelectorProps> = ({
  currentProfile,
  onProfileSelect,
}) => {
  const [profileIdInput, setProfileIdInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  // Explicit creation modal/form state
  const [showCreateForm, setShowCreateForm] = useState<boolean>(false);
  const [newUserId, setNewUserId] = useState<string>('');
  const [newHeadline, setNewHeadline] = useState<string>('');
  const [newSummary, setNewSummary] = useState<string>('');

  const handleAutoConnect = async () => {
    setLoading(true);
    setError(null);
    try {
      const active = await getActiveCandidateProfile();
      onProfileSelect(active);
    } catch (err: any) {
      setError(err.message || 'Failed to initialize active candidate profile.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!currentProfile) {
      handleAutoConnect();
    }
  }, []);

  const handleFetchProfile = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!profileIdInput.trim()) {
      setError('Please enter a valid Candidate Profile UUID.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const profile = await getCandidateProfile(profileIdInput.trim());
      onProfileSelect(profile);
      setProfileIdInput('');
    } catch (err: any) {
      setError(err.message || 'Failed to fetch candidate profile. Ensure the ID is valid.');
    } finally {
      setLoading(false);
    }
  };

  const handleExplicitCreateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUserId.trim()) {
      setError('User ID UUID is required to create a candidate profile.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const created = await createCandidateProfile({
        user_id: newUserId.trim(),
        headline: newHeadline.trim() || undefined,
        summary: newSummary.trim() || undefined,
      });
      onProfileSelect(created);
      setShowCreateForm(false);
      setNewUserId('');
      setNewHeadline('');
      setNewSummary('');
    } catch (err: any) {
      setError(err.message || 'Failed to create candidate profile. Ensure User ID exists.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="mb-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-50 text-blue-600 rounded-lg border border-blue-200">
            <User className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              Candidate Profile
              {currentProfile && (
                <span className="inline-flex items-center gap-1 text-[11px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200 font-mono">
                  <CheckCircle className="w-3 h-3 text-emerald-600" /> Active
                </span>
              )}
            </h3>
            <p className="text-xs text-slate-500">
              Active profile for resume upload and fact extraction
            </p>
          </div>
        </div>

        {currentProfile ? (
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200 text-slate-700">
              ID: {currentProfile.id}
            </span>
            <button
              onClick={() => setShowCreateForm(true)}
              className="text-xs px-3 py-1.5 rounded-lg bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 transition-colors flex items-center gap-1.5"
            >
              Switch / Create
            </button>
          </div>
        ) : (
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="text-xs px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium transition-colors flex items-center gap-1.5 self-start md:self-auto"
          >
            <Plus className="w-3.5 h-3.5" />
            Create Profile
          </button>
        )}
      </div>

      {error && (
        <Alert variant="error" className="mt-3" onDismiss={() => setError(null)}>
          {error}
        </Alert>
      )}

      {!currentProfile && !showCreateForm && (
        <div className="mt-3 p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-xs font-semibold text-amber-900 uppercase tracking-wide mb-1">
                Candidate Profile Required
              </h4>
              <p className="text-xs text-amber-800 mb-3">
                No Candidate Profile is currently active. Connect to an existing profile or create one before uploading a resume.
              </p>
              
              <div className="flex flex-wrap gap-2 mb-3">
                <button
                  type="button"
                  onClick={handleAutoConnect}
                  disabled={loading}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition-colors disabled:opacity-50 flex items-center gap-1.5"
                >
                  <Zap className="w-3.5 h-3.5" />
                  Auto-Connect / Default Profile
                </button>
              </div>

              <form onSubmit={handleFetchProfile} className="flex flex-col sm:flex-row gap-2">
                <div className="relative flex-1">
                  <Key className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    value={profileIdInput}
                    onChange={(e) => setProfileIdInput(e.target.value)}
                    placeholder="Enter Candidate Profile UUID..."
                    className="w-full pl-9 pr-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500 font-mono"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-3.5 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-900 text-white transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5"
                >
                  {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : 'Load Profile'}
                </button>
              </form>
            </div>
          </div>
        </div>
      )}

      {showCreateForm && (
        <form onSubmit={handleExplicitCreateProfile} className="mt-3 p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-3">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <h4 className="text-xs font-semibold text-slate-800 uppercase tracking-wide">
              Create Candidate Profile
            </h4>
            <button
              type="button"
              onClick={() => setShowCreateForm(false)}
              className="text-xs text-slate-500 hover:text-slate-800"
            >
              Cancel
            </button>
          </div>
          <div>
            <label className="block text-xs text-slate-700 mb-1 font-medium">User ID (UUID) *</label>
            <input
              type="text"
              required
              value={newUserId}
              onChange={(e) => setNewUserId(e.target.value)}
              placeholder="e.g. 123e4567-e89b-12d3-a456-426614174000"
              className="w-full px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 font-mono placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-700 mb-1 font-medium">Initial Headline (Optional)</label>
            <input
              type="text"
              value={newHeadline}
              onChange={(e) => setNewHeadline(e.target.value)}
              placeholder="e.g. Senior Full Stack Engineer"
              className="w-full px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-700 mb-1 font-medium">Initial Summary (Optional)</label>
            <textarea
              value={newSummary}
              onChange={(e) => setNewSummary(e.target.value)}
              placeholder="Brief candidate bio..."
              rows={2}
              className="w-full px-3 py-1.5 text-xs bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-1.5 text-xs font-medium rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition-colors disabled:opacity-50 flex items-center gap-1.5"
            >
              {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : 'Create Profile'}
            </button>
          </div>
        </form>
      )}
    </Card>
  );
};
