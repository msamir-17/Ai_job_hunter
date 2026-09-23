import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, X, AlertCircle, RefreshCw, Sparkles } from 'lucide-react';
import { Card } from '../ui/Card';
import { Alert } from '../ui/Alert';

interface ResumeUploadSectionProps {
  candidateProfileId: string | null;
  onUploadAndExtract: (file: File) => Promise<void>;
  isUploading: boolean;
  error: string | null;
  onErrorClear: () => void;
}

export const ResumeUploadSection: React.FC<ResumeUploadSectionProps> = ({
  candidateProfileId,
  onUploadAndExtract,
  isUploading,
  error,
  onErrorClear,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState<boolean>(false);
  const [clientError, setClientError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const ALLOWED_EXTENSIONS = ['.pdf', '.docx'];
  const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB limit

  const validateFile = (file: File): boolean => {
    setClientError(null);
    onErrorClear();

    const fileName = file.name.toLowerCase();
    const isValidFormat = ALLOWED_EXTENSIONS.some((ext) => fileName.endsWith(ext));
    if (!isValidFormat) {
      setClientError('Invalid file format. Only PDF (.pdf) and Word (.docx) documents are supported.');
      return false;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      setClientError(`File size exceeds 5 MB limit (Selected size: ${(file.size / (1024 * 1024)).toFixed(2)} MB).`);
      return false;
    }

    return true;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
      }
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
      }
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setClientError(null);
    onErrorClear();
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile || !candidateProfileId || isUploading) return;
    await onUploadAndExtract(selectedFile);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <Card className="mb-8">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2.5 bg-indigo-500/10 text-indigo-400 rounded-lg border border-indigo-500/20">
          <UploadCloud className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-base font-semibold text-white">Upload Resume Document</h3>
          <p className="text-xs text-slate-400">
            Upload your resume (.pdf or .docx) to trigger AI extraction into an unverified draft
          </p>
        </div>
      </div>

      {(clientError || error) && (
        <Alert variant="error" className="mb-4" onDismiss={() => { setClientError(null); onErrorClear(); }}>
          {clientError || error}
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        {!selectedFile ? (
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => candidateProfileId && fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${
              !candidateProfileId
                ? 'border-slate-800 bg-slate-950/30 opacity-60 cursor-not-allowed'
                : dragOver
                ? 'border-sky-500 bg-sky-500/10'
                : 'border-slate-800 bg-slate-950/50 hover:border-slate-700 hover:bg-slate-900/50'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              className="hidden"
              disabled={!candidateProfileId || isUploading}
            />
            <UploadCloud className="w-10 h-10 text-slate-500 mx-auto mb-3" />
            <h4 className="text-sm font-medium text-slate-200 mb-1">
              Drag & Drop your resume here, or <span className="text-sky-400 underline">Browse Files</span>
            </h4>
            <p className="text-xs text-slate-500">
              Supported formats: PDF (.pdf) and Word (.docx) • Max size: 5 MB
            </p>
            {!candidateProfileId && (
              <p className="text-xs text-amber-400/90 font-medium mt-3 flex items-center justify-center gap-1">
                <AlertCircle className="w-3.5 h-3.5" /> Select or create a Candidate Profile above to enable upload
              </p>
            )}
          </div>
        ) : (
          <div className="p-4 bg-slate-950/80 border border-slate-800 rounded-xl">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3 overflow-hidden">
                <div className="p-3 bg-sky-500/10 text-sky-400 rounded-lg border border-sky-500/20 shrink-0">
                  <FileText className="w-6 h-6" />
                </div>
                <div className="min-w-0">
                  <h4 className="text-xs font-semibold text-slate-200 truncate">{selectedFile.name}</h4>
                  <div className="flex items-center gap-3 text-[11px] text-slate-400 mt-0.5">
                    <span>Size: {formatFileSize(selectedFile.size)}</span>
                    <span>•</span>
                    <span className="uppercase text-sky-400 font-mono">
                      {selectedFile.name.split('.').pop()}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleRemoveFile}
                  disabled={isUploading}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-900 transition-colors disabled:opacity-50"
                  title="Remove file"
                  aria-label="Remove selected file"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-slate-800/80 flex items-center justify-between">
              <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-sky-400" />
                Ready to extract structured candidate draft JSON
              </p>
              <button
                type="submit"
                disabled={!candidateProfileId || isUploading}
                className="px-5 py-2 text-xs font-semibold rounded-lg bg-sky-600 hover:bg-sky-500 text-white transition-all shadow-md shadow-sky-950 disabled:opacity-50 flex items-center gap-2"
              >
                {isUploading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Uploading & Extracting...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    Upload & Trigger AI Extraction
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </form>
    </Card>
  );
};
