"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { Upload, CheckCircle, AlertCircle, FileVideo, X } from "lucide-react";
import { DashboardShell } from "@/components/layout/DashboardShell";
import { api } from "@/lib/api";
import type { Video } from "@/lib/types";

type UploadState = "idle" | "uploading" | "uploaded" | "error";

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<Video | null>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [dragging, setDragging] = useState(false);

  const handleFile = (f: File) => {
    const allowed = ["video/mp4", "video/quicktime", "video/x-msvideo", "video/x-matroska"];
    const ext = f.name.toLowerCase();
    if (
      !allowed.includes(f.type) &&
      !ext.endsWith(".mp4") &&
      !ext.endsWith(".mov") &&
      !ext.endsWith(".avi") &&
      !ext.endsWith(".mkv")
    ) {
      setErrorMsg("Unsupported file type. Please upload MP4, MOV, AVI, or MKV.");
      return;
    }
    setFile(f);
    setErrorMsg("");
    setUploadState("idle");
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) handleFile(dropped);
  }, []);

  const onInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleFile(f);
  };

  const handleUpload = async () => {
    if (!file) return;
    try {
      setUploadState("uploading");
      setProgress(0);
      const res = await api.uploadVideo(file, setProgress);
      setResult(res.data);
      setUploadState("uploaded");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Upload failed. Is the backend running?";
      setErrorMsg(msg);
      setUploadState("error");
    }
  };

  const reset = () => {
    setFile(null);
    setUploadState("idle");
    setProgress(0);
    setResult(null);
    setErrorMsg("");
  };

  return (
    <DashboardShell title="Upload Video">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Dropzone */}
        <div
          onDrop={onDrop}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors ${
            dragging
              ? "border-amber-500 bg-amber-500/5"
              : "border-[#334155] hover:border-[#475569] bg-[#1e293b]"
          }`}
        >
          {!file ? (
            <>
              <div className="flex justify-center mb-4">
                <div className="p-4 bg-amber-500/10 rounded-full">
                  <Upload size={28} className="text-amber-400" />
                </div>
              </div>
              <p className="text-slate-200 font-medium">
                Drag & drop a video here
              </p>
              <p className="text-slate-500 text-sm mt-1">
                MP4, MOV, AVI, MKV supported
              </p>
              <label className="mt-4 inline-block cursor-pointer">
                <span className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm rounded-lg transition-colors">
                  Browse file
                </span>
                <input
                  type="file"
                  accept=".mp4,.mov,.avi,.mkv,video/*"
                  className="hidden"
                  onChange={onInputChange}
                />
              </label>
            </>
          ) : (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FileVideo size={24} className="text-amber-400 flex-shrink-0" />
                <div className="text-left">
                  <p className="text-slate-200 font-medium truncate max-w-sm">
                    {file.name}
                  </p>
                  <p className="text-slate-500 text-xs">
                    {(file.size / 1024 / 1024).toFixed(1)} MB
                  </p>
                </div>
              </div>
              <button
                onClick={reset}
                className="text-slate-500 hover:text-slate-300 transition-colors ml-4"
              >
                <X size={16} />
              </button>
            </div>
          )}
        </div>

        {/* Error */}
        {errorMsg && (
          <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/30 rounded-xl">
            <AlertCircle size={18} className="text-red-400 flex-shrink-0" />
            <p className="text-red-300 text-sm">{errorMsg}</p>
          </div>
        )}

        {/* Progress */}
        {uploadState === "uploading" && (
          <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-5 space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-300">Uploading...</span>
              <span className="text-amber-400 font-medium">{progress}%</span>
            </div>
            <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-amber-400 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-slate-500 text-xs">
              Processing will start automatically after upload. Large files may
              take a moment.
            </p>
          </div>
        )}

        {/* Success */}
        {uploadState === "uploaded" && result && (
          <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-5 space-y-3">
            <div className="flex items-center gap-3">
              <CheckCircle size={20} className="text-emerald-400" />
              <div>
                <p className="text-emerald-300 font-medium">Upload successful</p>
                <p className="text-slate-400 text-sm mt-0.5">
                  Video ID {result.id} — status:{" "}
                  <span className="capitalize text-slate-300">{result.status}</span>
                </p>
              </div>
            </div>
            <p className="text-slate-500 text-sm">
              Background processing has started. Refresh the video page to check progress.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => router.push(`/videos/${result.id}`)}
                className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-black text-sm font-semibold rounded-lg transition-colors"
              >
                View results
              </button>
              <button
                onClick={reset}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm rounded-lg transition-colors"
              >
                Upload another
              </button>
            </div>
          </div>
        )}

        {/* Upload button */}
        {file && uploadState === "idle" && (
          <button
            onClick={handleUpload}
            className="w-full py-3 bg-amber-500 hover:bg-amber-600 text-black font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
          >
            <Upload size={18} />
            Upload and analyze
          </button>
        )}

        {/* Info box */}
        <div className="bg-[#1e293b] border border-[#334155] rounded-xl p-4 text-sm text-slate-400 space-y-1">
          <p className="text-slate-300 font-medium mb-2">What happens after upload?</p>
          <p>• Video is saved and queued for background processing</p>
          <p>• YOLO model detects helmets, vests, and workers per frame</p>
          <p>• Violations are timestamped and screenshots are captured</p>
          <p>• An annotated video and safety score are generated</p>
          <p>• Results appear on the video detail page</p>
        </div>
      </div>
    </DashboardShell>
  );
}
