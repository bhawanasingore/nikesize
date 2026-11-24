import type { NextConfig } from "next";

// Vercel and local runs serve the page at /. PAGES_BASE_PATH is only for hosting under a sub-path
// (for example GitHub Pages at /<repo-name>); the perf scripts use it to test that layout.
const basePath = process.env.PAGES_BASE_PATH ?? "";

const nextConfig: NextConfig = {
  output: "export", // plain HTML/CSS/JS in ./out, no server needed
  basePath,
  trailingSlash: true,
};

export default nextConfig;
