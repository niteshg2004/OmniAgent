"use client";

import { useCallback, useRef } from "react";

interface FileUploadProps {
  files: File[];
  onFilesChange: (files: File[]) => void;
  disabled?: boolean;
}

const ACCEPTED =
  ".pdf,.png,.jpg,.jpeg,.webp,.gif,.mp3,.wav,.m4a,.ogg,.txt,.md,.csv";

const getFileIcon = (fileName: string): string => {
  const ext = fileName.split(".").pop()?.toLowerCase() || "";
  if (["pdf"].includes(ext)) return "📄";
  if (["png", "jpg", "jpeg", "webp", "gif"].includes(ext)) return "🖼️";
  if (["mp3", "wav", "m4a", "ogg"].includes(ext)) return "🎵";
  if (["txt", "md", "csv"].includes(ext)) return "📋";
  return "📎";
};

const getFileTypeBadge = (fileName: string): string => {
  const ext = fileName.split(".").pop()?.toLowerCase() || "";
  if (["pdf"].includes(ext)) return "PDF";
  if (["png", "jpg", "jpeg", "webp", "gif"].includes(ext)) return "Image";
  if (["mp3", "wav", "m4a", "ogg"].includes(ext)) return "Audio";
  if (["txt"].includes(ext)) return "Text";
  if (["md"].includes(ext)) return "Markdown";
  if (["csv"].includes(ext)) return "CSV";
  return "File";
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
};

const getBadgeColor = (fileName: string): string => {
  const ext = fileName.split(".").pop()?.toLowerCase() || "";
  if (["pdf"].includes(ext)) return "bg-red-500/20 text-red-400 border-red-500/30";
  if (["png", "jpg", "jpeg", "webp", "gif"].includes(ext)) return "bg-blue-500/20 text-blue-400 border-blue-500/30";
  if (["mp3", "wav", "m4a", "ogg"].includes(ext)) return "bg-purple-500/20 text-purple-400 border-purple-500/30";
  if (["txt", "md", "csv"].includes(ext)) return "bg-green-500/20 text-green-400 border-green-500/30";
  return "bg-gray-500/20 text-gray-400 border-gray-500/30";
};

export function FileUpload({
  files,
  onFilesChange,
  disabled = false,
}: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = useCallback(
    (incoming: FileList | null) => {
      if (!incoming?.length) return;
      const merged = [...files, ...Array.from(incoming)];
      onFilesChange(merged);
    },
    [files, onFilesChange],
  );

  const removeFile = (index: number) => {
    onFilesChange(files.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-4">
      <div
        className="rounded-lg border-2 border-dashed border-surface-border bg-gray-50 p-6 text-center transition hover:border-accent/50"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          if (!disabled) addFiles(e.dataTransfer.files);
        }}
      >
        <p className="text-sm text-gray-600">
          Drag & drop files here, or{" "}
          <button
            type="button"
            className="text-accent hover:underline"
            disabled={disabled}
            onClick={() => inputRef.current?.click()}
          >
            browse
          </button>
        </p>
        <p className="mt-1 text-xs text-gray-500">
          PDF, images, audio, text — multiple files supported
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED}
          className="hidden"
          disabled={disabled}
          onChange={(e) => addFiles(e.target.files)}
        />
      </div>

      {files.length > 0 && (
        <div className="rounded-lg border border-accent/30 bg-accent/5 p-4">
          <div className="mb-3 flex items-center gap-2">
            <span className="text-xs font-semibold text-accent">✓ READY</span>
            <p className="text-sm font-medium text-gray-300">
              {files.length} file{files.length !== 1 ? "s" : ""} selected
            </p>
          </div>
          <ul className="space-y-2">
            {files.map((file, index) => (
              <li
                key={`${file.name}-${index}`}
                className="group flex items-center justify-between rounded-lg border-2 border-accent/40 bg-gradient-to-r from-accent/15 to-accent/5 px-4 py-4 transition hover:border-accent/70 hover:from-accent/25 hover:to-accent/15"
              >
                <div className="flex min-w-0 flex-1 items-center gap-3">
                  <span className="text-2xl">{getFileIcon(file.name)}</span>
                  <div className="min-w-0 flex-1">
                    <p className="break-words text-base font-bold text-white">
                      {file.name}
                    </p>
                    <p className="mt-1 text-xs text-gray-400">
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                  <span
                    className={`whitespace-nowrap rounded-full border px-3 py-1.5 text-sm font-bold ${getBadgeColor(file.name)}`}
                  >
                    {getFileTypeBadge(file.name)}
                  </span>
                </div>
                <button
                  type="button"
                  className="ml-4 rounded-md px-3 py-1.5 text-sm font-medium text-red-400 transition hover:bg-red-500/20 disabled:opacity-50"
                  disabled={disabled}
                  onClick={() => removeFile(index)}
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
