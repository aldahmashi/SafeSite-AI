"use client";

import type { LucideIcon } from "lucide-react";
import { Inbox } from "lucide-react";

interface Props {
  title?: string;
  message?: string;
  icon?: LucideIcon;
  action?: React.ReactNode;
}

export function EmptyState({
  title = "No data yet",
  message = "Nothing to show here yet.",
  icon: Icon = Inbox,
  action,
}: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4">
      <div className="p-4 bg-slate-700/50 rounded-full">
        <Icon size={32} className="text-slate-500" />
      </div>
      <div className="text-center">
        <p className="text-slate-300 font-medium">{title}</p>
        <p className="text-slate-500 text-sm mt-1">{message}</p>
      </div>
      {action}
    </div>
  );
}
