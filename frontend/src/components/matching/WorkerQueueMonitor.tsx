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
    // Poll every 15 seconds
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
    <div className="mb-6 rounded-xl border border-slate-700/80 bg-slate-800/80 p-5 shadow-lg backdrop-blur-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        {/* Title and Status Badge */}
        <div className="flex items-center space-x-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
            <Cpu className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-semibold text-white tracking-wide uppercase">
                Worker Daemon & Queue Engine
              </h3>
              {isWorkerActive ? (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400 border border-emerald-500/30">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Daemon Active ({statusData?.active_worker_count})
                </span>
              ) : (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-medium text-amber-400 border border-amber-500/30">
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
                  Daemon Idle / Standby
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              SKIP LOCKED Postgres Consumer with Dead-Letter Retry Safety
              {activeWorker ? ` - ${activeWorker.worker_id} (${activeWorker.current_stage || 'ready'})` : ''}
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={fetchStatus}
            disabled={isLoading}
            className="flex items-center space-x-1.5 rounded-lg border border-slate-600 bg-slate-700/60 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700 hover:text-white transition disabled:opacity-50"
            title="Refresh queue depths"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            type="button"
            onClick={handleTriggerCycle}
            disabled={isTriggering}
            className="flex items-center space-x-1.5 rounded-lg bg-indigo-600 px-3.5 py-1.5 text-xs font-medium text-white hover:bg-indigo-500 transition shadow-sm disabled:opacity-50"
          >
            {isTriggering ? (
              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Play className="h-3.5 w-3.5" />
            )}
            <span>{isTriggering ? 'Running Cycle...' : 'Trigger Ingest & Drain'}</span>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {/* Pending Ingested */}
        <div className="rounded-lg border border-slate-700/60 bg-slate-900/40 p-3">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Queued (Ingested)</span>
            <Layers className="h-3.5 w-3.5 text-amber-400" />
          </div>
          <div className="mt-1 text-xl font-bold text-slate-100">{queue.ingested || 0}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Pending stage transitions</div>
        </div>

        {/* Filtered */}
        <div className="rounded-lg border border-slate-700/60 bg-slate-900/40 p-3">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Deterministic Filter</span>
            <Activity className="h-3.5 w-3.5 text-cyan-400" />
          </div>
          <div className="mt-1 text-xl font-bold text-slate-100">{queue.filtered || 0}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Passed zero-cost rules</div>
        </div>

        {/* Scored & Ready */}
        <div className="rounded-lg border border-slate-700/60 bg-slate-900/40 p-3">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Scored & Ready</span>
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
          </div>
          <div className="mt-1 text-xl font-bold text-emerald-400">{queue.scored || 0}</div>
          <div className="text-[10px] text-slate-500 mt-0.5">Hybrid vectors evaluated</div>
        </div>

        {/* DLQ / Retries */}
        <div className="rounded-lg border border-slate-700/60 bg-slate-900/40 p-3">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Dead-Letter / Failed</span>
            <ShieldAlert className="h-3.5 w-3.5 text-rose-400" />
          </div>
          <div className="mt-1 text-xl font-bold text-rose-400">
            {(queue.dead_letter || 0) + (queue.failed || 0)}
          </div>
          <div className="text-[10px] text-slate-500 mt-0.5">Max retries exceeded</div>
        </div>
      </div>

      {/* Notifications */}
      {successBanner && (
        <div className="mt-3 flex items-center justify-between rounded-lg bg-emerald-500/10 border border-emerald-500/30 px-3 py-2 text-xs text-emerald-300">
          <span>{successBanner}</span>
          <button
            type="button"
            onClick={() => setSuccessBanner(null)}
            className="text-emerald-400 hover:text-emerald-200"
          >
            Dismiss
          </button>
        </div>
      )}

      {errorMessage && (
        <div className="mt-3 flex items-center justify-between rounded-lg bg-rose-500/10 border border-rose-500/30 px-3 py-2 text-xs text-rose-300">
          <div className="flex items-center space-x-1.5">
            <AlertCircle className="h-4 w-4" />
            <span>{errorMessage}</span>
          </div>
          <button
            type="button"
            onClick={() => setErrorMessage(null)}
            className="text-rose-400 hover:text-rose-200"
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
};
