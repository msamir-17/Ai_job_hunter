import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, X, AlertCircle, RefreshCw } from 'lucide-react';
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

  const handleDragLeave = () => {
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
    if (!selectedFile) return;
    await onUploadAndExtract(selectedFile);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <Card className="mb-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-blue-50 text-blue-600 rounded-lg border border-blue-200">
          <UploadCloud className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-slate-900">Upload Resume</h3>
          <p className="text-xs text-slate-500">
            Upload your resume (.pdf or .docx) to extract facts into a draft
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
                ? 'border-slate-200 bg-slate-50 opacity-60 cursor-not-allowed'
                : dragOver
                ? 'border-blue-500 bg-blue-50/50'
                : 'border-slate-200 bg-slate-50 hover:border-slate-300 hover:bg-slate-100/50'
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
            <UploadCloud className="w-8 h-8 text-slate-400 mx-auto mb-2" />
            <h4 className="text-xs font-semibold text-slate-800 mb-0.5">
              Drag and drop your resume, or <span className="text-blue-600 underline">Browse files</span>
            </h4>
            <p className="text-[11px] text-slate-500">
              PDF or DOCX • Max size 5 MB
            </p>
            {!candidateProfileId && (
              <p className="text-xs text-amber-700 font-medium mt-2 flex items-center justify-center gap-1">
                <AlertCircle className="w-3.5 h-3.5" /> Select a candidate profile above to enable upload
              </p>
            )}
          </div>
        ) : (
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3 overflow-hidden">
                <div className="p-2.5 bg-blue-50 text-blue-600 rounded-lg border border-blue-200 shrink-0">
                  <FileText className="w-5 h-5" />
                </div>
                <div className="min-w-0">
                  <h4 className="text-xs font-semibold text-slate-900 truncate">{selectedFile.name}</h4>
                  <div className="flex items-center gap-2 text-[11px] text-slate-500 mt-0.5">
                    <span>Size: {formatFileSize(selectedFile.size)}</span>
                    <span>•</span>
                    <span className="uppercase text-slate-600 font-mono">
                      {selectedFile.name.split('.').pop()}
                    </span>
                  </div>
                </div>
              </div>

              <button
                type="button"
                onClick={handleRemoveFile}
                disabled={isUploading}
                className="p-1 rounded text-slate-400 hover:text-red-600 hover:bg-white transition-colors disabled:opacity-50"
                title="Remove file"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="mt-3 pt-3 border-t border-slate-200 flex items-center justify-between">
              <p className="text-[11px] text-slate-500">
                Ready to extract structured candidate facts
              </p>
              <button
                type="submit"
                disabled={!candidateProfileId || isUploading}
                className="px-4 py-1.5 text-xs font-medium rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors disabled:opacity-50 flex items-center gap-1.5"
              >
                {isUploading ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Extracting...</span>
                  </>
                ) : (
                  <span>Upload & Extract</span>
                )}
              </button>
            </div>
          </div>
        )}
      </form>
    </Card>
  );
};
