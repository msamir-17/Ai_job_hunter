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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm overflow-y-auto">
      <div className="bg-white border border-slate-200 rounded-xl w-full max-w-3xl overflow-hidden shadow-xl my-6 flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4 bg-white">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-blue-50 text-blue-600 rounded-lg border border-blue-200">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900 tracking-tight">
                Attached Documents
              </h2>
              <p className="text-xs text-slate-500">
                {jobTitle} • {companyName}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Document Selection Tabs */}
        {documents.length > 0 && (
          <div className="px-6 py-2.5 bg-slate-50 border-b border-slate-100 flex items-center gap-2 overflow-x-auto">
            {documents.map((doc, idx) => (
              <button
                key={doc.id}
                onClick={() => setSelectedIdx(idx)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 whitespace-nowrap ${
                  selectedIdx === idx
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
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
                <span className="text-xs text-slate-500">
                  Version {currentDoc.version} • {currentDoc.is_approved_by_user ? (
                    <span className="text-emerald-700 font-medium">Candidate Approved</span>
                  ) : (
                    <span className="text-amber-700 font-medium">Draft (Pending Approval)</span>
                  )}
                </span>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1.5 px-3 py-1 bg-white hover:bg-slate-50 rounded text-xs text-slate-700 border border-slate-200 transition-colors"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5 text-slate-400" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs font-mono text-slate-800 whitespace-pre-wrap leading-relaxed">
                {currentDoc.content}
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-slate-400 text-xs italic">
              No tailored documents attached to this application yet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
