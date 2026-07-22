# TemuClaude Upgrade Plan: Durable Maximum-Quality Generation Jobs

## Objective

Allow Playground and API generation tasks to run for hours without being tied
to one browser, Vercel function, or Modal web request. A task must retain the
full quality pipeline (specialist panel, synthesis, artifact delivery,
isolated validation, QA, repair, and re-validation), survive worker retries,
and return its final artifact only when the configured acceptance policy is
satisfied.

### Measurable outcomes

- **Quality:** every `maximum_quality` code task completes the configured
  panel, artifact validation, and QA/repair policy before `completed`.
- **Reliability:** browser disconnects and HTTP deadlines do not cancel a job;
  a recoverable worker failure resumes from its most recently persisted stage.
- **Latency:** request acceptance is under 2 seconds; there is intentionally
  no customer-facing generation duration limit.
- **Safety/cost:** each model attempt remains bounded and auditable; jobs have
  an explicit owner-defined budget, retry policy, cancellation path, and a
  hard 24-hour checkpoint boundary per Modal function execution.

## Research Inputs

- Current service: `modal_app.py` executes the whole pipeline in an ASGI
  request, with an 85-second orchestration deadline, a 120-second function
  timeout, and an upstream gateway abort at 115 seconds.
- Current UI pattern: media jobs already persist a job record, return quickly,
  and poll job status (`supabase/migrations/202607130004_media_jobs.sql`,
  `website/lib/media-jobs.ts`, and `website/app/playground/page.tsx`). Reuse
  this ownership, authorization, and polling pattern; do not make the browser
  a Modal client.
- Modal: web-function HTTP requests have a 150-second limit, while Modal
  function executions can be configured up to 24 hours. Use a short web
  endpoint to submit work and a background function to run it.
- Architecture caveat: `ARCHITECTURE.md` describes Modal as dormant while the
  current TypeScript routes force Modal in some paths. Phase 0 must establish
  the actual deployed route before switching traffic.

## Target Architecture

```text
browser/API client
  -> Vercel accepts authenticated request and creates a Supabase job
  -> Vercel calls Modal /jobs/{id}/start (short, authenticated request)
  -> Modal starts background run_generation_job(job_id, lease_token)
  -> worker checkpoints each stage in Supabase and stores artifacts privately
  -> browser polls Vercel status endpoint (SSE can be added after polling)
  -> Vercel returns final result only from persisted completed job state
```

No web request waits for orchestration. A Modal function may run up to 24
hours; an unfinished job is checkpointed and resumed by a new function before
that boundary.

## Maximum-Quality Pipeline Contract

This profile is distinct from normal synchronous chat. It must not report
`completed` until every required stage below has a persisted success record.
An unavailable provider puts the job into `waiting_retry`; it must not silently
turn into a smaller model panel or a single-model response.

1. **Intake and immutable task snapshot** — persist the full conversation,
   artifact requirements, model registry version, prompt policy version,
   budget policy, and acceptance policy.
2. **Full specialist panel** — run and persist independent responses from GLM,
   DeepSeek, Kimi, MiniMax, Gemini, Luna, Kimi Frontier, and Grok. Each role
   retries independently with provider fallback; completed roles are never run
   again solely because another role failed.
3. **Synthesis and contradiction review** — GLM synthesizes all successful
   required roles; the frontier reviewer checks unresolved contradictions.
4. **Artifact implementation** — Kimi produces the complete requested
   self-contained deliverable. A truncated or non-runnable artifact is a
   validation failure, not a final answer.
5. **Deterministic validation** — extract/write the artifact, launch it in the
   isolated preview, collect console/runtime errors, verify document shape,
   and run task-specific interaction smoke tests.
6. **Independent quality gate** — Nemotron scores goal alignment, correctness,
   completeness, accessibility, security, and artifact quality. Persist the
   full score and actionable feedback.
7. **Repair loop** — when deterministic validation fails or QA is below the
   configured acceptance threshold, select the responsible repair specialist,
   create a new artifact revision, and repeat validation plus QA. Every
   revision is retained for comparison and rollback.
8. **Final acceptance and publication** — only a passing artifact/answer is
   marked `completed`; store the final revision, signed preview/download URL,
   model completion ledger, validation evidence, cost, and elapsed time.

Jobs can run for hours, but the process is not infinite: the owner can cancel
at any checkpoint, and an explicit job budget/retry policy requires an
operator-visible `needs_review` state rather than silently spending forever.

## Job Model and State Machine

Create `temuclaude_generation_jobs` and `temuclaude_generation_job_events`.

`generation_jobs` essential fields:

- `id` (`gen_<uuid>`), `user_id`, `request_kind` (`chat|artifact`), encrypted
  or access-controlled messages/input, selected quality profile, and snapshot
  of pipeline/model configuration.
- `status`: `queued`, `running`, `waiting_retry`, `validating`, `completed`,
  `failed`, `cancel_requested`, `cancelled`.
- `stage`: `panel`, `synthesis`, `artifact`, `sandbox_validation`, `qa`,
  `repair`, `finalizing`.
- `attempt`, `stage_attempt`, `lease_token`, `lease_expires_at`,
  `next_run_at`, `cancel_requested_at`, and `last_error_code`.
- `cost_limit_credits`, `cost_reserved`, `cost_settled`, model/token/cost
  telemetry, final answer/artifact reference, and timestamps.

`generation_job_events` is append-only: stage start/finish, model attempt,
retry reason, validation result, cost change, cancellation, and terminal
state. Never store provider secrets or raw sensitive provider error bodies.

Database functions must atomically:

1. reserve a job budget and enforce a per-user pending-job limit;
2. claim a queued/retryable job with a lease;
3. checkpoint only when the caller holds the matching lease;
4. settle/refund credits idempotently on terminal state;
5. request cancellation; and
6. release expired leases for safe resumption.

## Implementation Phases

### 0. Establish production truth and freeze the contract

- Verify which deployed routes currently reach Modal, Fly, or TypeScript
  orchestration; reconcile `ARCHITECTURE.md` with production configuration.
- Define one explicit `maximum_quality` profile. It is the only profile that
  can run indefinitely; existing synchronous Lite/normal routes retain their
  current contracts.
- Document a versioned pipeline snapshot so a resumed job uses the same policy
  unless an operator explicitly migrates it.
- Add feature flags: `DURABLE_JOBS_ENABLED`, `DURABLE_JOBS_SHADOW`, and
  `MAX_QUALITY_ASYNC_REQUIRED`.

### 1. Add durable storage and authenticated Vercel job APIs

- Add a Supabase migration following the existing media-job ownership and
  idempotent-credit conventions.
- Add `website/lib/generation-jobs.ts` for validation, creation, reads,
  lease-aware updates, cost accounting, and safe public DTOs.
- Add authenticated routes:
  - `POST /api/generation-jobs` creates and dispatches a job;
  - `GET /api/generation-jobs/:id` returns only the owning user's status;
  - `POST /api/generation-jobs/:id/cancel` requests cancellation;
  - `GET /v1/jobs/:id` provides the equivalent API-key-owned API surface.
- Return `202 Accepted` with `job_id`, status, and polling URL. Do not return
  generated content from this creation route.
- Apply pending-job and reserved-budget checks before dispatch; make repeated
  submissions idempotent through an idempotency key.

### 2. Convert Modal into submitter plus resumable background worker

- Keep a small authenticated FastAPI endpoint in `modal_app.py` that accepts
  only a job id and signed internal dispatch token. It validates the request,
  starts `run_generation_job.spawn(job_id, lease_token)`, and returns `202`.
- Implement `run_generation_job` as a non-web Modal function with a 24-hour
  timeout and explicit retry configuration. It loads state from Supabase,
  claims/renews its lease, and checkpoints after every completed stage and
  model call.
- Replace direct `complete_with_rescue()` use for maximum-quality jobs with a
  stage dispatcher that resumes at the first unfinished stage.
- Before the function's final safety window, checkpoint `waiting_retry` and
  spawn a successor function. This makes multi-hour work possible without
  crossing Modal's per-execution cap.
- A cancelled job stops before each provider call and between stages. Do not
  attempt to cancel a provider call that cannot safely be cancelled; record it
  and prevent later stages from running.

### 3. Preserve the full quality pipeline, but make it durable

- Persist individual panel responses as they arrive; retry only the missing
  role rather than repeating a successful panel.
- Persist synthesis, the generated HTML/game artifact, sandbox results, QA
  verdicts, repair candidates, and acceptance decision.
- Use deterministic artifact checks before LLM QA: complete HTML document,
  size/truncation checks, isolated preview launch, console/runtime errors,
  and required interaction smoke tests.
- Define explicit quality termination conditions: accepted score/validation,
  exhausted repair attempts, exhausted budget, user cancellation, or a
  non-retryable policy/security failure. “No deadline” must not mean an
  unbounded retry or cost loop.
- Store final artifacts in private Supabase Storage (or the existing approved
  artifact store); return signed URLs only to the job owner.

### 3a. Close the current maximum-quality gaps

- Replace the worker's current all-at-once `orchestrate()` call with durable
  stage handlers matching the pipeline contract above. A stage handler must
  read its prior checkpoint before calling a provider.
- Remove the fixed three-attempt terminal retry policy for `maximum_quality`.
  Instead, use per-role retry state and exponential backoff until the job's
  owner-configured budget/review policy is reached.
- Add a scheduled recovery dispatcher that claims expired leases and launches
  a successor worker. Before a worker's 24-hour Modal boundary, it must
  checkpoint, release/expire its lease, and dispatch that successor.
- Add `sandbox_validation` and `needs_review` states to the database and UI.
  The current worker must not mark an artifact completed before sandbox
  validation and the independent QA gate have persisted success.
- Add a cancellation check before and after every provider call, validation
  action, and repair revision.

### 4. Playground and API UX

- Replace the current long `/api/chat` wait for maximum-quality requests with
  `POST /api/generation-jobs`.
- Reuse the existing media polling UX initially: status every 5 seconds with
  exponential backoff, resume polling after refresh, and a visible Cancel
  action. Add SSE only after the polling path is reliable.
- Show real persisted stages: panel progress, artifact generation, sandbox
  validation, QA, repair, completed/failed/cancelled. Never present an
  incomplete artifact as final.
- Add API documentation for `202`, job status retrieval, cancellation, and
  final result retrieval. Preserve synchronous endpoint behavior for clients
  that have not opted into `maximum_quality` jobs.

### 5. Reliability, operations, and rollout

- Build a sweeper (scheduled Modal function or secured cron endpoint) that
  finds expired leases and re-dispatches retryable jobs exactly once per lease
  generation.
- Add dashboards/alerts for queued age, stage duration, retry rate, worker
  lease expiry, provider/model failure rate, cancellation rate, and cost per
  accepted artifact.
- Shadow mode: create/checkpoint jobs while the existing synchronous output is
  still authoritative; compare artifacts, quality results, cost, and failures.
- Canary to internal accounts, then a limited percentage of maximum-quality
  Playground traffic. Do not migrate all normal chat traffic initially.
- Update README, architecture docs, and public docs only after the durable
  route is live and verified.

## Exact Repository Touchpoints

- **Modal worker:** `modal_app.py` (or a new `modal_jobs.py` if splitting is
  cleaner); focused tests in `tests/test_modal_orchestration_reliability.py`
  plus new `tests/test_durable_generation_jobs.py`.
- **Database:** new migration under `supabase/migrations/`, modeled on
  `202607130004_media_jobs.sql`.
- **Vercel APIs:** new `website/app/api/generation-jobs/route.ts`,
  `website/app/api/generation-jobs/[jobId]/route.ts`, cancellation route, and
  API job-status route.
- **Website domain code:** new `website/lib/generation-jobs.ts`; adapt
  `website/app/api/chat/route.ts`, `website/app/v1/chat/completions/route.ts`,
  and `website/app/playground/page.tsx`.
- **Docs:** `ARCHITECTURE.md`, `README.md`, `website/app/docs/page.tsx`.

## Rollback Plan

- `DURABLE_JOBS_ENABLED=false` stops new job creation without deleting or
  corrupting existing jobs.
- Existing queued/running jobs remain readable and cancellable; an operator
  can pause dispatch by disabling the worker-dispatch flag.
- Revert the Playground/API routing only after pending durable jobs reach a
  terminal state or are explicitly cancelled/refunded.
- Automatically pause rollout if lease recovery fails, duplicate execution is
  observed, completion reliability regresses, or cost exceeds the configured
  job budget.

## Verification

```bash
PYTHONPATH=. pytest -q tests/test_durable_generation_jobs.py tests/test_modal_orchestration_reliability.py
python3 -m py_compile modal_app.py
cd website && npm run build
git diff --check
```

Integration checks:

1. submit a maximum-quality webpage job and close/reopen the browser;
2. verify the same job resumes status polling and completes;
3. simulate a role failure and confirm only that role retries;
4. simulate worker termination/lease expiry and confirm one successor resumes;
5. cancel at each stage and confirm no later stage runs and accounting settles;
6. validate the final HTML in the isolated preview; and
7. verify a non-maximum-quality request still uses its existing compatible
   endpoint behavior.

## Success Criteria

- No customer-facing request waits for the full orchestration.
- A maximum-quality job can span multiple Modal function executions and retain
  every completed stage.
- Exactly one worker owns a job stage at a time.
- Browser refresh/disconnect does not lose work.
- The final artifact meets deterministic validation and configured model-QA
  acceptance conditions, or the job reports a precise terminal reason.
- Per-job spend and retries remain bounded, visible, and cancellable.
