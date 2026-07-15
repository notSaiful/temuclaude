/** @type {import('next').NextConfig} */
const path = require('path');

const isStandalone = process.env.NEXT_OUTPUT_STANDALONE === 'true';

const nextConfig = {
  reactStrictMode: true,
  // For the Cloud Run standalone build, trace from the website dir itself so
  // the standalone output is flat (`.next/standalone/server.js` + traced
  // node_modules) and the container's `node server.js` finds the entry. For
  // Vercel, trace from the repo root (unchanged from before this change).
  outputFileTracingRoot: isStandalone ? __dirname : path.join(__dirname, '..'),
  // `output: 'standalone'` is enabled ONLY for the Cloud Run container build
  // (NEXT_OUTPUT_STANDALONE=true), producing a self-contained `.next/standalone/
  // server.js` for the long-timeout chat service. The Vercel build leaves this
  // unset, so Vercel's deployment output is unchanged.
  ...(isStandalone ? { output: 'standalone' } : {}),
};

module.exports = nextConfig;
