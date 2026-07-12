/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
  // Audit route is gated at runtime via NEXT_PUBLIC_LAWTRACE_AUDIT.
};

module.exports = nextConfig;
