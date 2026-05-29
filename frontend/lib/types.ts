export type VideoStatus = "uploaded" | "processing" | "completed" | "failed";

export type ViolationType =
  | "NO_HELMET"
  | "NO_VEST"
  | "NO_MASK"
  | "HIGH_RISK_ZONE"
  | "MACHINERY_PROXIMITY_RISK"
  | "FALL_RISK";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface Video {
  id: number;
  filename: string;
  original_path: string;
  output_path: string | null;
  status: VideoStatus;
  fps: number | null;
  total_frames: number | null;
  duration_seconds: number | null;
  safety_score: number | null;
  created_at: string;
  updated_at: string | null;
}

export interface Incident {
  id: number;
  video_id: number;
  worker_id: number | null;
  violation_type: ViolationType;
  risk_level: RiskLevel;
  confidence: number;
  timestamp_seconds: number;
  frame_number: number;
  screenshot_path: string | null;
  bbox: string | null;
  description: string | null;
  created_at: string;
}

export interface VideoSummary {
  video: Video;
  total_workers: number;
  total_incidents: number;
  high_risk_incidents: number;
  helmet_compliance_pct: number;
  vest_compliance_pct: number;
}

export interface DashboardStats {
  total_videos: number;
  total_incidents: number;
  high_risk_incidents: number;
  avg_safety_score: number;
  helmet_compliance_pct: number;
  vest_compliance_pct: number;
}

export interface Report {
  id: number;
  video_id: number;
  report_path: string | null;
  summary: string | null;
  created_at: string;
}

export interface Stream {
  id: number;
  stream_id: string;
  name: string;
  url: string;
  status: "running" | "stopped" | "error";
  incident_count: number;
  error_message: string | null;
  started_at: string;
  stopped_at: string | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface AnalyticsOverview {
  total_workers: number;
  total_incidents: number;
  high_risk_incidents: number;
  helmet_compliance_pct: number;
  vest_compliance_pct: number;
  mask_compliance_pct: number;
  avg_safety_score: number;
  violation_breakdown: Record<string, number>;
  risk_breakdown: Record<string, number>;
  completed_videos: number;
}

export interface ApiError {
  detail: string;
}
