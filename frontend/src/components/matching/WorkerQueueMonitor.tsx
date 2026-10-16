import React, { useState, useEffect } from 'react';
import { Activity, Cpu, Layers, RefreshCw, Play, CheckCircle2, AlertCircle, ShieldAlert } from 'lucide-react';
import { getWorkerStatus, triggerWorkerCycle, WorkerStatusResponse } from '../../api/jobs';

interface WorkerQueueMonitorProps {
  onCycleTriggered?: () => void;
}

export const WorkerQueueMonitor: React.FC<WorkerQueueMonitorProps> = ({ onCycleTriggered }) => {
  const [statusData, setStatusData] = useState<WorkerStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isTriggering, setIsTriggering] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  const fetchStatus = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await getWorkerStatus();
      setStatusData(data);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to fetch worker status');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleTriggerCycle = async () => {
    setIsTriggering(true);
    setSuccessBanner(null);
    setErrorMessage(null);
    try {
      const updated = await triggerWorkerCycle(15, 'manual');
      setStatusData(updated);
      setSuccessBanner('Ingestion & worker cycle completed. Pipeline queue updated.');
      if (onCycleTriggered) {
        onCycleTriggered();
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to trigger worker cycle');
    } finally {
      setIsTriggering(false);
    }
  };

  const queue = statusData?.queue_depths || {
    ingested: 0,
    filtered: 0,
    scored: 0,
    tailored: 0,
    notified: 0,
    failed: 0,
    dead_letter: 0,
  };

  const isWorkerActive = (statusData?.active_worker_count || 0) > 0;
  const activeWorker = statusData?.workers?.[0];

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        {/* Title and Status Badge */}
        <div className="flex items-center space-x-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50 border border-blue-200 text-blue-600">
            <Cpu className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-xs font-semibold text-slate-800 tracking-wide uppercase">
                Worker Daemon & Queue
              </h3>
              {isWorkerActive ? (
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-700 border border-emerald-200">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                  Active ({statusData?.active_worker_count})
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600 border border-slate-200">
                  <span className="h-1.5 w-1.5 rounded-full bg-slate-400" />
                  Standby
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Postgres SKIP LOCKED queue consumer
              {activeWorker ? ` • ${activeWorker.worker_id} (${activeWorker.current_stage || 'ready'})` : ''}
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={fetchStatus}
            disabled={isLoading}
            className="flex items-center space-x-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 transition disabled:opacity-50"
            title="Refresh queue depths"
          >
            <RefreshCw className={`h-3 w-3 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            type="button"
            onClick={handleTriggerCycle}
            disabled={isTriggering}
            className="flex items-center space-x-1.5 rounded-lg bg-blue-600 px-3.5 py-1.5 text-xs font-medium text-white hover:bg-blue-700 transition disabled:opacity-50"
          >
            {isTriggering ? (
              <RefreshCw className="h-3 w-3 animate-spin" />
            ) : (
              <Play className="h-3 w-3" />
            )}
            <span>{isTriggering ? 'Running...' : 'Run Cycle'}</span>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="mt-3 grid grid-cols-2 gap-2.5 sm:grid-cols-4">
        {/* Pending Ingested */}
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Ingested</span>
            <Layers className="h-3.5 w-3.5 text-slate-400" />
          </div>
          <div className="mt-1 text-lg font-bold text-slate-800">{queue.ingested || 0}</div>
          <div className="text-[10px] text-slate-400">Pending pipeline</div>
        </div>

        {/* Filtered */}
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Filtered</span>
            <Activity className="h-3.5 w-3.5 text-slate-400" />
          </div>
          <div className="mt-1 text-lg font-bold text-slate-800">{queue.filtered || 0}</div>
          <div className="text-[10px] text-slate-400">Passed deterministic rules</div>
        </div>

        {/* Scored & Ready */}
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Scored & Ready</span>
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
          </div>
          <div className="mt-1 text-lg font-bold text-emerald-700">{queue.scored || 0}</div>
          <div className="text-[10px] text-slate-400">Similarity evaluated</div>
        </div>

        {/* DLQ / Retries */}
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Dead-Letter / Failed</span>
            <ShieldAlert className="h-3.5 w-3.5 text-red-500" />
          </div>
          <div className="mt-1 text-lg font-bold text-red-600">
            {(queue.dead_letter || 0) + (queue.failed || 0)}
          </div>
          <div className="text-[10px] text-slate-400">Errors encountered</div>
        </div>
      </div>

      {/* Notifications */}
      {successBanner && (
        <div className="mt-2.5 flex items-center justify-between rounded-lg bg-emerald-50 border border-emerald-200 px-3 py-1.5 text-xs text-emerald-800">
          <span>{successBanner}</span>
          <button
            type="button"
            onClick={() => setSuccessBanner(null)}
            className="text-emerald-600 hover:text-emerald-800"
          >
            Dismiss
          </button>
        </div>
      )}

      {errorMessage && (
        <div className="mt-2.5 flex items-center justify-between rounded-lg bg-red-50 border border-red-200 px-3 py-1.5 text-xs text-red-700">
          <div className="flex items-center space-x-1.5">
            <AlertCircle className="h-3.5 w-3.5" />
            <span>{errorMessage}</span>
          </div>
          <button
            type="button"
            onClick={() => setErrorMessage(null)}
            className="text-red-600 hover:text-red-800"
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
};
