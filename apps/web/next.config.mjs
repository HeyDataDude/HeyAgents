/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  async rewrites() {
    const api = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
    return [
      // Proxy API calls so the browser can hit a same-origin path in dev.
      { source: "/proxy/:path*", destination: `${api}/:path*` },
    ];
  },
};

export default nextConfig;
