/** @type {import('next').NextConfig} */
const nextConfig = {
  outputFileTracingIncludes: {
    "/api/random": ["./data/**/*"],
  },
};

module.exports = nextConfig;