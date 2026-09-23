import React, { useState } from 'react';
import { User, Key, Plus, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { CandidateProfileResponse } from '../../types/candidateProfile';
import { getCandidateProfile, createCandidateProfile } from '../../api/candidateProfile';
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
    <Card className="mb-8 border-sky-500/20 bg-slate-900/80">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-sky-500/10 text-sky-400 rounded-lg border border-sky-500/20">
            <User className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              Candidate Profile Context
              {currentProfile && (
                <span className="inline-flex items-center gap-1 text-xs text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20 font-mono">
                  <CheckCircle className="w-3 h-3" /> Active
                </span>
              )}
            </h3>
            <p className="text-xs text-slate-400">
              Select or specify an existing Candidate Profile before uploading a resume
            </p>
          </div>
        </div>

        {currentProfile ? (
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 text-slate-300">
              Profile ID: {currentProfile.id}
            </span>
            <button
              onClick={() => setShowCreateForm(true)}
              className="text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors flex items-center gap-1.5"
            >
              Switch / Create
            </button>
          </div>
        ) : (
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="text-xs px-3 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-medium transition-colors flex items-center gap-1.5 self-start md:self-auto"
          >
            <Plus className="w-3.5 h-3.5" />
            Create Candidate Profile
          </button>
        )}
      </div>

      {error && (
        <Alert variant="error" className="mt-4" onDismiss={() => setError(null)}>
          {error}
        </Alert>
      )}

      {!currentProfile && !showCreateForm && (
        <div className="mt-4 p-4 bg-amber-950/20 border border-amber-800/40 rounded-xl">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-xs font-semibold text-amber-300 uppercase tracking-wider mb-1">
                Candidate Profile Required
              </h4>
              <p className="text-xs text-amber-200/80 mb-3">
                No Candidate Profile is currently active. You must connect to an existing candidate profile or explicitly create one before triggering resume extraction.
              </p>
              
              <form onSubmit={handleFetchProfile} className="flex flex-col sm:flex-row gap-2">
                <div className="relative flex-1">
                  <Key className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                  <input
                    type="text"
                    value={profileIdInput}
                    onChange={(e) => setProfileIdInput(e.target.value)}
                    placeholder="Enter existing Candidate Profile UUID..."
                    className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-950 border border-slate-800 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 font-mono"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-sky-600 hover:bg-sky-500 text-white transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5"
                >
                  {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : 'Load Profile'}
                </button>
              </form>
            </div>
          </div>
        </div>
      )}

      {showCreateForm && (
        <form onSubmit={handleExplicitCreateProfile} className="mt-4 p-4 bg-slate-950/80 border border-slate-800 rounded-xl space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
              Explicit Candidate Profile Creation
            </h4>
            <button
              type="button"
              onClick={() => setShowCreateForm(false)}
              className="text-xs text-slate-500 hover:text-slate-300"
            >
              Cancel
            </button>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1 font-medium">User ID (UUID) *</label>
            <input
              type="text"
              required
              value={newUserId}
              onChange={(e) => setNewUserId(e.target.value)}
              placeholder="e.g. 123e4567-e89b-12d3-a456-426614174000"
              className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-800 rounded-lg text-white font-mono placeholder-slate-600 focus:outline-none focus:border-sky-500"
            />
            <p className="text-[10px] text-slate-500 mt-1">Must correspond to an existing User record in the database.</p>
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1 font-medium">Initial Headline (Optional)</label>
            <input
              type="text"
              value={newHeadline}
              onChange={(e) => setNewHeadline(e.target.value)}
              placeholder="e.g. Senior Full Stack Engineer"
              className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-sky-500"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1 font-medium">Initial Summary (Optional)</label>
            <textarea
              value={newSummary}
              onChange={(e) => setNewSummary(e.target.value)}
              placeholder="Brief candidate bio..."
              rows={2}
              className="w-full px-3 py-1.5 text-xs bg-slate-900 border border-slate-800 rounded-lg text-white placeholder-slate-600 focus:outline-none focus:border-sky-500"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-1.5 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition-colors disabled:opacity-50 flex items-center gap-1.5"
            >
              {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : 'Create Candidate Profile'}
            </button>
          </div>
        </form>
      )}
    </Card>
  );
};
