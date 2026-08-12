/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Allow large audio data URIs in API response bodies
  experimental: {
    largePageDataBytes: 128 * 1000,
  },
};

module.exports = nextConfig;