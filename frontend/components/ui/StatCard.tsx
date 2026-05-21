"use client";

import clsx from "clsx";
import type { LucideIcon } from "lucide-react";

interface Props {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: "up" | "down" | "neutral";
  accent?: "default" | "green" | "red" | "yellow" | "blue";
}

const ACCENT_STYLES = {
  default: "text-amber-400 bg-amber-400/10",
  green: "text-emerald-400 bg-emerald-400/10",
  red: "text-red-400 bg-red-400/10",
  yellow: "text-yellow-400 bg-yellow-400/10",
  blue: "text-blue-400 bg-blue-400/10",
};

export function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  accent = "default",
}: Props) {
  return (
    <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-5 flex items-start gap-4 hover:border-[#475569] transition-colors">
      <div className={clsx("p-3 rounded-lg flex-shrink-0", ACCENT_STYLES[accent])}>
        <Icon size={20} />
      </div>
      <div className="min-w-0">
        <p className="text-slate-400 text-sm font-medium truncate">{title}</p>
        <p className="text-white text-2xl font-bold mt-0.5">{value}</p>
        {subtitle && (
          <p className="text-slate-500 text-xs mt-1">{subtitle}</p>
        )}
      </div>
    </div>
  );
}
