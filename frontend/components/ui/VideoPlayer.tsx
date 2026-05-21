"use client";

import { useState } from "react";
import { Play, Download, AlertCircle } from "lucide-react";

interface Props {
  src: string;
  downloadUrl?: string;
  filename?: string;
}

export function VideoPlayer({ src, downloadUrl, filename }: Props) {
  const [error, setError] = useState(false);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center bg-slate-800 rounded-xl aspect-video gap-3 border border-slate-700">
        <AlertCircle size={32} className="text-slate-500" />
        <p className="text-slate-400 text-sm">Video unavailable or still processing</p>
      </div>
    );
  }

  return (
    <div className="bg-black rounded-xl overflow-hidden border border-[#334155]">
      <video
        src={src}
        controls
        className="w-full aspect-video"
        onError={() => setError(true)}
        preload="metadata"
      >
        Your browser does not support the video tag.
      </video>
      {downloadUrl && (
        <div className="px-4 py-3 bg-[#1e293b] flex items-center justify-between">
          <span className="text-slate-400 text-sm truncate max-w-xs">
            {filename ?? "Annotated output"}
          </span>
          <a
            href={downloadUrl}
            download
            className="flex items-center gap-2 px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-black text-xs font-semibold rounded-lg transition-colors"
          >
            <Download size={14} />
            Download
          </a>
        </div>
      )}
    </div>
  );
}
