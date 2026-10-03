import React, { useState, useEffect } from 'react';
import {
  Kanban,
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
  color: string;
  badgeBg: string;
}

const COLUMNS: ColumnDef[] = [
  {
    status: 'saved',
    title: 'Saved',
    color: 'border-slate-700',
    badgeBg: 'bg-slate-800 text-slate-300',
  },
  {
    status: 'applied',
    title: 'Applied',
    color: 'border-sky-500/40',
    badgeBg: 'bg-sky-500/20 text-sky-300',
  },
  {
    status: 'interviewing',
    title: 'Interviewing',
    color: 'border-indigo-500/40',
    badgeBg: 'bg-indigo-500/20 text-indigo-300',
  },
  {
    status: 'offer',
    title: 'Offer Received',
    color: 'border-emerald-500/40',
    badgeBg: 'bg-emerald-500/20 text-emerald-300',
  },
  {
    status: 'rejected',
    title: 'Rejected',
    color: 'border-red-500/30',
    badgeBg: 'bg-red-500/20 text-red-400',
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
      // Revert on error
      loadData();
    }
  };

  const handleDelete = async (appId: string) => {
    try {
      setApplications((prev) => prev.filter((app) => app.id !== appId));
      await deleteApplication(appId);
    } catch (err: any) {
      console.error('Failed to delete application:', err);
      loadData();
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
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-sky-500/10 text-sky-400 rounded-lg border border-sky-500/20">
              <Kanban className="w-6 h-6" />
            </div>
            <h1 className="text-2xl font-extrabold tracking-tight text-white">
              Application Pipeline Kanban
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Track job opportunities through your pipeline with attached tailored documents and human-in-the-loop safeguards.
            {profile && profile.headline && (
              <span className="block text-sky-400 font-medium mt-0.5">
                Active Profile: {profile.headline}
              </span>
            )}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-950/30 border border-emerald-500/30 text-xs text-emerald-300">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Human-in-the-Loop Safe Apply</span>
          </div>

          <button
            onClick={loadData}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors disabled:opacity-50"
          >
            <RotateCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Pipeline Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Total Pipeline
          </span>
          <span className="text-2xl font-bold text-white mt-1 block">{totalCount}</span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-[11px] font-semibold text-sky-400 uppercase tracking-wider block">
            Submitted (Applied)
          </span>
          <span className="text-2xl font-bold text-sky-300 mt-1 block">{appliedCount}</span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-[11px] font-semibold text-indigo-400 uppercase tracking-wider block">
            Interviewing
          </span>
          <span className="text-2xl font-bold text-indigo-300 mt-1 block">
            {interviewingCount}
          </span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider block">
            Offers
          </span>
          <span className="text-2xl font-bold text-emerald-300 mt-1 block">{offerCount}</span>
        </div>
      </div>

      {/* Human-in-the-Loop Safeguard Notice */}
      <div className="p-3.5 bg-slate-900/40 border border-slate-800 rounded-xl flex items-center justify-between text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>
            <strong>HITL Policy:</strong> This co-pilot prepares grounded, verified application materials. You review the documents, click the external link to the company's application portal, and submit the application yourself.
          </span>
        </div>
      </div>

      {/* Kanban Board Columns */}
      {isLoading ? (
        <div className="py-24 text-center space-y-3">
          <RotateCw className="w-8 h-8 text-sky-400 animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading Kanban applications...</p>
        </div>
      ) : error ? (
        <div className="p-4 bg-red-950/30 border border-red-800/40 rounded-xl text-xs text-red-300">
          {error}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-start">
          {COLUMNS.map((col) => {
            const columnApps = applications.filter((app) => app.status === col.status);

            return (
              <div
                key={col.status}
                className="bg-slate-950/50 border border-slate-800/90 rounded-2xl p-3 flex flex-col min-h-[500px]"
              >
                {/* Column Header */}
                <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-white tracking-wide">
                      {col.title}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${col.badgeBg}`}
                    >
                      {columnApps.length}
                    </span>
                  </div>
                </div>

                {/* Cards Container */}
                <div className="space-y-3 flex-1">
                  {columnApps.length === 0 ? (
                    <div className="py-12 text-center text-slate-600 text-xs italic">
                      Empty column
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
