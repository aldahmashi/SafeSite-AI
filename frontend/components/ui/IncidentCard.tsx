"use client";

import { Clock, User, Camera } from "lucide-react";
import { StatusBadge } from "./StatusBadge";
import type { Incident } from "@/lib/types";

interface Props {
  incident: Incident;
  screenshotBase?: string;
}

function formatTimestamp(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function IncidentCard({ incident, screenshotBase }: Props) {
  const screenshotUrl =
    incident.screenshot_path && screenshotBase
      ? `${screenshotBase}/${incident.screenshot_path.split(/[\\/]/).pop()}`
      : null;

  return (
    <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-4 flex gap-4 hover:border-[#475569] transition-colors">
      {screenshotUrl ? (
        <img
          src={screenshotUrl}
          alt="Violation screenshot"
          className="w-24 h-16 object-cover rounded-lg border border-slate-700 flex-shrink-0"
          onError={(e) => {
            (e.target as HTMLImageElement).style.display = "none";
          }}
        />
      ) : (
        <div className="w-24 h-16 bg-slate-700/50 rounded-lg flex items-center justify-center flex-shrink-0">
          <Camera size={20} className="text-slate-600" />
        </div>
      )}

      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2 flex-wrap">
            <StatusBadge value={incident.violation_type} />
            <StatusBadge value={incident.risk_level} />
          </div>
          <span className="text-slate-500 text-xs">
            {Math.round(incident.confidence * 100)}% confidence
          </span>
        </div>

        <div className="flex items-center gap-4 mt-2 text-slate-400 text-xs">
          <span className="flex items-center gap-1">
            <Clock size={12} />
            {formatTimestamp(incident.timestamp_seconds)}
          </span>
          {incident.worker_id && (
            <span className="flex items-center gap-1">
              <User size={12} />
              Worker #{incident.worker_id}
            </span>
          )}
          <span>Frame {incident.frame_number}</span>
        </div>
      </div>
    </div>
  );
}
