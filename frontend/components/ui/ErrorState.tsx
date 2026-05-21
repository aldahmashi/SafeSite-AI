"use client";

import { AlertTriangle } from "lucide-react";

interface Props {
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({
  message = "Something went wrong. The backend may not be running.",
  onRetry,
}: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4">
      <div className="p-4 bg-red-500/10 rounded-full">
        <AlertTriangle size={32} className="text-red-400" />
      </div>
      <p className="text-slate-300 text-sm text-center max-w-sm">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm rounded-lg transition-colors"
        >
          Try again
        </button>
      )}
    </div>
  );
}
