export type VideoStatus = "uploaded" | "processing" | "completed" | "failed";

export type ViolationType =
  | "NO_HELMET"
  | "NO_VEST"
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
  frame_count: number | null;
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
  bounding_box: Record<string, number> | null;
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

export interface ApiError {
  detail: string;
}
