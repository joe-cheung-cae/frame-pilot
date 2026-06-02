import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  distDir: process.env.FRAMEPILOT_NEXT_DIST_DIR ?? ".next",
  outputFileTracingRoot: __dirname,
};

export default nextConfig;
