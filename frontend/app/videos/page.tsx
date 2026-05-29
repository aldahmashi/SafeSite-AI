"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { Video, Upload, RefreshCw, Search } from "lucide-react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { DataTable } from "@/components/ui/DataTable";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { api } from "@/lib/api";
import type { Video as VideoType, VideoStatus } from "@/lib/types";
import { format } from "date-fns";

const STATUS_OPTIONS: Array<{ label: string; value: VideoStatus | "ALL" }> = [
  { label: "All Statuses", value: "ALL" },
  { label: "Uploaded", value: "uploaded" },
  { label: "Processing", value: "processing" },
  { label: "Completed", value: "completed" },
  { label: "Failed", value: "failed" },
];

export default function VideosPage() {
  const router = useRouter();
  const [videos, setVideos] = useState<VideoType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<VideoStatus | "ALL">("ALL");

  const load = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.listVideos(0, 200);
      setVideos(res.data);
    } catch {
      setError("Failed to load videos. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const filtered = useMemo(() => {
    return videos.filter((v) => {
      const matchesSearch = v.filename.toLowerCase().includes(search.toLowerCase());
      const matchesStatus = statusFilter === "ALL" || v.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [videos, search, statusFilter]);

  return (
    <DashboardShell title="Videos">
      <div className="space-y-4">
        {/* Toolbar */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Search */}
          <div className="relative flex-1 min-w-48">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search by filename…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-[#1e293b] border border-[#334155] text-slate-300 text-sm rounded-lg pl-9 pr-3 py-2 focus:outline-none focus:border-amber-500 placeholder:text-slate-600"
            />
          </div>

          {/* Status filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as VideoStatus | "ALL")}
            className="bg-[#1e293b] border border-[#334155] text-slate-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-amber-500"
          >
            {STATUS_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>

          <button
            onClick={load}
            className="flex items-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm rounded-lg transition-colors"
          >
            <RefreshCw size={14} />
            Refresh
          </button>
          <button
            onClick={() => router.push("/upload")}
            className="flex items-center gap-2 px-3 py-2 bg-amber-500 hover:bg-amber-600 text-black text-sm font-semibold rounded-lg transition-colors"
          >
            <Upload size={14} />
            Upload
          </button>
        </div>

        {/* Count */}
        {!loading && !error && (
          <p className="text-slate-500 text-sm">
            {filtered.length} of {videos.length} video{videos.length !== 1 ? "s" : ""}
          </p>
        )}

        {loading && <LoadingState message="Loading videos..." />}
        {error && <ErrorState message={error} onRetry={load} />}

        {!loading && !error && videos.length === 0 && (
          <EmptyState
            title="No videos yet"
            message="Upload your first construction site video to get started."
            icon={Video}
            action={
              <button
                onClick={() => router.push("/upload")}
                className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-black text-sm font-semibold rounded-lg transition-colors"
              >
                Upload video
              </button>
            }
          />
        )}

        {!loading && !error && videos.length > 0 && filtered.length === 0 && (
          <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-8 text-center">
            <p className="text-slate-400 text-sm">No videos match your search.</p>
          </div>
        )}

        {!loading && !error && filtered.length > 0 && (
          <DataTable
            data={filtered}
            keyFn={(v) => v.id}
            onRowClick={(v) => router.push(`/videos/${v.id}`)}
            columns={[
              {
                key: "filename",
                header: "Filename",
                render: (v) => (
                  <span className="text-slate-200 font-medium">{v.filename}</span>
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
                          ? "text-emerald-400 font-medium"
                          : v.safety_score >= 60
                          ? "text-yellow-400 font-medium"
                          : "text-red-400 font-medium"
                      }
                    >
                      {v.safety_score}%
                    </span>
                  ) : (
                    <span className="text-slate-500">—</span>
                  ),
              },
              {
                key: "duration_seconds",
                header: "Duration",
                render: (v) =>
                  v.duration_seconds !== null ? (
                    <span className="text-slate-400 text-xs">
                      {Math.floor(v.duration_seconds / 60)}m{" "}
                      {Math.floor(v.duration_seconds % 60)}s
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
              {
                key: "actions",
                header: "",
                render: (v) => (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      router.push(`/videos/${v.id}`);
                    }}
                    className="text-amber-400 hover:text-amber-300 text-xs transition-colors"
                  >
                    View →
                  </button>
                ),
              },
            ]}
          />
        )}
      </div>
    </DashboardShell>
  );
}
