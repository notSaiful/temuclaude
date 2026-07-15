# TemuClaude website — Next.js standalone build for Cloud Run.
#
# The chat route (/api/chat) runs here under Cloud Run's long request timeout
# (set at deploy time via `gcloud run deploy --timeout=3600`) so hard
# orchestration runs that exceed Vercel's 300s function ceiling can finish.
# The Vercel playground calls this service cross-origin with a bearer Supabase
# access token; CORS is handled in the route itself. Only /api/chat is used
# cross-origin — the rest of the app is bundled but dormant here.
#
# Build context: the website/ directory  (gcloud run deploy --source website).
# .dockerignore excludes the local (darwin) node_modules so the linux image
# gets a fresh `npm ci` install.

FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app
ENV NEXT_OUTPUT_STANDALONE=true
ENV NEXT_TELEMETRY_DISABLED=1
# Build-time public vars only. Runtime secrets (OPENROUTER_API_KEY, Supabase
# keys) are injected at deploy time and read by the server at runtime.
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
# Cloud Run injects PORT; the standalone server listens on it.
ENV PORT=8080
ENV HOSTNAME=0.0.0.0
# Standalone server + traced node_modules, plus static assets + public.
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 8080
CMD ["node", "server.js"]
