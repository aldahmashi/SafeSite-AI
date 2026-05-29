"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Upload,
  Video,
  AlertTriangle,
  BarChart2,
  FileText,
  MessageSquare,
  ShieldCheck,
  X,
  Radio,
} from "lucide-react";
import clsx from "clsx";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/upload", label: "Upload Video", icon: Upload },
  { href: "/videos", label: "Videos", icon: Video },
  { href: "/streams", label: "Live Streams", icon: Radio },
  { href: "/incidents", label: "Incidents", icon: AlertTriangle },
  { href: "/analytics", label: "Analytics", icon: BarChart2 },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/assistant", label: "AI Assistant", icon: MessageSquare },
];

interface Props {
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ open, onClose }: Props) {
  const pathname = usePathname();

  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/60 z-20 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          "fixed top-0 left-0 h-full w-64 bg-[#0f172a] border-r border-[#1e293b] z-30 flex flex-col transition-transform duration-200",
          "lg:translate-x-0 lg:static lg:z-auto",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Logo */}
        <div className="flex items-center justify-between px-5 py-5 border-b border-[#1e293b]">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-500/10 rounded-lg">
              <ShieldCheck size={20} className="text-amber-400" />
            </div>
            <div>
              <span className="text-white font-bold text-sm leading-tight block">
                SafeSite AI
              </span>
              <span className="text-slate-500 text-xs">Safety Monitor</span>
            </div>
          </div>
          <button
            className="lg:hidden text-slate-500 hover:text-slate-300 transition-colors"
            onClick={onClose}
          >
            <X size={18} />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                onClick={onClose}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                  active
                    ? "bg-amber-500/15 text-amber-400 border border-amber-500/20"
                    : "text-slate-400 hover:text-slate-200 hover:bg-[#1e293b]"
                )}
              >
                <Icon size={16} />
                {label}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-[#1e293b]">
          <p className="text-slate-600 text-xs">Phase 4 — Live Streams</p>
          <p className="text-slate-700 text-xs mt-0.5">v0.4.0</p>
        </div>
      </aside>
    </>
  );
}
