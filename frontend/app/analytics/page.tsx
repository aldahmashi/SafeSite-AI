"use client";

import { useEffect, useState } from "react";
import {
  BarChart, Bar, PieChart, Pie, Cell, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { VideoIcon } from "lucide-react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { ChartCard } from "@/components/ui/ChartCard";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { api } from "@/lib/api";
import type { AnalyticsOverview, Video, VideoSummary } from "@/lib/types";

const VIOLATION_COLORS: Record<string, string> = {
  NO_HELMET:               "#f59e0b",
  NO_VEST:                 "#3b82f6",
  NO_MASK:                 "#06b6d4",
  HIGH_RISK_ZONE:          "#ef4444",
  MACHINERY_PROXIMITY_RISK:"#8b5cf6",
  FALL_RISK:               "#ec4899",
};

const RISK_COLORS: Record<string, string> = {
  LOW:      "#22c55e",
  MEDIUM:   "#f59e0b",
  HIGH:     "#f97316",
  CRITICAL: "#ef4444",
};

const COMPLIANCE_COLORS = ["#f59e0b", "#3b82f6", "#06b6d4"];

export default function AnalyticsPage() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedVideoId, setSelectedVideoId] = useState<number | "">("");
  const [videoSummary, setVideoSummary] = useState<VideoSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);

  const load = async () => {
    try {
      setLoading(true);
      setError(null);
      const [overviewRes, vidRes] = await Promise.all([
        api.getAnalyticsOverview(),
        api.listVideos(0, 100),
      ]);
      setOverview(overviewRes.data);
      setVideos(vidRes.data);
    } catch {
      setError("Failed to load analytics data. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  // Fetch per-video summary when a video is selected
  useEffect(() => {
    if (selectedVideoId === "") {
      setVideoSummary(null);
      return;
    }
    setSummaryLoading(true);
    api.getVideoSummary(selectedVideoId as number)
      .then((r) => setVideoSummary(r.data))
      .catch(() => setVideoSummary(null))
      .finally(() => setSummaryLoading(false));
  }, [selectedVideoId]);

  const completedVideos = videos.filter((v) => v.status === "completed");

  // ── Charts derived from overview (all videos) or selected video summary ──────

  const violationData = selectedVideoId === "" && overview
    ? Object.entries(overview.violation_breakdown).map(([name, count]) => ({
        name: name.replace(/_/g, " "),
        count,
        fill: VIOLATION_COLORS[name] ?? "#94a3b8",
      }))
    : [];

  const riskData = selectedVideoId === "" && overview
    ? Object.entries(overview.risk_breakdown).map(([name, value]) => ({
        name,
        value,
        fill: RISK_COLORS[name] ?? "#94a3b8",
      }))
    : (() => {
        // For a specific selected video, compute risk from its incidents
        if (!videoSummary) return [];
        // Reuse risk_breakdown from overview filtered to this video — not available yet,
        // so return empty (overview only has aggregate data)
        return [];
      })();

  // When a specific video is selected, fetch incidents separately for risk chart
  const [videoIncidents, setVideoIncidents] = useState<Record<string, number>>({});
  useEffect(() => {
    if (selectedVideoId === "") {
      setVideoIncidents({});
      return;
    }
    api.listIncidents({ video_id: selectedVideoId as number, limit: 500 })
      .then((r) => {
        const counts: Record<string, number> = {};
        r.data.forEach((i) => {
          counts[i.risk_level] = (counts[i.risk_level] ?? 0) + 1;
        });
        setVideoIncidents(counts);
      })
      .catch(() => {});
  }, [selectedVideoId]);

  // Violation breakdown for selected video
  const [videoViolations, setVideoViolations] = useState<Record<string, number>>({});
  useEffect(() => {
    if (selectedVideoId === "") {
      setVideoViolations({});
      return;
    }
    api.listIncidents({ video_id: selectedVideoId as number, limit: 500 })
      .then((r) => {
        const counts: Record<string, number> = {};
        r.data.forEach((i) => {
          counts[i.violation_type] = (counts[i.violation_type] ?? 0) + 1;
        });
        setVideoViolations(counts);
      })
      .catch(() => {});
  }, [selectedVideoId]);

  const activeViolationData = selectedVideoId !== ""
    ? Object.entries(videoViolations).map(([name, count]) => ({
        name: name.replace(/_/g, " "),
        count,
        fill: VIOLATION_COLORS[name] ?? "#94a3b8",
      }))
    : violationData;

  const activeRiskData = selectedVideoId !== ""
    ? Object.entries(videoIncidents).map(([name, value]) => ({
        name,
        value,
        fill: RISK_COLORS[name] ?? "#94a3b8",
      }))
    : riskData;

  // Safety score trend — all completed videos
  const scoreTrend = completedVideos
    .filter((v) => v.safety_score !== null)
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
    .map((v, i) => ({
      name: `Video ${i + 1}`,
      score: v.safety_score as number,
      highlight: v.id === selectedVideoId,
    }));

  // PPE compliance — real worker-based numbers from backend
  const complianceData = videoSummary
    ? [
        { name: "Helmet",      compliance: videoSummary.helmet_compliance_pct },
        { name: "Safety Vest", compliance: videoSummary.vest_compliance_pct },
        { name: "Mask",        compliance: 100 }, // no mask tracking yet per video
      ]
    : overview
    ? [
        { name: "Helmet",      compliance: overview.helmet_compliance_pct },
        { name: "Safety Vest", compliance: overview.vest_compliance_pct },
        { name: "Mask",        compliance: overview.mask_compliance_pct },
      ]
    : [];

  const hasData = !!(overview && (overview.total_incidents > 0 || overview.completed_videos > 0));

  return (
    <DashboardShell title="Analytics">
      {loading && <LoadingState message="Loading analytics..." />}
      {error && <ErrorState message={error} onRetry={load} />}

      {!loading && !error && (
        <div className="space-y-6">
          {/* Video selector */}
          <div className="flex flex-wrap items-center gap-3 bg-[#1e293b] border border-[#334155] rounded-xl px-4 py-3">
            <VideoIcon size={15} className="text-slate-400" />
            <span className="text-slate-400 text-sm font-medium">Analyze:</span>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setSelectedVideoId("")}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  selectedVideoId === ""
                    ? "bg-amber-500 text-slate-900"
                    : "bg-[#0f172a] text-slate-400 hover:text-slate-200 border border-[#334155]"
                }`}
              >
                All Videos
              </button>
              {completedVideos.map((v) => (
                <button
                  key={v.id}
                  onClick={() => setSelectedVideoId(v.id)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors max-w-[180px] truncate ${
                    selectedVideoId === v.id
                      ? "bg-amber-500 text-slate-900"
                      : "bg-[#0f172a] text-slate-400 hover:text-slate-200 border border-[#334155]"
                  }`}
                  title={v.filename}
                >
                  {v.filename.length > 22 ? v.filename.slice(0, 20) + "…" : v.filename}
                </button>
              ))}
            </div>

            {/* Summary badge for selected video */}
            {selectedVideoId !== "" && videoSummary && !summaryLoading && (
              <span className="ml-auto text-slate-500 text-xs">
                {videoSummary.total_workers} workers · {videoSummary.total_incidents} incidents
                · score {videoSummary.video.safety_score ?? "—"}
              </span>
            )}
            {selectedVideoId !== "" && summaryLoading && (
              <span className="ml-auto text-slate-600 text-xs animate-pulse">Loading…</span>
            )}
            {selectedVideoId === "" && overview && (
              <span className="ml-auto text-slate-500 text-xs">
                {overview.total_workers} workers · {overview.total_incidents} incidents
                · avg score {overview.avg_safety_score}
              </span>
            )}
          </div>

          {!hasData ? (
            <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-12 text-center">
              <p className="text-slate-400">No data yet — upload and process a video to see analytics.</p>
            </div>
          ) : (
            <>
              {/* Row 1 */}
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <ChartCard title="Violations by Type" subtitle="Count per violation category">
                  {activeViolationData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={240}>
                      <BarChart data={activeViolationData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                        <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} allowDecimals={false} />
                        <Tooltip
                          contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8 }}
                          labelStyle={{ color: "#e2e8f0" }}
                          itemStyle={{ color: "#94a3b8" }}
                        />
                        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                          {activeViolationData.map((entry, i) => (
                            <Cell key={i} fill={entry.fill} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="text-slate-500 text-sm text-center py-16">No incidents yet</p>
                  )}
                </ChartCard>

                <ChartCard title="Risk Level Distribution" subtitle="Incidents by severity">
                  {activeRiskData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={240}>
                      <PieChart>
                        <Pie
                          data={activeRiskData}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={90}
                          paddingAngle={3}
                          dataKey="value"
                        >
                          {activeRiskData.map((entry, i) => (
                            <Cell key={i} fill={entry.fill} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8 }}
                          labelStyle={{ color: "#e2e8f0" }}
                          itemStyle={{ color: "#94a3b8" }}
                        />
                        <Legend formatter={(v) => <span style={{ color: "#94a3b8", fontSize: 12 }}>{v}</span>} />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="text-slate-500 text-sm text-center py-16">No incidents yet</p>
                  )}
                </ChartCard>
              </div>

              {/* Row 2 */}
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <ChartCard
                  title="Safety Score Trend"
                  subtitle="Per processed video (chronological)"
                >
                  {scoreTrend.length > 0 ? (
                    <ResponsiveContainer width="100%" height={240}>
                      <LineChart data={scoreTrend} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                        <YAxis domain={[0, 100]} tick={{ fill: "#94a3b8", fontSize: 11 }} />
                        <Tooltip
                          contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8 }}
                          labelStyle={{ color: "#e2e8f0" }}
                          itemStyle={{ color: "#94a3b8" }}
                          formatter={(v: number) => [`${v}%`, "Safety Score"]}
                        />
                        <Line
                          type="monotone"
                          dataKey="score"
                          stroke="#f59e0b"
                          strokeWidth={2}
                          dot={{ fill: "#f59e0b", r: 4 }}
                          activeDot={{ r: 6 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <p className="text-slate-500 text-sm text-center py-16">No completed videos yet</p>
                  )}
                </ChartCard>

                <ChartCard
                  title="PPE Compliance Rate"
                  subtitle={
                    videoSummary
                      ? "Based on tracked workers in this video"
                      : "Based on tracked workers across all videos"
                  }
                >
                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={complianceData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                      <YAxis domain={[0, 100]} tick={{ fill: "#94a3b8", fontSize: 11 }} />
                      <Tooltip
                        contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8 }}
                        labelStyle={{ color: "#e2e8f0" }}
                        itemStyle={{ color: "#94a3b8" }}
                        formatter={(v: number) => [`${v}%`, "Compliance"]}
                      />
                      <Bar dataKey="compliance" radius={[4, 4, 0, 0]}>
                        {complianceData.map((_, i) => (
                          <Cell key={i} fill={COMPLIANCE_COLORS[i % COMPLIANCE_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </ChartCard>
              </div>
            </>
          )}
        </div>
      )}
    </DashboardShell>
  );
}
