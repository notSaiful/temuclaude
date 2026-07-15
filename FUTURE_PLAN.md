# TemuClaude Future Plan

**Status:** Parked for future development. Do not implement the full PLG/CRO
program until the traction gate below is met.

**Decision:** Preserve the current visual identity. Until traction exists, make
only small correctness and measurement changes that are required to learn from
real visitors. Do not launch a broad redesign, guest-key platform, micro-tool
portfolio, programmatic SEO system, or ecosystem-integration campaign yet.

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

## Immediate priorities before traction

1. Keep the playground and API on one tested routing contract.
2. Measure answer quality, latency, reliability, and cost before changing a
   default model.
3. Make failures explicit and preserve a safe fallback path.
4. Keep credentials server-side and enforce authentication before paid work.
5. Publish only claims supported by reproducible tests.

These are maintenance and launch-readiness tasks, not the future redesign:

1. Make every public curl and SDK example match the live authentication and
   model contract.
2. Remove stale prices, dead paths, simulated statistics, and unsupported
   quality, cost, latency, uptime, privacy, or enterprise claims.
3. Add privacy-minimized first-party funnel counters without storing prompt or
   response content so traction can be measured.
4. Keep one reliable Playground path live and record whether users reach a
   successful response.
5. Interview early developers and record their actual use cases before building
   new acquisition surfaces.

## Traction gate

Re-open the future plan when at least one of these conditions is met:

- 500 qualified website visitors in a rolling 30-day period;
- 20 developers complete three successful requests within 24 hours;
- 5 developers return and use TemuClaude in a second week; or
- 5 founder-led developer interviews identify the same urgent use case and at
  least 2 participants ask to keep using the product.

The visitor threshold alone is not sufficient to justify the full build. Before
large distribution work, require evidence that some users reach value and want
to return.

## Future objective

Turn an anonymous visitor into a developer who completes three successful API
calls within five minutes, then make sharing, starter projects, and integrations
bring in the next developer.

Primary future metric: **Weekly Activated Developers**, defined as unique
developers who complete three successful API calls within 24 hours.

Supporting metrics:

- proof-to-test-key conversion;
- test-key-to-first-success conversion;
- first-to-third-request conversion;
- median and 95th-percentile time to first value;
- cost per activated developer;
- seven-day activated-developer retention;
- account-claim and free-to-paid conversion; and
- referral-assisted activations.

## Future Phase 1 — Shock-and-awe proof

Keep the cream/orange editorial design and replace unsupported simulated proof
with a reproducible benchmark module.

Proposed headline:

> Your AI stack overpays for easy work—and underchecks the hard work.

Proposed subheadline:

> TemuClaude is an OpenAI-compatible router that starts with efficient models,
> escalates when verification demands it, and returns one answer with the route,
> latency, usage, and cost exposed.

The above-the-fold proof should:

- render a signed recorded result immediately, without spending inference cost;
- cover JSON extraction, code repair, and exact-answer reasoning;
- disclose the baseline model and benchmark timestamp;
- show deterministic pass/fail checks, actual latency, and actual provider cost;
- link to raw prompts, evaluator code, results, and failure cases; and
- permit one constrained custom Lite request only after abuse and spend controls
  are verified.

Do not publish quantified superiority claims until a reproducible comparison has
at least 200 representative prompts, repeated runs where variance matters,
identical budgets, deterministic validators or blind judging, raw results, and
actual provider costs.

## Future Phase 2 — Zero-friction onboarding

Target flow:

```text
Landing proof
  -> copy a working curl
  -> receive a short-lived scoped test key
  -> complete the first request
  -> claim the key with GitHub or email OTP
  -> complete two more free requests
  -> upgrade or wait for allowance renewal
```

Delete or delay:

- mandatory signup before first value;
- name collection during activation;
- combined password and email-OTP signup;
- dashboard detours before the first successful call;
- paid-plan requirements for a short-lived test key;
- credit-card collection before value; and
- company, team, enterprise, and detailed use-case questions before activation.

Future test keys must be server-side records with hashed secrets, a short TTL,
three-request maximum, Lite-only scope, strict input/output limits, per-network
issuance limits, a daily global spend ceiling, and automatic abuse revocation.
They must not enable media, tools, projects, sandboxes, or unrestricted model
access.

Required kill switches:

- `GUEST_KEYS_ENABLED`;
- `LANDING_DEMO_ENABLED`;
- `GUEST_DAILY_BUDGET_USD`;
- `GUEST_MAX_REQUESTS`; and
- `GUEST_KEY_TTL_SECONDS`.

## Future Phase 3 — Developer experience and documentation

Replace the long mixed-purpose documentation page with:

```text
/docs
|- Quickstart
|- API Reference
|  |- Authentication
|  |- Chat Completions
|  |- Models
|  |- Streaming
|  |- Errors
|  `- Limits
|- SDKs
|  |- JavaScript and TypeScript
|  |- Python
|  |- Vercel AI SDK
|  `- LangChain
|- Guides
|  |- Migrate from OpenAI
|  |- Stream responses
|  `- JSON extraction
|- Examples
|- Benchmarks
|- Changelog
`- Status
```

Every featured snippet must have language tabs, copy and run controls, an
expected response, exact error guidance, and an automated production smoke test.
The first curl should explicitly include the API key, model, messages, and
streaming choice.

Before official provider integrations, publish and pass a compatibility matrix
for non-streaming, streaming, authentication errors, rate limits, cancellation,
empty upstream responses, model listing, tool calls, and structured output.
Unsupported OpenAI-compatible fields must be documented rather than silently
advertised.

## Future Phase 4 — Viral assets and distribution

Build only after activation is measurable:

1. **`temuclaude-json-contract-lab`** — an open-source JSON extraction tool
   with schema validation, route/cost visibility, an opt-in shareable result,
   and “Fork this tool” and “Use this endpoint” actions.
2. **`create-temuclaude-app`** — a Next.js and Vercel AI SDK starter with
   streaming, environment validation, errors, usage display, smoke tests,
   one-click deployment, and an honest removable attribution badge.
3. **`@temuclaude/proof-widget`** — a React/Web Component that displays a
   signed benchmark result with baseline, validator, latency, cost, timestamp,
   and a link to reproduce the test.

Distribution order:

1. founder-led usability sessions;
2. one reliable micro-tool;
3. a transparent Show HN and open-source release;
4. relevant Reddit communities with founder disclosure;
5. Product Hunt after activation is reliable;
6. 10-12 evidence-rich migration and use-case pages;
7. generic OpenAI-compatible integration guides;
8. a Vercel AI SDK community provider;
9. LangChain, LlamaIndex, Flowise, Langflow, and UI-client integrations only
   after the compatibility matrix passes; and
10. broader SEO only for page formats that demonstrate unique value.

Do not mass-generate thin comparison pages or send untested provider PRs. Every
technical marketing claim must link to data, code, configuration, and known
failures.

## Future implementation sequence

| Window | Deliverable | Promotion gate |
| --- | --- | --- |
| Days 1-2 | Claims, examples, pricing, and measurement corrections | Every displayed command is truthful |
| Days 3-7 | Recorded proof and constrained test-key foundation | Spend caps and abuse tests pass |
| Week 2 | Guest first value and post-value account claim | Median interactive TTFV below 10 seconds |
| Week 3 | Documentation information architecture and executable snippets | Snippets pass against production in CI |
| Week 4 | Self-serve checkout | Webhook, quota, cancellation, and recovery tests pass |
| Weeks 5-6 | JSON Contract Lab and starter template | Activation and unit economics are acceptable |
| Weeks 7-8 | Integration guides and first provider package | Compatibility matrix is green |
| After evidence | SEO expansion and DevRel | Each page or article contains unique measured value |

## Future rollback and cost controls

- Ship the proof module, test keys, onboarding flow, and checkout behind
  independent server-side flags.
- Preserve the current authenticated flow as the fallback until the replacement
  passes production smoke tests.
- Disable guest inference automatically when daily budget, abuse, latency, or
  failure thresholds are exceeded.
- Fall back to signed recorded proof rather than an unrestricted anonymous API.
- Never log prompt or response content for growth analytics.
- Fail closed when persistent storage, authentication, or quota enforcement is
  unavailable.

## Future verification

- Unit and contract tests for key issuance, TTL, scope, quotas, and revocation.
- End-to-end tests for anonymous proof, first request, account claim, API key,
  checkout, cancellation, and exhausted limits.
- CI execution of every public curl and SDK snippet.
- Reproducible benchmark packet with raw results and failure cases.
- TypeScript, production gates, production build, security scan, and live smoke
  verification before promotion.
- Privacy review before enabling funnel analytics or shareable artifacts.

## Change gate

A routing or model change may ship only when:

- focused unit and contract tests pass;
- the production website builds;
- unauthenticated requests are rejected;
- the configured provider accepts the selected model identifiers;
- a live smoke test returns a usable response; and
- cost, latency, and failure behavior have a documented rollback.

Completed designs and research notes belong in Git history or focused research
reports, not in additional roadmap files. `FUTURE_PLAN.md` is the single
canonical product plan.
