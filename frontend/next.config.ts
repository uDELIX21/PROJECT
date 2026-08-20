import type { NextConfig } from "next";

// All API calls go through relative /api/* paths — the dev server (and nginx in
// prod) proxies them to the FastAPI backend. The browser never needs to know the
// backend host (design §13; preview-host friendly).
const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${BACKEND_URL}/api/:path*` }];
  },
  allowedDevOrigins: ["*.e2b.app", "*.arena.gg", "localhost", "127.0.0.1"],
  poweredByHeader: false,
};

export default nextConfig;
