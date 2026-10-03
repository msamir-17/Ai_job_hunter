import React, { useState } from 'react';
import { X, FileText, CheckCircle2, Copy, Check } from 'lucide-react';
import { GeneratedDocumentResponse } from '../../types/application';

interface DocumentPreviewModalProps {
  documents: GeneratedDocumentResponse[];
  jobTitle?: string | null;
  companyName?: string | null;
  isOpen: boolean;
  onClose: () => void;
}

export const DocumentPreviewModal: React.FC<DocumentPreviewModalProps> = ({
  documents,
  jobTitle,
  companyName,
  isOpen,
  onClose,
}) => {
  const [selectedIdx, setSelectedIdx] = useState<number>(0);
  const [copied, setCopied] = useState<boolean>(false);

  if (!isOpen) return null;

  const currentDoc = documents[selectedIdx] || null;

  const handleCopy = () => {
    if (!currentDoc) return;
    navigator.clipboard.writeText(currentDoc.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in overflow-y-auto">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl my-6 flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4 bg-slate-950/70">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-sky-500/10 text-sky-400 rounded-lg border border-sky-500/20">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight">
                Attached Application Documents
              </h2>
              <p className="text-xs text-slate-400">
                {jobTitle} • {companyName}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Document Selection Tabs */}
        {documents.length > 0 && (
          <div className="px-6 py-3 bg-slate-950/40 border-b border-slate-800 flex items-center gap-2 overflow-x-auto">
            {documents.map((doc, idx) => (
              <button
                key={doc.id}
                onClick={() => setSelectedIdx(idx)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap ${
                  selectedIdx === idx
                    ? 'bg-sky-600 text-white shadow'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                <span>{doc.doc_type.replace('_', ' ').toUpperCase()}</span>
                {doc.is_approved_by_user && (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-300" />
                )}
              </button>
            ))}
          </div>
        )}

        {/* Content Body */}
        <div className="p-6 overflow-y-auto flex-1">
          {currentDoc ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">
                  Version {currentDoc.version} • {currentDoc.is_approved_by_user ? (
                    <span className="text-emerald-400 font-medium">Candidate Approved ✓</span>
                  ) : (
                    <span className="text-amber-400 font-medium">Draft (Pending Approval)</span>
                  )}
                </span>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1.5 px-3 py-1 bg-slate-800 hover:bg-slate-700 rounded text-xs text-slate-300 border border-slate-700 transition-colors"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5 text-slate-400" />
                      Copy Content
                    </>
                  )}
                </button>
              </div>

              <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs font-mono text-slate-200 whitespace-pre-wrap leading-relaxed">
                {currentDoc.content}
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-slate-500 text-xs italic">
              No tailored documents attached to this application yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
