# TemuClaude roadmap

## Primary objective

Give each user one reliable answer while using the least expensive model that
can do the job. Add extra models or verification only when they are likely to
improve the result.

## Current system

- The playground and the OpenAI-compatible API require authentication.
- Requests are classified by task and difficulty.
- A small request normally uses one model.
- Hard or high-risk work may use specialists and an independent check.
- Usage is recorded only after a response completes.
- The playground chat service runs on Cloud Run with a 60-minute request limit.
- Public model and quality claims must match live provider data and measured
  results.

## Current priorities

1. Keep the playground and API on one tested routing contract.
2. Measure answer quality, latency, reliability, and cost before changing a
   default model.
3. Make failures explicit and preserve a safe fallback path.
4. Keep credentials server-side and enforce authentication before paid work.
5. Publish only claims supported by reproducible tests.

## Change gate

A routing or model change may ship only when:

- focused unit and contract tests pass;
- the production website builds;
- unauthenticated requests are rejected;
- the configured provider accepts the selected model identifiers;
- a live smoke test returns a usable response; and
- cost, latency, and failure behavior have a documented rollback.

Completed designs and research notes belong in Git history or focused research
reports, not in additional roadmap files. This is the only active product plan.
