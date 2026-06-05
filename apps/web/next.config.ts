import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  distDir: process.env.FRAMEPILOT_NEXT_DIST_DIR ?? ".next",
  outputFileTracingRoot: __dirname,
  allowedDevOrigins: ["127.0.0.1"],
};

export default nextConfig;
