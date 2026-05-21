"use client";

import { Menu, Activity } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Props {
  onMenuClick: () => void;
  title: string;
}

export function Navbar({ onMenuClick, title }: Props) {
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    api
      .health()
      .then(() => setBackendStatus("online"))
      .catch(() => setBackendStatus("offline"));
  }, []);

  return (
    <header className="h-14 bg-[#0f172a] border-b border-[#1e293b] flex items-center px-4 gap-4 sticky top-0 z-10">
      <button
        className="lg:hidden text-slate-400 hover:text-slate-200 transition-colors"
        onClick={onMenuClick}
      >
        <Menu size={20} />
      </button>

      <h1 className="text-slate-200 font-semibold text-sm flex-1">{title}</h1>

      <div className="flex items-center gap-2">
        <Activity
          size={14}
          className={
            backendStatus === "online"
              ? "text-emerald-400"
              : backendStatus === "offline"
              ? "text-red-400"
              : "text-slate-500 animate-pulse"
          }
        />
        <span
          className={`text-xs ${
            backendStatus === "online"
              ? "text-emerald-400"
              : backendStatus === "offline"
              ? "text-red-400"
              : "text-slate-500"
          }`}
        >
          {backendStatus === "checking"
            ? "Connecting..."
            : backendStatus === "online"
            ? "Backend online"
            : "Backend offline"}
        </span>
      </div>
    </header>
  );
}
