"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Video,
  AlertTriangle,
  ShieldAlert,
  Activity,
  HardHat,
  Shirt,
} from "lucide-react";
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { StatCard } from "@/components/ui/StatCard";
import { ChartCard } from "@/components/ui/ChartCard";
import { IncidentCard } from "@/components/ui/IncidentCard";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { DataTable } from "@/components/ui/DataTable";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/lib/api";
import type { DashboardStats, Video as VideoType, Incident } from "@/lib/types";
import { format } from "date-fns";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const SCREENSHOT_BASE = `${BASE_URL}/violation_frames`;

const VIOLATION_COLORS: Record<string, string> = {
  "NO HELMET": "#f59e0b",
  "NO VEST": "#3b82f6",
  "HIGH RISK ZONE": "#ef4444",
  "MACHINERY PROXIMITY RISK": "#8b5cf6",
  "FALL RISK": "#ec4899",
};

const RISK_COLORS: Record<string, string> = {
  LOW: "#22c55e",
  MEDIUM: "#f59e0b",
  HIGH: "#f97316",
  CRITICAL: "#ef4444",
};

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentVideos, setRecentVideos] = useState<VideoType[]>([]);
  const [recentIncidents, setRecentIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      setLoading(true);
      setError(null);
      const [statsData, videosRes, incidentsRes] = await Promise.all([
        api.getDashboardStats(),
        api.listVideos(0, 5),
        api.listIncidents({ limit: 5 }),
      ]);
      setStats(statsData);
      setRecentVideos(videosRes.data);
      setRecentIncidents(incidentsRes.data);
    } catch {
      setError("Failed to load dashboard data. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  // Chart data derived from stats
  const complianceChartData = stats
    ? [
        { name: "Helmet", compliance: stats.helmet_compliance_pct },
        { name: "Vest", compliance: stats.vest_compliance_pct },
      ]
    : [];

  const riskChartData =
    stats && stats.total_incidents > 0
      ? [
          {
            name: "High Risk",
            value: stats.high_risk_incidents,
            fill: RISK_COLORS.HIGH,
          },
          {
            name: "Other",
            value: Math.max(0, stats.total_incidents - stats.high_risk_incidents),
            fill: "#334155",
          },
        ]
      : [];

  const safeScoreColor = (score: number) => {
    if (score >= 80) return "green";
    if (score >= 60) return "yellow";
    return "red";
  };

  return (
    <DashboardShell title="Dashboard">
      {loading && <LoadingState message="Loading dashboard..." />}
      {error && <ErrorState message={error} onRetry={load} />}

      {!loading && !error && stats && (
        <div className="space-y-6">
          {/* Stats grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
            <StatCard
              title="Total Videos"
              value={stats.total_videos}
              subtitle="Uploaded for analysis"
              icon={Video}
              accent="blue"
            />
            <StatCard
              title="Total Incidents"
              value={stats.total_incidents}
              subtitle="Across all videos"
              icon={AlertTriangle}
              accent="yellow"
            />
            <StatCard
              title="High-Risk Incidents"
              value={stats.high_risk_incidents}
              subtitle="HIGH or CRITICAL level"
              icon={ShieldAlert}
              accent="red"
            />
            <StatCard
              title="Avg Safety Score"
              value={stats.avg_safety_score > 0 ? `${stats.avg_safety_score}%` : "N/A"}
              subtitle="Across completed videos"
              icon={Activity}
              accent={stats.avg_safety_score > 0 ? safeScoreColor(stats.avg_safety_score) : "default"}
            />
            <StatCard
              title="Helmet Compliance"
              value={`${stats.helmet_compliance_pct}%`}
              subtitle="Workers with hard hats"
              icon={HardHat}
              accent="green"
            />
            <StatCard
              title="Vest Compliance"
              value={`${stats.vest_compliance_pct}%`}
              subtitle="Workers with safety vests"
              icon={Shirt}
              accent="green"
            />
          </div>

          {/* Charts row */}
          {stats.total_incidents > 0 && (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <ChartCard title="PPE Compliance" subtitle="Helmet and vest compliance rates">
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={complianceChartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                    <YAxis domain={[0, 100]} tick={{ fill: "#94a3b8", fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8 }}
                      labelStyle={{ color: "#e2e8f0" }}
                      formatter={(v: number) => [`${v}%`, "Compliance"]}
                    />
                    <Bar dataKey="compliance" radius={[4, 4, 0, 0]}>
                      <Cell fill="#22c55e" />
                      <Cell fill="#3b82f6" />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Risk Breakdown" subtitle="High-risk vs other incidents">
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={riskChartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={80}
                      paddingAngle={3}
                      dataKey="value"
                    >
                      {riskChartData.map((entry, i) => (
                        <Cell key={i} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8 }}
                      labelStyle={{ color: "#e2e8f0" }}
                      itemStyle={{ color: "#94a3b8" }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </ChartCard>
            </div>
          )}

          {/* Recent incidents */}
          {recentIncidents.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-slate-200 font-semibold">Recent Incidents</h2>
                <button
                  onClick={() => router.push("/incidents")}
                  className="text-amber-400 hover:text-amber-300 text-sm transition-colors"
                >
                  View all →
                </button>
              </div>
              <div className="space-y-3">
                {recentIncidents.map((incident) => (
                  <IncidentCard
                    key={incident.id}
                    incident={incident}
                    screenshotBase={SCREENSHOT_BASE}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Recent videos */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-slate-200 font-semibold">Recent Videos</h2>
              <button
                onClick={() => router.push("/videos")}
                className="text-amber-400 hover:text-amber-300 text-sm transition-colors"
              >
                View all →
              </button>
            </div>

            {recentVideos.length === 0 ? (
              <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-8 text-center">
                <p className="text-slate-400 text-sm">No videos uploaded yet.</p>
                <button
                  onClick={() => router.push("/upload")}
                  className="mt-3 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-black text-sm font-semibold rounded-lg transition-colors"
                >
                  Upload your first video
                </button>
              </div>
            ) : (
              <DataTable
                data={recentVideos}
                keyFn={(v) => v.id}
                onRowClick={(v) => router.push(`/videos/${v.id}`)}
                columns={[
                  {
                    key: "filename",
                    header: "Filename",
                    render: (v) => (
                      <span className="text-slate-200 font-medium truncate max-w-xs block">
                        {v.filename}
                      </span>
                    ),
                  },
                  {
                    key: "status",
                    header: "Status",
                    render: (v) => <StatusBadge value={v.status} />,
                  },
                  {
                    key: "safety_score",
                    header: "Safety Score",
                    render: (v) =>
                      v.safety_score !== null ? (
                        <span
                          className={
                            v.safety_score >= 80
                              ? "text-emerald-400"
                              : v.safety_score >= 60
                              ? "text-yellow-400"
                              : "text-red-400"
                          }
                        >
                          {v.safety_score}%
                        </span>
                      ) : (
                        <span className="text-slate-500">—</span>
                      ),
                  },
                  {
                    key: "created_at",
                    header: "Uploaded",
                    render: (v) => (
                      <span className="text-slate-400 text-xs">
                        {format(new Date(v.created_at), "MMM d, yyyy HH:mm")}
                      </span>
                    ),
                  },
                ]}
              />
            )}
          </div>
        </div>
      )}
    </DashboardShell>
  );
}
