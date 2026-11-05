import type { NextConfig } from "next";

// Static export: the whole app is plain files (HTML, JS, JSON), so it can be
// hosted on Cloudflare Pages with no server and cached for offline reading.
const config: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  reactStrictMode: true,
};

export default config;
