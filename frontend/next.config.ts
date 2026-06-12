import type { NextConfig } from "next";

/** Backend URL used by Next.js server-side rewrites (not exposed to the browser).
 * On Render, BACKEND_URL comes from fromService.property=hostport (e.g. "hostname:443").
 * Locally it is the full URL (e.g. "http://127.0.0.1:8000").
 */
const rawBackend = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";
const backendUrl = rawBackend.startsWith("http")
  ? rawBackend
  : `https://${rawBackend}`;

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
