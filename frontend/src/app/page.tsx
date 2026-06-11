"use client";

import { useState } from "react";
import { FileUpload } from "@/components/FileUpload";
import { ResponsePanel } from "@/components/ResponsePanel";
import { TracePanel } from "@/components/TracePanel";
import {
  type AgentResult,
  type ToolTraceEntry,
  isFollowUp,
  processAgent,
} from "@/lib/api";

export default function HomePage() {
  const [message, setMessage] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AgentResult | null>(null);

  const trace: ToolTraceEntry[] = result
    ? isFollowUp(result)
      ? result.trace
      : result.trace
    : [];

  const metadata = result && !isFollowUp(result) ? result.metadata : undefined;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);

    if (!message.trim() && files.length === 0) {
      setError("Enter a message or upload at least one file.");
      return;
    }

    setLoading(true);
    try {
      const data = await processAgent(message, files);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto min-h-screen max-w-4xl px-4 py-10">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">
          OmniAgent
        </h1>
        <p className="mt-2 text-gray-600">
          Upload files, describe your goal, and watch the agent plan and execute
          tools autonomously.
        </p>
      </header>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label
            htmlFor="message"
            className="mb-2 block text-sm font-medium text-gray-700"
          >
            Your instruction
          </label>
          <textarea
            id="message"
            rows={3}
            className="w-full rounded-lg border border-surface-border bg-white px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            placeholder="e.g. Summarize the YouTube video mentioned in this PDF"
            value={message}
            disabled={loading}
            onChange={(e) => setMessage(e.target.value)}
          />
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-gray-700">
            Files
          </label>
          <FileUpload
            files={files}
            onFilesChange={setFiles}
            disabled={loading}
          />
        </div>

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-accent px-6 py-2.5 text-sm font-medium text-white transition hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Processing…" : "Run Agent"}
        </button>
      </form>

      {result && (
        <section className="mt-10 space-y-6">
          {isFollowUp(result) ? (
            <ResponsePanel
              title="Follow-up Question"
              content={result.follow_up}
              variant="followup"
            />
          ) : (
            <ResponsePanel title="Response" content={result.response} />
          )}
          <TracePanel trace={trace} metadata={metadata} />
        </section>
      )}
    </main>
  );
}
