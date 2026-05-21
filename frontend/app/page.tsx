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
import { DashboardShell } from "@/components/layout/DashboardShell";
import { StatCard } from "@/components/ui/StatCard";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { DataTable } from "@/components/ui/DataTable";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/lib/api";
import type { DashboardStats, Video as VideoType } from "@/lib/types";
import { format } from "date-fns";

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentVideos, setRecentVideos] = useState<VideoType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      setLoading(true);
      setError(null);
      const [statsData, videosRes] = await Promise.all([
        api.getDashboardStats(),
        api.listVideos(0, 5),
      ]);
      setStats(statsData);
      setRecentVideos(videosRes.data);
    } catch {
      setError("Failed to load dashboard data. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

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
              subtitle="Workers with helmets"
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
