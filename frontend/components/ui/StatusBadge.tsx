"use client";

import clsx from "clsx";
import type { VideoStatus, RiskLevel, ViolationType } from "@/lib/types";

type BadgeVariant = VideoStatus | RiskLevel | ViolationType | string;

const STATUS_STYLES: Record<string, string> = {
  // VideoStatus
  uploaded: "bg-blue-500/20 text-blue-300 border-blue-500/30",
  processing: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
  completed: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  failed: "bg-red-500/20 text-red-300 border-red-500/30",
  // RiskLevel
  LOW: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
  MEDIUM: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
  HIGH: "bg-orange-500/20 text-orange-300 border-orange-500/30",
  CRITICAL: "bg-red-500/20 text-red-300 border-red-500/30",
  // ViolationType
  NO_HELMET: "bg-orange-500/20 text-orange-300 border-orange-500/30",
  NO_VEST: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
  HIGH_RISK_ZONE: "bg-red-500/20 text-red-300 border-red-500/30",
  MACHINERY_PROXIMITY_RISK: "bg-red-500/20 text-red-300 border-red-500/30",
  FALL_RISK: "bg-red-600/20 text-red-300 border-red-600/30",
};

const LABELS: Record<string, string> = {
  uploaded: "Uploaded",
  processing: "Processing",
  completed: "Completed",
  failed: "Failed",
  LOW: "Low",
  MEDIUM: "Medium",
  HIGH: "High",
  CRITICAL: "Critical",
  NO_HELMET: "No Helmet",
  NO_VEST: "No Vest",
  HIGH_RISK_ZONE: "High Risk Zone",
  MACHINERY_PROXIMITY_RISK: "Machinery Proximity",
  FALL_RISK: "Fall Risk",
};

interface Props {
  value: BadgeVariant;
  className?: string;
}

export function StatusBadge({ value, className }: Props) {
  const style =
    STATUS_STYLES[value] ?? "bg-slate-500/20 text-slate-300 border-slate-500/30";
  const label = LABELS[value] ?? value;

  return (
    <span
      className={clsx(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border",
        style,
        className
      )}
    >
      {label}
    </span>
  );
}
