import type { NextConfig } from "next";
import { fileURLToPath } from "node:url";

const nextConfig: NextConfig = {
  turbopack: {
    root: fileURLToPath(new URL(".", import.meta.url)),
  },
  allowedDevOrigins: ["192.168.0.115", "192.168.0.103"],
};

export default nextConfig;
