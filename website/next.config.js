/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  reactStrictMode: true,
  outputFileTracingRoot: path.join(__dirname, '..'),
  // `output: 'standalone'` is enabled ONLY for the Cloud Run container build
  // (NEXT_OUTPUT_STANDALONE=true), producing a self-contained `.next/standalone/
  // server.js` for the long-timeout chat service. The Vercel build leaves this
  // unset, so Vercel's deployment output is unchanged.
  ...(process.env.NEXT_OUTPUT_STANDALONE === 'true' ? { output: 'standalone' } : {}),
};

module.exports = nextConfig;
