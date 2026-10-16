import React, { useState, useEffect } from 'react';
import {
  RotateCw,
  ShieldCheck,
} from 'lucide-react';
import { ApplicationResponse, ApplicationStatus } from '../types/application';
import { CandidateProfileResponse } from '../types/candidateProfile';
import { listCandidateProfiles } from '../api/candidateProfile';
import {
  listApplications,
  updateApplicationStatus,
  deleteApplication,
} from '../api/applications';
import { KanbanCard } from '../components/applications/KanbanCard';
import { DocumentPreviewModal } from '../components/applications/DocumentPreviewModal';

interface ColumnDef {
  status: ApplicationStatus;
  title: string;
  badgeBg: string;
}

const COLUMNS: ColumnDef[] = [
  {
    status: 'saved',
    title: 'Saved',
    badgeBg: 'bg-slate-200 text-slate-700',
  },
  {
    status: 'applied',
    title: 'Applied',
    badgeBg: 'bg-blue-100 text-blue-800',
  },
  {
    status: 'interviewing',
    title: 'Interviewing',
    badgeBg: 'bg-indigo-100 text-indigo-800',
  },
  {
    status: 'offer',
    title: 'Offer',
    badgeBg: 'bg-emerald-100 text-emerald-800',
  },
  {
    status: 'rejected',
    title: 'Archived / Rejected',
    badgeBg: 'bg-slate-200 text-slate-600',
  },
];

export const ApplicationsKanbanPage: React.FC = () => {
  const [profile, setProfile] = useState<CandidateProfileResponse | null>(null);
  const [applications, setApplications] = useState<ApplicationResponse[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Document preview modal state
  const [previewApp, setPreviewApp] = useState<ApplicationResponse | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState<boolean>(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const profiles = await listCandidateProfiles(1);
      const p = profiles.length > 0 ? profiles[0] : null;
      setProfile(p);
      const apps = await listApplications(p ? p.user_id : undefined);
      setApplications(apps);
    } catch (err: any) {
      setError(err.message || 'Failed to load applications.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStatusChange = async (appId: string, newStatus: ApplicationStatus) => {
    try {
      // Optimistic update
      setApplications((prev) =>
        prev.map((app) => (app.id === appId ? { ...app, status: newStatus } : app))
      );

      const updated = await updateApplicationStatus(appId, newStatus);
      setApplications((prev) =>
        prev.map((app) => (app.id === appId ? updated : app))
      );
    } catch (err: any) {
      console.error('Failed to update status:', err);
    }
  };

  const handleDelete = async (appId: string) => {
    try {
      await deleteApplication(appId);
      setApplications((prev) => prev.filter((app) => app.id !== appId));
    } catch (err: any) {
      console.error('Failed to delete application:', err);
    }
  };

  const handleOpenPreview = (app: ApplicationResponse) => {
    setPreviewApp(app);
    setIsPreviewOpen(true);
  };

  // Stats calculation
  const totalCount = applications.length;
  const appliedCount = applications.filter((a) => a.status === 'applied').length;
  const interviewingCount = applications.filter((a) => a.status === 'interviewing').length;
  const offerCount = applications.filter((a) => a.status === 'offer').length;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900">
            Applications
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Track job applications through pipeline stages.
            {profile && profile.headline && (
              <span className="text-slate-700 font-medium ml-1">
                • {profile.headline}
              </span>
            )}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition-colors disabled:opacity-50"
          >
            <RotateCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Pipeline Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
          <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block">
            Total Pipeline
          </span>
          <span className="text-2xl font-bold text-slate-900 mt-1 block">{totalCount}</span>
        </div>
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
          <span className="text-[11px] font-medium text-blue-600 uppercase tracking-wider block">
            Applied
          </span>
          <span className="text-2xl font-bold text-slate-900 mt-1 block">{appliedCount}</span>
        </div>
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
          <span className="text-[11px] font-medium text-indigo-600 uppercase tracking-wider block">
            Interviewing
          </span>
          <span className="text-2xl font-bold text-slate-900 mt-1 block">
            {interviewingCount}
          </span>
        </div>
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
          <span className="text-[11px] font-medium text-emerald-600 uppercase tracking-wider block">
            Offers
          </span>
          <span className="text-2xl font-bold text-slate-900 mt-1 block">{offerCount}</span>
        </div>
      </div>

      {/* Human-in-the-Loop Safeguard Notice */}
      <div className="p-3 bg-white border border-slate-200 rounded-lg flex items-center justify-between text-xs text-slate-600">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>
            <strong>Human-in-the-Loop Verification:</strong> Generated application materials require candidate review. Submissions are initiated by opening the company's portal link.
          </span>
        </div>
      </div>

      {/* Kanban Board Columns */}
      {isLoading ? (
        <div className="py-24 text-center space-y-2">
          <RotateCw className="w-6 h-6 text-slate-400 animate-spin mx-auto" />
          <p className="text-xs text-slate-500">Loading applications...</p>
        </div>
      ) : error ? (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-xs text-red-600">
          {error}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 items-start">
          {COLUMNS.map((col) => {
            const columnApps = applications.filter((app) => app.status === col.status);

            return (
              <div
                key={col.status}
                className="bg-slate-100/70 border border-slate-200 rounded-xl p-3 flex flex-col min-h-[460px]"
              >
                {/* Column Header */}
                <div className="flex items-center justify-between pb-2.5 mb-2.5 border-b border-slate-200">
                  <span className="text-xs font-semibold text-slate-800">
                    {col.title}
                  </span>
                  <span
                    className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${col.badgeBg}`}
                  >
                    {columnApps.length}
                  </span>
                </div>

                {/* Cards Container */}
                <div className="space-y-2.5 flex-1">
                  {columnApps.length === 0 ? (
                    <div className="py-12 text-center text-slate-400 text-xs">
                      No applications
                    </div>
                  ) : (
                    columnApps.map((app) => (
                      <KanbanCard
                        key={app.id}
                        application={app}
                        onStatusChange={handleStatusChange}
                        onDelete={handleDelete}
                        onPreviewDocuments={handleOpenPreview}
                      />
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Document Preview Modal */}
      {previewApp && (
        <DocumentPreviewModal
          documents={previewApp.documents}
          jobTitle={previewApp.job_title}
          companyName={previewApp.job_company}
          isOpen={isPreviewOpen}
          onClose={() => setIsPreviewOpen(false)}
        />
      )}
    </div>
  );
};
