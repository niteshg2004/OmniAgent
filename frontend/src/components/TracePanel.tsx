import type { ToolTraceEntry } from "@/lib/api";
import { useState } from "react";

interface TracePanelProps {
  trace: ToolTraceEntry[];
  metadata?: Record<string, unknown>;
}

function statusColor(status: ToolTraceEntry["status"]): string {
  switch (status) {
    case "success":
      return "text-green-400 bg-green-400/10 border-green-400/30";
    case "failed":
      return "text-red-400 bg-red-400/10 border-red-400/30";
    case "skipped":
      return "text-yellow-400 bg-yellow-400/10 border-yellow-400/30";
    default:
      return "text-gray-400 bg-gray-400/10 border-gray-400/30";
  }
}

function statusBgColor(status: ToolTraceEntry["status"]): string {
  switch (status) {
    case "success":
      return "bg-green-500/40";
    case "failed":
      return "bg-red-500/40";
    case "skipped":
      return "bg-yellow-500/40";
    default:
      return "bg-gray-500/40";
  }
}

export function TracePanel({ trace, metadata }: TracePanelProps) {
  const [viewMode, setViewMode] = useState<"list" | "timeline">("list");

  if (trace.length === 0) {
    return (
      <div className="rounded-lg border border-surface-border bg-gray-50 p-4 text-sm text-gray-600">
        No tool execution yet.
      </div>
    );
  }

  const maxDuration = Math.max(...trace.map((e) => e.duration_ms || 0), 1);

  return (
    <div className="rounded-lg border border-surface-border bg-gray-50">
      <div className="flex items-center justify-between border-b border-surface-border bg-white px-4 py-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-700">
          Execution Trace
        </h2>
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode("list")}
            className={`px-2 py-1 text-xs font-medium rounded transition ${
              viewMode === "list"
                ? "bg-blue-500/20 text-blue-600 border border-blue-400/50"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            List
          </button>
          <button
            onClick={() => setViewMode("timeline")}
            className={`px-2 py-1 text-xs font-medium rounded transition ${
              viewMode === "timeline"
                ? "bg-blue-500/20 text-blue-600 border border-blue-400/50"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Timeline
          </button>
        </div>
      </div>

      <div className="p-4">
        {viewMode === "list" ? (
          // List View
          <ol className="space-y-2">
            {trace.map((entry) => (
              <li
                key={entry.step}
                className="flex items-start gap-3 rounded-md bg-white px-3 py-2 text-sm border"
              >
                <span className="font-mono text-gray-500 min-w-6">{entry.step}</span>
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-gray-900">{entry.tool}</span>
                    <span
                      className={`rounded px-2 py-0.5 text-xs font-medium border ${statusColor(entry.status)}`}
                    >
                      {entry.status}
                    </span>
                    {entry.duration_ms != null && (
                      <span className="text-xs text-gray-500">
                        {entry.duration_ms.toFixed(0)}ms
                      </span>
                    )}
                  </div>
                  {entry.error && (
                    <p className="mt-1 text-xs text-red-400">{entry.error}</p>
                  )}
                </div>
              </li>
            ))}
          </ol>
        ) : (
          // Timeline View
          <div className="space-y-4">
            {trace.map((entry) => (
              <div key={entry.step} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                      entry.status === "success"
                        ? "bg-green-500"
                        : entry.status === "failed"
                          ? "bg-red-500"
                          : "bg-gray-400"
                    }`}
                  >
                    {entry.step}
                  </div>
                  {trace[trace.length - 1].step !== entry.step && (
                    <div className="w-0.5 h-8 bg-gray-300 mt-2"></div>
                  )}
                </div>
                <div className="flex-1 pt-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-medium text-gray-900">{entry.tool}</span>
                    <span
                      className={`rounded px-2 py-0.5 text-xs font-medium border ${statusColor(entry.status)}`}
                    >
                      {entry.status}
                    </span>
                  </div>

                  {/* Duration Bar */}
                  {entry.duration_ms != null && (
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-6 overflow-hidden">
                        <div
                          className={`h-full transition-all ${statusBgColor(entry.status)} flex items-center px-2 text-xs font-mono text-gray-700`}
                          style={{
                            width: `${(entry.duration_ms / maxDuration) * 100}%`,
                            minWidth:
                              (entry.duration_ms / maxDuration) * 100 > 15
                                ? "auto"
                                : "auto",
                          }}
                        >
                          {entry.duration_ms > 100 && (
                            <span>{entry.duration_ms.toFixed(0)}ms</span>
                          )}
                        </div>
                      </div>
                      {entry.duration_ms <= 100 && (
                        <span className="text-xs text-gray-500 w-12 text-right">
                          {entry.duration_ms.toFixed(0)}ms
                        </span>
                      )}
                    </div>
                  )}

                  {entry.error && (
                    <p className="mt-2 text-xs text-red-500 bg-red-50 border border-red-200 rounded px-2 py-1">
                      {entry.error}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Cost Information */}
        {metadata?.cost_usd && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex items-center justify-between rounded-md bg-blue-50 px-3 py-2 text-sm">
              <span className="text-gray-700">Total API Cost:</span>
              <span className="font-mono font-semibold text-blue-600">
                ${(metadata.cost_usd as number).toFixed(6)}
              </span>
            </div>
            {metadata.cost_breakdown &&
              typeof metadata.cost_breakdown === "object" && (
                <div className="mt-2 space-y-1 text-xs">
                  {Object.entries(metadata.cost_breakdown).map(([tool, cost]) => (
                    <div key={tool} className="flex justify-between text-gray-600">
                      <span>{tool}:</span>
                      <span className="font-mono">
                        ${(cost as number).toFixed(6)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
          </div>
        )}
      </div>
    </div>
  );
}
