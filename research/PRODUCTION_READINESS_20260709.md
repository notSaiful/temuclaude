# TemuClaude Production Readiness Hardening — 2026-07-09

## Objective

Move TemuClaude from "live prototype" toward production-safe launch by closing the highest-risk audit blockers:

- successful API responses with empty assistant content
- silent production fallback to ephemeral `/tmp` persistence
- missing repeatable production smoke gates
- deployment hygiene warning from ambiguous Next.js output tracing root

## Implemented Guardrails

1. `/v1/chat/completions` now validates assistant content before returning success.
   - Modal responses with empty content fall back to the in-process pipeline unless Modal is required.
   - In-process orchestration runs a final rescue pass through conservative fallback models.
   - If all paths return empty content, the API returns `503` instead of a fake `200`.

2. Production persistence now fails closed when Supabase admin credentials are missing.
   - JSON file storage remains available for local/dev.
   - Production can use ephemeral storage only when `ALLOW_EPHEMERAL_DB=true` is explicitly set.

3. `npm run production:gates` was added under `website/`.
   - Static guardrails verify the source still contains the API and DB fail-closed checks.
   - Optional live smoke test runs when `TEMUCLAUDE_SMOKE_URL` and `TEMUCLAUDE_SMOKE_KEY` are set.

4. Next.js output tracing root is explicit.
   - This prevents build tracing from selecting a parent workspace because of unrelated lockfiles.

## Required Production Environment

Before paid users are admitted, Vercel production must have:

- `OPENROUTER_API_KEY`
- `TEMUCLAUDE_MASTER_KEY`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `SUPABASE_SECRET_KEY` or `SUPABASE_SERVICE_ROLE_KEY`
- `ALLOW_EPHEMERAL_DB=false`
- Razorpay live keys and plan IDs for paid plans

## Verification Checklist

```bash
PYTHONPATH=. pytest -q
cd website && npm run production:gates
cd website && npm run build
TEMUCLAUDE_SMOKE_URL=http://localhost:3001 TEMUCLAUDE_SMOKE_KEY=$TEMUCLAUDE_MASTER_KEY npm run production:gates
```

## Launch Gate

TemuClaude should not accept general paid API traffic until:

- authenticated `/v1/chat/completions` returns non-empty content in production
- Supabase-backed API key creation, validation, usage increment, and quota enforcement are verified
- payment webhook verification is exercised with Razorpay test/live events
- benchmark evidence supports the exact public quality/cost claims
