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
    <div className="bg-white border border-slate-200 rounded-lg p-3.5 shadow-sm hover:shadow transition-shadow space-y-2.5 group">
      {/* Title & Company */}
      <div>
        <div className="flex items-start justify-between gap-2">
          <h4 className="text-xs font-semibold text-slate-900 group-hover:text-blue-600 transition-colors line-clamp-1">
            {application.job_title || 'Untitled Role'}
          </h4>
          {confirmDelete ? (
            <div className="flex items-center gap-1">
              <button
                onClick={() => onDelete(application.id)}
                className="text-[10px] px-1.5 py-0.5 bg-red-100 hover:bg-red-200 text-red-700 rounded font-semibold"
              >
                Delete?
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                className="text-[10px] px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded"
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={() => setConfirmDelete(true)}
              className="text-slate-300 hover:text-red-500 p-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
              title="Delete application"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-1.5 text-[11px] text-slate-500 mt-1">
          <span className="flex items-center gap-1 font-medium text-slate-700">
            <Building className="w-3 h-3 text-slate-400" />
            {application.job_company || 'Unknown Company'}
          </span>
          <span>•</span>
          <span className="flex items-center gap-1 text-slate-400">
            <MapPin className="w-3 h-3 text-slate-400" />
            {application.job_location || (application.job_is_remote ? 'Remote' : 'Location N/A')}
          </span>
        </div>
      </div>

      {/* Applied Date */}
      {application.applied_at && (
        <div className="flex items-center gap-1 text-[10px] text-emerald-700 font-mono">
          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
          <span>Applied: {new Date(application.applied_at).toLocaleDateString()}</span>
        </div>
      )}

      {/* Documents attached */}
      <div className="flex items-center justify-between text-xs pt-1.5 border-t border-slate-100">
        <button
          onClick={() => onPreviewDocuments(application)}
          className="flex items-center gap-1 text-[11px] text-blue-600 hover:text-blue-800 transition-colors"
        >
          <FileText className="w-3 h-3" />
          <span>
            {application.documents.length}{' '}
            {application.documents.length === 1 ? 'Doc' : 'Docs'}
          </span>
        </button>

        {application.job_url ? (
          <a
            href={application.job_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-[11px] px-2 py-0.5 rounded bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 transition-colors"
            title="Open external application link"
          >
            <span>Apply ↗</span>
          </a>
        ) : (
          <span className="text-[10px] text-slate-400">No URL</span>
        )}
      </div>

      {/* Column Mover Controls */}
      <div className="flex items-center justify-between pt-1 border-t border-slate-100 text-[10px]">
        {prevStatus ? (
          <button
            onClick={() => onStatusChange(application.id, prevStatus)}
            className="flex items-center gap-0.5 text-slate-400 hover:text-slate-700 px-1 py-0.5 rounded hover:bg-slate-100 transition-colors"
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
            className="flex items-center gap-0.5 text-slate-400 hover:text-slate-700 px-1 py-0.5 rounded hover:bg-slate-100 transition-colors"
          >
            <span className="capitalize">{nextStatus}</span>
            <ChevronRight className="w-3 h-3" />
          </button>
        )}
      </div>
    </div>
  );
};
