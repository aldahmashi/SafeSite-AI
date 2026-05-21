import axios from "axios";
import type { Video, Incident, VideoSummary, DashboardStats } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const client = axios.create({ baseURL: BASE, timeout: 60_000 });

export const api = {
  // Health
  health: () => client.get<{ status: string }>("/health"),

  // Videos
  listVideos: (skip = 0, limit = 50) =>
    client.get<Video[]>("/api/videos", { params: { skip, limit } }),

  getVideo: (id: number) => client.get<Video>(`/api/videos/${id}`),

  getVideoSummary: (id: number) =>
    client.get<VideoSummary>(`/api/videos/${id}/summary`),

  getVideoIncidents: (id: number) =>
    client.get<Incident[]>(`/api/videos/${id}/incidents`),

  uploadVideo: (file: File, onProgress?: (pct: number) => void) => {
    const form = new FormData();
    form.append("file", file);
    return client.post<Video>("/api/videos/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (e) => {
        if (onProgress && e.total) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      },
    });
  },

  downloadAnnotatedVideo: (id: number) =>
    `${BASE}/api/videos/${id}/download`,

  // Incidents
  listIncidents: (params?: {
    skip?: number;
    limit?: number;
    violation_type?: string;
    risk_level?: string;
  }) => client.get<Incident[]>("/api/incidents", { params }),

  getIncident: (id: number) => client.get<Incident>(`/api/incidents/${id}`),

  // Reports
  generateReport: (videoId: number) =>
    client.post(`/api/reports/generate/${videoId}`),

  // Screenshot URL helper
  screenshotUrl: (path: string) =>
    `${BASE}/api/incidents/screenshot?path=${encodeURIComponent(path)}`,

  // Dashboard stats — computed client-side; never throws, returns zeroed stats on failure
  getDashboardStats: async (): Promise<DashboardStats> => {
    const empty: DashboardStats = {
      total_videos: 0,
      total_incidents: 0,
      high_risk_incidents: 0,
      avg_safety_score: 0,
      helmet_compliance_pct: 100,
      vest_compliance_pct: 100,
    };

    const [videosResult, incidentsResult] = await Promise.allSettled([
      client.get<Video[]>("/api/videos", { params: { limit: 1000 } }),
      client.get<Incident[]>("/api/incidents", { params: { limit: 1000 } }),
    ]);

    const videos: Video[] =
      videosResult.status === "fulfilled" ? videosResult.value.data ?? [] : [];
    const incidents: Incident[] =
      incidentsResult.status === "fulfilled"
        ? incidentsResult.value.data ?? []
        : [];

    if (videos.length === 0 && incidents.length === 0) return empty;

    const completed = videos.filter((v) => v.status === "completed");
    const scores = completed
      .map((v) => v.safety_score)
      .filter((s): s is number => s !== null);
    const avgScore =
      scores.length > 0
        ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
        : 0;

    const highRisk = incidents.filter(
      (i) => i.risk_level === "HIGH" || i.risk_level === "CRITICAL"
    ).length;

    const helmetViolations = incidents.filter(
      (i) => i.violation_type === "NO_HELMET"
    ).length;
    const vestViolations = incidents.filter(
      (i) => i.violation_type === "NO_VEST"
    ).length;
    const base = Math.max(completed.length * 5, 1);

    return {
      total_videos: videos.length,
      total_incidents: incidents.length,
      high_risk_incidents: highRisk,
      avg_safety_score: avgScore,
      helmet_compliance_pct: Math.max(
        0,
        Math.round(100 - (helmetViolations / base) * 100)
      ),
      vest_compliance_pct: Math.max(
        0,
        Math.round(100 - (vestViolations / base) * 100)
      ),
    };
  },
};
