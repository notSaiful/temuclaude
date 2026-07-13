# Hermes on Google Cloud Run

## Purpose

This service is an owner-operated, private Hermes runtime for TemuClaude. It
is **not** exposed directly to browsers and it is not a replacement for the
Vercel application. Vercel continues to authenticate users and store actions,
approvals, usage, and workspace data in Supabase.

## What this deploys

- Region: `asia-south1` (Mumbai).
- One Cloud Run service with a maximum of one concurrent instance.
- Scale-to-zero when idle; no local workspace persistence.
- Hermes' OpenAI-compatible API server on the Cloud Run `PORT` (8080), with
  `/health`, `/v1/chat/completions`, `/v1/runs`, approval, and SSE endpoints.
- A 15-minute request bound. Long-running work must checkpoint to Supabase and
  resume as a new task rather than depend on a single HTTP connection.

## Required controls before connecting it to the Playground

1. Keep Cloud Run authenticated; do not enable unauthenticated invocation.
2. Create a dedicated Vercel-to-Cloud-Run service identity. Never reuse a
   customer TemuClaude key or a Google owner credential.
3. Store provider credentials in Secret Manager, not in Docker, source, or
   browser environment variables.
4. Enable no Hermes shell, filesystem, browser, or network tool by default.
   Each capability needs a reviewed adapter plus a corresponding approved
   `temuclaude_project_actions` record.
5. Run generated or untrusted code only in E2B (or an equivalently isolated
   sandbox). Never run it in the Cloud Run Hermes container.
6. Configure the API server's mandatory bearer token as a Secret
   Manager-backed `API_SERVER_KEY`. Use a distinct restricted TemuClaude
   service key for the model provider; never use a customer API key.

## Deployment order

1. Enable Cloud Run, Cloud Build, Artifact Registry, Secret Manager, and
   Service Usage APIs in project `temuclaude-502009`.
2. Create a zero-spend budget alert before deploying.
3. Create `hermes-api-server-key` and `temuclaude-hermes-api-key`; grant the
   Cloud Run runtime service account access only to those two secrets. The
   manifest binds them as runtime variables. Never put their values in the
   image, Git, or Vercel.
4. Build the immutable image in Artifact Registry and deploy the manifest.
5. Verify `/health`, verify that `/v1/models` rejects a missing bearer token,
   then verify it succeeds with the service key.
6. Add the authenticated Vercel connector only after a successful isolated
   smoke test.

## Cost guardrails

The manifest has `minScale: 0`, `maxScale: 1`, one vCPU, 1 GiB memory, and a
15-minute request timeout. This is intentionally a low-traffic launch
configuration, not a multi-user worker pool. Configure Cloud Billing alerts
and stop the rollout if forecasted spend is non-zero without an explicit
decision to accept it.
