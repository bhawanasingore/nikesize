import type { NextConfig } from "next";

// On GitHub Pages the site lives under /<repo-name>, so the deploy workflow
// sets PAGES_BASE_PATH. Locally it's empty and the page runs at /.
const basePath = process.env.PAGES_BASE_PATH ?? "";

const nextConfig: NextConfig = {
  output: "export", // plain HTML/CSS/JS in ./out, no server needed
  basePath,
  trailingSlash: true,
};

export default nextConfig;
