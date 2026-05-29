"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, RefreshCw, HardHat, Shirt, Users, AlertTriangle } from "lucide-react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { VideoPlayer } from "@/components/ui/VideoPlayer";
import { IncidentCard } from "@/components/ui/IncidentCard";
import { StatCard } from "@/components/ui/StatCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { api } from "@/lib/api";
import type { VideoSummary, Incident } from "@/lib/types";
import { format } from "date-fns";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SCREENSHOT_BASE = `${BASE_URL}/violation_frames`;
const POLL_INTERVAL_MS = 5000;

interface Props {
  params: { id: string };
}

export default function VideoDetailPage({ params }: Props) {
  const videoId = Number(params.id);
  const router = useRouter();

  const [summary, setSummary] = useState<VideoSummary | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = async () => {
    try {
      setError(null);
      const [summaryRes, incidentsRes] = await Promise.all([
        api.getVideoSummary(videoId),
        api.getVideoIncidents(videoId),
      ]);
      setSummary(summaryRes.data);
      setIncidents(incidentsRes.data as Incident[]);
    } catch {
      setError("Failed to load video. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [videoId]);

  // Poll while processing
  useEffect(() => {
    if (!summary) return;
    if (summary.video.status === "processing" || summary.video.status === "uploaded") {
      pollRef.current = setTimeout(() => load(), POLL_INTERVAL_MS);
    }
    return () => {
      if (pollRef.current) clearTimeout(pollRef.current);
    };
  }, [summary]);

  const isProcessing =
    summary?.video.status === "processing" || summary?.video.status === "uploaded";

  return (
    <DashboardShell title={summary?.video.filename ?? "Video Detail"}>
      <div className="space-y-6">
        {/* Back + header */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/videos")}
            className="flex items-center gap-1.5 text-slate-400 hover:text-slate-200 text-sm transition-colors"
          >
            <ArrowLeft size={16} />
            All videos
          </button>
          {summary && <StatusBadge value={summary.video.status} />}
          {isProcessing && (
            <span className="flex items-center gap-1.5 text-amber-400 text-xs animate-pulse">
              <RefreshCw size={12} className="animate-spin" />
              Processing…
            </span>
          )}
        </div>

        {loading && <LoadingState message="Loading video details..." />}
        {error && <ErrorState message={error} onRetry={load} />}

        {!loading && !error && summary && (
          <>
            {/* Metadata bar */}
            <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-4 flex flex-wrap gap-4 text-sm">
              <div>
                <span className="text-slate-500">Filename</span>
                <p className="text-slate-200 font-medium mt-0.5">{summary.video.filename}</p>
              </div>
              {summary.video.duration_seconds !== null && (
                <div>
                  <span className="text-slate-500">Duration</span>
                  <p className="text-slate-200 mt-0.5">
                    {Math.floor(summary.video.duration_seconds / 60)}m{" "}
                    {Math.floor(summary.video.duration_seconds % 60)}s
                  </p>
                </div>
              )}
              {summary.video.fps !== null && (
                <div>
                  <span className="text-slate-500">FPS</span>
                  <p className="text-slate-200 mt-0.5">{summary.video.fps.toFixed(1)}</p>
                </div>
              )}
              {summary.video.total_frames !== null && (
                <div>
                  <span className="text-slate-500">Frames</span>
                  <p className="text-slate-200 mt-0.5">{summary.video.total_frames.toLocaleString()}</p>
                </div>
              )}
              <div>
                <span className="text-slate-500">Uploaded</span>
                <p className="text-slate-200 mt-0.5">
                  {format(new Date(summary.video.created_at), "MMM d, yyyy HH:mm")}
                </p>
              </div>
            </div>

            {/* Video player */}
            {summary.video.status === "completed" && summary.video.output_path ? (
              <VideoPlayer
                src={api.annotatedVideoUrl(summary.video.output_path)}
                downloadUrl={api.downloadAnnotatedVideo(videoId)}
                filename={`annotated_${summary.video.filename}`}
              />
            ) : isProcessing ? (
              <div className="flex flex-col items-center justify-center bg-[#1e293b] border border-[#334155] rounded-xl aspect-video gap-3">
                <RefreshCw size={28} className="text-amber-400 animate-spin" />
                <p className="text-slate-400 text-sm">Video is being processed…</p>
                <p className="text-slate-500 text-xs">This page updates automatically.</p>
              </div>
            ) : summary.video.status === "failed" ? (
              <div className="flex flex-col items-center justify-center bg-[#1e293b] border border-red-500/30 rounded-xl aspect-video gap-3">
                <AlertTriangle size={28} className="text-red-400" />
                <p className="text-slate-400 text-sm">Processing failed.</p>
              </div>
            ) : null}

            {/* Stats */}
            {summary.video.status === "completed" && (
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
                <StatCard title="Workers Detected" value={summary.total_workers} subtitle="Unique tracked workers" icon={Users} accent="blue" />
                <StatCard title="Total Incidents" value={summary.total_incidents} subtitle="PPE violations" icon={AlertTriangle} accent="yellow" />
                <StatCard
                  title="Helmet Compliance"
                  value={`${summary.helmet_compliance_pct}%`}
                  subtitle="Workers with hard hats"
                  icon={HardHat}
                  accent={summary.helmet_compliance_pct >= 80 ? "green" : summary.helmet_compliance_pct >= 60 ? "yellow" : "red"}
                />
                <StatCard
                  title="Vest Compliance"
                  value={`${summary.vest_compliance_pct}%`}
                  subtitle="Workers with safety vests"
                  icon={Shirt}
                  accent={summary.vest_compliance_pct >= 80 ? "green" : summary.vest_compliance_pct >= 60 ? "yellow" : "red"}
                />
              </div>
            )}

            {/* Incidents */}
            {incidents.length > 0 && (
              <div>
                <h2 className="text-slate-200 font-semibold mb-3">
                  Incidents ({incidents.length})
                </h2>
                <div className="space-y-3">
                  {incidents.map((incident) => (
                    <IncidentCard key={incident.id} incident={incident} screenshotBase={SCREENSHOT_BASE} />
                  ))}
                </div>
              </div>
            )}

            {summary.video.status === "completed" && incidents.length === 0 && (
              <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-6 text-center">
                <p className="text-emerald-300 font-medium">No violations detected</p>
                <p className="text-slate-400 text-sm mt-1">All workers wore proper PPE throughout the video.</p>
              </div>
            )}
          </>
        )}
      </div>
    </DashboardShell>
  );
}
