export interface ToolTraceEntry {
  step: number;
  tool: string;
  status: "success" | "failed" | "skipped";
  error?: string;
  duration_ms?: number;
}

export interface AgentResponse {
  response: string;
  trace: ToolTraceEntry[];
  metadata?: Record<string, unknown>;
}

export interface FollowUpResponse {
  follow_up: string;
  trace: ToolTraceEntry[];
}

export type AgentResult = AgentResponse | FollowUpResponse;

export function isFollowUp(result: AgentResult): result is FollowUpResponse {
  return "follow_up" in result;
}

/**
 * API base URL for browser requests.
 * Empty string = same origin; Next.js rewrites /api/* to the backend (see next.config.ts).
 * Set NEXT_PUBLIC_API_URL only when the API is on a separate public host.
 */
function getApiBase(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (configured) {
    return configured.replace(/\/$/, "");
  }
  return "";
}

export async function processAgent(
  message: string,
  files: File[],
): Promise<AgentResult> {
  const formData = new FormData();

  if (message.trim()) {
    formData.append("message", message.trim());
  }

  for (const file of files) {
    formData.append("files", file);
  }

  const url = `${getApiBase()}/api/v1/agent`;

  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      body: formData,
    });
  } catch {
    throw new Error(
      "Cannot reach the backend API. Ensure the backend is running " +
        "(uvicorn app.main:app --reload --host 0.0.0.0 --port 8000) " +
        "and restart the frontend after any config changes.",
    );
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      (error as { detail?: string }).detail ??
        `Request failed with status ${response.status}`,
    );
  }

  return response.json() as Promise<AgentResult>;
}
