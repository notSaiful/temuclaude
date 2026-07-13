# Persistent Hermes on Render

This service is the full Hermes dashboard: sessions, memory, workspace files,
terminal, Git tools, MCP configuration, skills, schedules, and messaging.
It is deliberately separate from TemuClaude's public OpenAI-compatible API.

## Why it is separate

The Playground's **Agent Mode** uses OpenRouter inside the Vercel web app for
safe workspace analysis and approval-aware plans. The upstream Hermes dashboard
is a long-running authenticated tool service; it does not expose
`/v1/chat/completions`. Pointing the Playground's gateway variable at it would
therefore break Agent Mode. Keep `HERMES_RUNTIME=openrouter` in Vercel.

## Cost and operating choice

Use Render Starter with a 1 GB disk for this single-owner service. Render's
free web service sleeps after inactivity and cannot host a persistent disk, so
it cannot preserve Hermes memory or sessions. Starter compute is currently
$7/month and the 1 GB disk is billed separately at $0.25/GB/month. This is a
small private-agent deployment, not a multi-user execution cluster.

## Deploy

1. Push the repository changes to the GitHub repository connected to Render.
2. In Render, select **New +** → **Blueprint**, select the repository, then
   choose `services/hermes/render.yaml`.
3. When Render asks for secrets, supply:
   - `OPENROUTER_API_KEY`: the existing server-side OpenRouter key.
   - `HERMES_DASHBOARD_BASIC_AUTH_USERNAME`: an owner-only username.
   - `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD`: a new long password used only for
     Hermes. Do not reuse the TemuClaude login password.
   - `HERMES_DASHBOARD_PUBLIC_URL`: the HTTPS `onrender.com` URL assigned to
     the service after its first deploy. Save this variable and deploy once
     more so Hermes can set secure cookies correctly.
4. Keep the generated `HERMES_DASHBOARD_BASIC_AUTH_SECRET`; it signs dashboard
   sessions and must remain stable across deploys.
5. Open the Render service URL. The Hermes login page must appear before any
   dashboard page. Sign in with the credentials from step 3.

## Required verification

1. Render Events shows a successful deploy and the health check is passing.
2. Visiting the service URL while signed out shows the login page, not the
   dashboard.
3. After sign-in, create a test session, add a harmless note to memory, then
   redeploy. Confirm the session and note remain. This verifies the `/opt/data`
   persistent disk.
4. In the dashboard, confirm the configured model is an OpenRouter model and
   run a harmless prompt such as “Reply only with Hermes is ready.”
5. Do not enable unattended command execution. Hermes command, network, Git,
   credential, and deployment actions should continue to require approval.

## Security boundaries

- The service must remain owner-authenticated. Never set an insecure/public
  dashboard mode.
- The disk contains conversation history, tool configuration, and possibly
  credentials. Do not share its service URL or login credentials.
- This first service is a single owner/admin Hermes instance. It is not safe to
  give every TemuClaude customer shared terminal or repository access. A later
  multi-user integration needs per-user isolated workspaces and SSO before it
  can expose execution controls inside the public Playground.
- Rotate the OpenRouter key if it has ever been committed or displayed.
