import React, { useState } from 'react';
import {
  FileText,
  Trash2,
  ChevronLeft,
  ChevronRight,
  Building,
  MapPin,
  CheckCircle2,
} from 'lucide-react';
import { ApplicationResponse, ApplicationStatus } from '../../types/application';

interface KanbanCardProps {
  application: ApplicationResponse;
  onStatusChange: (appId: string, newStatus: ApplicationStatus) => void;
  onDelete: (appId: string) => void;
  onPreviewDocuments: (app: ApplicationResponse) => void;
}

const STATUS_ORDER: ApplicationStatus[] = [
  'saved',
  'applied',
  'interviewing',
  'offer',
  'rejected',
];

export const KanbanCard: React.FC<KanbanCardProps> = ({
  application,
  onStatusChange,
  onDelete,
  onPreviewDocuments,
}) => {
  const currentIdx = STATUS_ORDER.indexOf(application.status);
  const prevStatus = currentIdx > 0 ? STATUS_ORDER[currentIdx - 1] : null;
  const nextStatus =
    currentIdx < STATUS_ORDER.length - 1 ? STATUS_ORDER[currentIdx + 1] : null;

  const [confirmDelete, setConfirmDelete] = useState<boolean>(false);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-md hover:border-slate-700 transition-all space-y-3 group">
      {/* Title & Company */}
      <div>
        <div className="flex items-start justify-between gap-2">
          <h4 className="text-sm font-bold text-white tracking-tight group-hover:text-sky-300 transition-colors line-clamp-1">
            {application.job_title || 'Untitled Role'}
          </h4>
          {confirmDelete ? (
            <div className="flex items-center gap-1">
              <button
                onClick={() => onDelete(application.id)}
                className="text-[10px] px-1.5 py-0.5 bg-red-900/50 hover:bg-red-900 text-red-200 rounded font-semibold"
              >
                Delete?
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                className="text-[10px] px-1.5 py-0.5 bg-slate-800 text-slate-400 rounded"
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={() => setConfirmDelete(true)}
              className="text-slate-600 hover:text-red-400 p-1 opacity-0 group-hover:opacity-100 transition-opacity"
              title="Delete application"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-400 mt-1">
          <span className="flex items-center gap-1 font-medium text-slate-300">
            <Building className="w-3 h-3 text-slate-500" />
            {application.job_company || 'Unknown Company'}
          </span>
          <span>•</span>
          <span className="flex items-center gap-1">
            <MapPin className="w-3 h-3 text-slate-500" />
            {application.job_location || (application.job_is_remote ? 'Remote' : 'Location N/A')}
          </span>
        </div>
      </div>

      {/* Applied Date / Timestamp info */}
      {application.applied_at && (
        <div className="flex items-center gap-1.5 text-[11px] text-emerald-400/90 font-mono">
          <CheckCircle2 className="w-3 h-3" />
          <span>Applied: {new Date(application.applied_at).toLocaleDateString()}</span>
        </div>
      )}

      {/* Documents attached */}
      <div className="flex items-center justify-between text-xs pt-1 border-t border-slate-800/80">
        <button
          onClick={() => onPreviewDocuments(application)}
          className="flex items-center gap-1 text-[11px] text-sky-400 hover:text-sky-300 transition-colors"
        >
          <FileText className="w-3 h-3" />
          <span>
            {application.documents.length}{' '}
            {application.documents.length === 1 ? 'Doc' : 'Docs'}
          </span>
        </button>

        {/* Human-in-the-Loop Safeguard: External link button */}
        {application.job_url ? (
          <a
            href={application.job_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-[11px] px-2 py-0.5 rounded bg-sky-500/10 hover:bg-sky-500/20 text-sky-300 border border-sky-500/30 transition-colors group/link"
            title="Human-in-the-Loop Safe: Opens employer portal in a new tab for manual candidate review & submission."
          >
            <span>Apply ↗</span>
          </a>
        ) : (
          <span className="text-[10px] text-slate-600">No URL</span>
        )}
      </div>

      {/* Column Mover Controls */}
      <div className="flex items-center justify-between pt-1 border-t border-slate-800/50 text-[10px]">
        {prevStatus ? (
          <button
            onClick={() => onStatusChange(application.id, prevStatus)}
            className="flex items-center gap-0.5 text-slate-400 hover:text-white px-1.5 py-0.5 rounded hover:bg-slate-800 transition-colors"
          >
            <ChevronLeft className="w-3 h-3" />
            <span className="capitalize">{prevStatus}</span>
          </button>
        ) : (
          <span />
        )}

        {nextStatus && (
          <button
            onClick={() => onStatusChange(application.id, nextStatus)}
            className="flex items-center gap-0.5 text-slate-400 hover:text-white px-1.5 py-0.5 rounded hover:bg-slate-800 transition-colors"
          >
            <span className="capitalize">{nextStatus}</span>
            <ChevronRight className="w-3 h-3" />
          </button>
        )}
      </div>
    </div>
  );
};
