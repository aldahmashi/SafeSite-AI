"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, Filter } from "lucide-react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { IncidentCard } from "@/components/ui/IncidentCard";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { api } from "@/lib/api";
import type { Incident, Video, Stream } from "@/lib/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SCREENSHOT_BASE = `${BASE_URL}/violation_frames`;

const VIOLATION_TYPES = [
  "ALL", "NO_HELMET", "NO_VEST", "HIGH_RISK_ZONE",
  "MACHINERY_PROXIMITY_RISK", "FALL_RISK",
];
const RISK_LEVELS = ["ALL", "LOW", "MEDIUM", "HIGH", "CRITICAL"];

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [videos, setVideos] = useState<Video[]>([]);
  const [streams, setStreams] = useState<Stream[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter state
  const [violationType, setViolationType] = useState("ALL");
  const [riskLevel, setRiskLevel] = useState("ALL");
  const [selectedVideoId, setSelectedVideoId] = useState<string>("");   // "" = all
  const [selectedStreamId, setSelectedStreamId] = useState<string>(""); // "" = all

  // Load dropdown options once
  useEffect(() => {
    api.listVideos(0, 100).then((r) => setVideos(r.data)).catch(() => {});
    api.listStreams().then((r) => setStreams(r.data)).catch(() => {});
  }, []);

  // Reload incidents whenever any filter changes
  useEffect(() => {
    let cancelled = false;

    const fetchIncidents = async () => {
      setLoading(true);
      setError(null);

      // Stream filter: incidents aren't DB-linked to streams yet
      if (selectedStreamId !== "") {
        if (!cancelled) {
          setIncidents([]);
          setLoading(false);
        }
        return;
      }

      try {
        const params: Parameters<typeof api.listIncidents>[0] = { limit: 500 };
        if (violationType !== "ALL") params.violation_type = violationType;
        if (riskLevel !== "ALL") params.risk_level = riskLevel;
        if (selectedVideoId !== "") params.video_id = Number(selectedVideoId);

        const res = await api.listIncidents(params);
        if (!cancelled) setIncidents(res.data);
      } catch {
        if (!cancelled) setError("Failed to load incidents. Is the backend running?");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    fetchIncidents();
    return () => { cancelled = true; };
  }, [violationType, riskLevel, selectedVideoId, selectedStreamId]);

  const completedVideos = videos.filter((v) => v.status === "completed");
  const streamSelected = selectedStreamId !== "";

  return (
    <DashboardShell title="Incidents">
      <div className="space-y-4">
        {/* Filter bar */}
        <div className="flex flex-wrap items-center gap-3 bg-[#1e293b] border border-[#334155] rounded-xl px-4 py-3">
          <div className="flex items-center gap-2 text-slate-400">
            <Filter size={14} />
            <span className="text-sm font-medium">Filter:</span>
          </div>

          {/* Violation type */}
          <select
            value={violationType}
            onChange={(e) => setViolationType(e.target.value)}
            className="bg-[#0f172a] border border-[#334155] text-slate-300 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-amber-500"
          >
            {VIOLATION_TYPES.map((t) => (
              <option key={t} value={t}>
                {t === "ALL" ? "All Types" : t.replace(/_/g, " ")}
              </option>
            ))}
          </select>

          {/* Risk level */}
          <select
            value={riskLevel}
            onChange={(e) => setRiskLevel(e.target.value)}
            className="bg-[#0f172a] border border-[#334155] text-slate-300 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-amber-500"
          >
            {RISK_LEVELS.map((r) => (
              <option key={r} value={r}>
                {r === "ALL" ? "All Risk Levels" : r}
              </option>
            ))}
          </select>

          {/* Video selector */}
          <select
            value={selectedVideoId}
            onChange={(e) => { setSelectedVideoId(e.target.value); setSelectedStreamId(""); }}
            className="bg-[#0f172a] border border-[#334155] text-slate-300 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-amber-500 max-w-[200px]"
          >
            <option value="">All Videos</option>
            {completedVideos.map((v) => (
              <option key={v.id} value={String(v.id)}>
                {v.filename.length > 26 ? v.filename.slice(0, 24) + "…" : v.filename}
              </option>
            ))}
          </select>

          {/* Stream selector */}
          <select
            value={selectedStreamId}
            onChange={(e) => { setSelectedStreamId(e.target.value); setSelectedVideoId(""); }}
            className="bg-[#0f172a] border border-[#334155] text-slate-300 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-amber-500 max-w-[200px]"
          >
            <option value="">All Streams</option>
            {streams.map((s) => (
              <option key={s.stream_id} value={s.stream_id}>
                {s.name.length > 26 ? s.name.slice(0, 24) + "…" : s.name}
              </option>
            ))}
          </select>

          {!loading && !error && !streamSelected && (
            <span className="text-slate-500 text-sm ml-auto">
              {incidents.length} result{incidents.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>

        {loading && <LoadingState message="Loading incidents..." />}
        {error && <ErrorState message={error} onRetry={() => setViolationType(violationType)} />}

        {/* Stream selected but no DB link yet */}
        {!loading && streamSelected && (
          <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-10 text-center space-y-2">
            <p className="text-slate-400 font-medium">Live stream incident history</p>
            <p className="text-slate-600 text-sm">
              Stream-linked incident storage will appear here once live stream processing is fully enabled.
            </p>
          </div>
        )}

        {!loading && !error && !streamSelected && incidents.length === 0 && (
          <EmptyState
            title="No incidents found"
            message="No PPE violations match the selected filters."
            icon={AlertTriangle}
          />
        )}

        {!loading && !error && !streamSelected && incidents.length > 0 && (
          <div className="space-y-3">
            {incidents.map((incident) => (
              <IncidentCard
                key={incident.id}
                incident={incident}
                screenshotBase={SCREENSHOT_BASE}
              />
            ))}
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
