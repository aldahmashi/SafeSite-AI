"use client";

import { useState, useEffect, useRef } from "react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { api } from "@/lib/api";
import type { Stream } from "@/lib/types";
import { Plus, Radio, Square, Trash2, AlertTriangle, Wifi, WifiOff } from "lucide-react";

const POLL_MS = 4000;

export default function StreamsPage() {
  const [streams, setStreams] = useState<Stream[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [url, setUrl] = useState("");
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = async () => {
    try {
      const res = await api.listStreams();
      setStreams(res.data);
      setError(null);
    } catch {
      setError("Could not reach backend. Is it running?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const schedule = () => {
      pollRef.current = setTimeout(async () => {
        await load();
        schedule();
      }, POLL_MS);
    };
    schedule();
    return () => {
      if (pollRef.current) clearTimeout(pollRef.current);
    };
  }, []);

  const handleStart = async () => {
    if (!url.trim()) {
      setFormError("Stream URL or webcam index is required.");
      return;
    }
    setSubmitting(true);
    setFormError(null);
    try {
      await api.startStream(url.trim(), name.trim() || undefined);
      setUrl("");
      setName("");
      setShowForm(false);
      await load();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setFormError(err?.response?.data?.detail ?? "Failed to start stream.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleStop = async (streamId: string) => {
    try {
      await api.stopStream(streamId);
      await load();
    } catch {
      // silent — UI will reflect next poll
    }
  };

  const handleDelete = async (streamId: string) => {
    try {
      await api.deleteStream(streamId);
      await load();
    } catch {
      // silent
    }
  };

  const running = streams.filter((s) => s.status === "running").length;

  return (
    <DashboardShell title="Live Streams">
      <div className="space-y-6">
        {/* Header row */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-slate-400 text-sm mt-1">
              Monitor live CCTV / RTSP streams for PPE violations in real time.
            </p>
            {running > 0 && (
              <p className="text-emerald-400 text-xs mt-1 flex items-center gap-1.5">
                <Radio size={11} className="animate-pulse" />
                {running} stream{running > 1 ? "s" : ""} active
              </p>
            )}
          </div>
          <button
            onClick={() => setShowForm((v) => !v)}
            className="flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-400 text-black font-semibold text-sm rounded-lg transition-colors"
          >
            <Plus size={15} />
            Add Stream
          </button>
        </div>

        {/* Add stream form */}
        {showForm && (
          <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-5 space-y-4">
            <h3 className="text-slate-200 font-semibold text-sm">New Stream</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-slate-400 text-xs block mb-1">
                  Stream URL / Webcam Index
                </label>
                <input
                  className="w-full bg-[#0f172a] border border-[#334155] rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-amber-500 placeholder:text-slate-600"
                  placeholder="rtsp://camera.ip:554/stream  or  0"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleStart()}
                />
              </div>
              <div>
                <label className="text-slate-400 text-xs block mb-1">
                  Name (optional)
                </label>
                <input
                  className="w-full bg-[#0f172a] border border-[#334155] rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-amber-500 placeholder:text-slate-600"
                  placeholder="Site Camera A"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleStart()}
                />
              </div>
            </div>
            {formError && <p className="text-red-400 text-xs">{formError}</p>}
            <div className="flex gap-3">
              <button
                onClick={handleStart}
                disabled={submitting}
                className="px-4 py-2 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-black font-semibold text-sm rounded-lg transition-colors"
              >
                {submitting ? "Starting…" : "Start Stream"}
              </button>
              <button
                onClick={() => { setShowForm(false); setFormError(null); }}
                className="px-4 py-2 border border-[#334155] text-slate-400 hover:text-slate-200 text-sm rounded-lg transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {loading && <LoadingState message="Loading streams…" />}
        {error && <ErrorState message={error} onRetry={load} />}

        {!loading && !error && streams.length === 0 && (
          <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-12 text-center">
            <Wifi size={32} className="text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 font-medium">No streams configured</p>
            <p className="text-slate-500 text-sm mt-1">
              Click &quot;Add Stream&quot; to start monitoring a live CCTV or RTSP feed.
            </p>
          </div>
        )}

        {!loading && !error && streams.length > 0 && (
          <div className="space-y-3">
            {streams.map((stream) => (
              <StreamRow
                key={stream.stream_id}
                stream={stream}
                onStop={() => handleStop(stream.stream_id)}
                onDelete={() => handleDelete(stream.stream_id)}
              />
            ))}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}

function StreamRow({
  stream,
  onStop,
  onDelete,
}: {
  stream: Stream;
  onStop: () => void;
  onDelete: () => void;
}) {
  const isRunning = stream.status === "running";
  const isFailed = stream.status === "error";

  return (
    <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-4 flex flex-wrap items-center gap-4">
      {/* Status icon */}
      <div
        className={`p-2 rounded-lg ${
          isRunning
            ? "bg-emerald-500/10"
            : isFailed
            ? "bg-red-500/10"
            : "bg-slate-700/40"
        }`}
      >
        {isRunning ? (
          <Radio size={18} className="text-emerald-400 animate-pulse" />
        ) : isFailed ? (
          <AlertTriangle size={18} className="text-red-400" />
        ) : (
          <WifiOff size={18} className="text-slate-500" />
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <p className="text-slate-200 font-medium text-sm truncate">{stream.name}</p>
        <p className="text-slate-500 text-xs truncate">{stream.url}</p>
        {stream.error_message && (
          <p className="text-red-400 text-xs mt-0.5 truncate">{stream.error_message}</p>
        )}
      </div>

      {/* Stats */}
      <div className="flex items-center gap-6 text-sm">
        <div className="text-center">
          <p className="text-slate-500 text-xs">Status</p>
          <span
            className={`text-xs font-semibold ${
              isRunning
                ? "text-emerald-400"
                : isFailed
                ? "text-red-400"
                : "text-slate-400"
            }`}
          >
            {stream.status.toUpperCase()}
          </span>
        </div>
        <div className="text-center">
          <p className="text-slate-500 text-xs">Incidents</p>
          <p className="text-amber-400 font-bold">{stream.incident_count}</p>
        </div>
        {stream.started_at && (
          <div className="text-center hidden sm:block">
            <p className="text-slate-500 text-xs">Started</p>
            <p className="text-slate-400 text-xs">
              {new Date(stream.started_at).toLocaleTimeString()}
            </p>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        {isRunning && (
          <button
            onClick={onStop}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 text-xs font-medium rounded-lg transition-colors"
          >
            <Square size={12} />
            Stop
          </button>
        )}
        <button
          onClick={onDelete}
          title="Delete stream"
          className="p-1.5 text-slate-500 hover:text-red-400 transition-colors rounded"
        >
          <Trash2 size={15} />
        </button>
      </div>
    </div>
  );
}
