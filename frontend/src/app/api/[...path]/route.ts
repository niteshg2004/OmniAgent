/**
 * Runtime proxy: forwards /api/* requests to the FastAPI backend.
 * BACKEND_URL is read at request time (runtime), so it works correctly
 * with Render's fromService environment variable injection.
 */

import { type NextRequest, NextResponse } from "next/server";

const rawBackend =
  process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

/** Ensure the backend URL always has a protocol prefix. */
const BACKEND_BASE = rawBackend.startsWith("http")
  ? rawBackend.replace(/\/$/, "")
  : `https://${rawBackend.replace(/\/$/, "")}`;

async function handler(
  req: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const { path } = await params;
  const targetUrl = `${BACKEND_BASE}/api/${path.join("/")}${req.nextUrl.search}`;

  // Forward only necessary headers
  const forwardHeaders = new Headers();
  const contentType = req.headers.get("content-type");
  if (contentType) forwardHeaders.set("content-type", contentType);

  const upstream = await fetch(targetUrl, {
    method: req.method,
    headers: forwardHeaders,
    body:
      req.method !== "GET" && req.method !== "HEAD" ? req.body : undefined,
    // @ts-expect-error — duplex is required for streaming bodies
    duplex: "half",
  });

  const resHeaders = new Headers();
  upstream.headers.forEach((v, k) => resHeaders.set(k, v));

  return new NextResponse(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: resHeaders,
  });
}

export const GET = handler;
export const POST = handler;
export const PUT = handler;
export const PATCH = handler;
export const DELETE = handler;
