import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",

  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: "http://localhost:54000/api/v1/:path*",
      },
    ];
  },
};

export default nextConfig;
