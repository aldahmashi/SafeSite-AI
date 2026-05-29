"use client";

import { useEffect, useState } from "react";
import { FileText, Download, RefreshCw, Plus } from "lucide-react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { LoadingState } from "@/components/ui/LoadingState";
import { ErrorState } from "@/components/ui/ErrorState";
import { EmptyState } from "@/components/ui/EmptyState";
import { DataTable } from "@/components/ui/DataTable";
import { api } from "@/lib/api";
import type { Report, Video } from "@/lib/types";
import { format } from "date-fns";

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState<number | null>(null);
  const [selectedVideoId, setSelectedVideoId] = useState<string>("");

  const load = async () => {
    try {
      setLoading(true);
      setError(null);
      const [rRes, vRes] = await Promise.all([
        api.listReports(),
        api.listVideos(0, 100),
      ]);
      setReports(rRes.data);
      const completed = vRes.data.filter((v) => v.status === "completed");
      setVideos(completed);
    } catch {
      setError("Failed to load reports. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleGenerate = async () => {
    const id = Number(selectedVideoId);
    if (!id) return;
    try {
      setGenerating(id);
      await api.generateReport(id);
      await load();
      setSelectedVideoId("");
    } catch {
      // show nothing — next load will refresh
    } finally {
      setGenerating(null);
    }
  };

  return (
    <DashboardShell title="Reports">
      <div className="space-y-6">
        {/* Generate report panel */}
        <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-5">
          <h2 className="text-slate-200 font-semibold mb-3">Generate Report</h2>
          <div className="flex flex-wrap gap-3 items-end">
            <div className="flex-1 min-w-48">
              <label className="text-slate-400 text-xs block mb-1">Select completed video</label>
              <select
                value={selectedVideoId}
                onChange={(e) => setSelectedVideoId(e.target.value)}
                className="w-full bg-[#0f172a] border border-[#334155] text-slate-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-amber-500"
              >
                <option value="">— choose video —</option>
                {videos.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.filename} (ID {v.id})
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={handleGenerate}
              disabled={!selectedVideoId || generating !== null}
              className="flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed text-black text-sm font-semibold rounded-lg transition-colors"
            >
              {generating !== null ? (
                <RefreshCw size={14} className="animate-spin" />
              ) : (
                <Plus size={14} />
              )}
              Generate
            </button>
          </div>
          {videos.length === 0 && !loading && (
            <p className="text-slate-500 text-xs mt-2">
              No completed videos yet — process a video first.
            </p>
          )}
        </div>

        {/* Reports table */}
        {loading && <LoadingState message="Loading reports..." />}
        {error && <ErrorState message={error} onRetry={load} />}

        {!loading && !error && reports.length === 0 && (
          <EmptyState
            title="No reports yet"
            message="Generate a report from a completed video above."
            icon={FileText}
          />
        )}

        {!loading && !error && reports.length > 0 && (
          <DataTable
            data={reports}
            keyFn={(r) => r.id}
            columns={[
              {
                key: "id",
                header: "Report ID",
                render: (r) => (
                  <span className="text-slate-400 text-xs font-mono">#{r.id}</span>
                ),
              },
              {
                key: "video_id",
                header: "Video ID",
                render: (r) => (
                  <span className="text-slate-300 text-sm">Video #{r.video_id}</span>
                ),
              },
              {
                key: "summary",
                header: "Summary",
                render: (r) => (
                  <span className="text-slate-400 text-sm truncate max-w-xs block">
                    {r.summary ?? "—"}
                  </span>
                ),
              },
              {
                key: "created_at",
                header: "Created",
                render: (r) => (
                  <span className="text-slate-400 text-xs">
                    {format(new Date(r.created_at), "MMM d, yyyy HH:mm")}
                  </span>
                ),
              },
              {
                key: "download",
                header: "",
                render: (r) =>
                  r.report_path ? (
                    <a
                      href={api.downloadReportUrl(r.id)}
                      download
                      onClick={(e) => e.stopPropagation()}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 text-xs rounded-lg transition-colors"
                    >
                      <Download size={12} />
                      PDF
                    </a>
                  ) : (
                    <span className="text-slate-600 text-xs">No PDF</span>
                  ),
              },
            ]}
          />
        )}
      </div>
    </DashboardShell>
  );
}
