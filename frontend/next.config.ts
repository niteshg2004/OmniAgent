import type { NextConfig } from "next";

/** Backend URL used by Next.js server-side rewrites (not exposed to the browser). */
const backendHost = process.env.BACKEND_HOST ?? process.env.BACKEND_URL ?? "127.0.0.1:8000";
const backendUrl = backendHost.startsWith("http")
  ? backendHost
  : backendHost.includes(":")
    ? `http://${backendHost}`
    : `http://${backendHost}:8000`;

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
