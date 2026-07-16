# Quality-First Research Alignment Audit

**Date:** 2026-07-16
**Scope:** Python orchestration, FastAPI gateway, Vercel Playground gateway,
Vercel OpenAI-compatible gateway, research plans, benchmark evidence.

## Governing policy

1. **Primary objective:** outperform a single frontier-model response on
   specifically benchmarked, verifiable task classes.
2. **Secondary objective:** reduce cost only when the same benchmark packet
   shows no material quality or reliability regression.
3. **Product rule:** Pro must not silently downgrade to a low-cost worker;
   Lite and `max_savings` are explicit, labelled cost-bounded modes.
4. **Truthfulness rule:** a technique is not a customer-facing capability until
   the gateway a customer uses invokes it and an evaluation has measured it.

## Evidence reviewed

| Artifact | What it establishes | Limitation |
|---|---|---|
| `PLAN-v3-final.md` | Correctly limits superiority claims to verifiable tasks and rejects broad unmeasured frontier claims. | It is a plan, not an evaluation result. |
| `PLAN-v6-FINAL.md` | Describes a richer panel/fusion ambition. | Several stated wins are projections, not measurements. |
| `research/benchmark_results_real.json` | A 20-item internal sample where the recorded MoA result is 20/20. | It is too small and lacks a matched frontier baseline; it cannot substantiate a frontier-beating claim. |
| `research/model_benchmark_results.json` | Basic model availability/arithmetic probes. | Repeatedly evaluates one arithmetic answer; it is not a capability benchmark. |
| `ARCHITECTURE.md` | Correctly identifies independent Python and TypeScript production paths. | The duplicated paths can drift without shared conformance tests. |

## Implementation alignment

| Research mechanism | Python/FastAPI | Playground (`/api/chat`) | Public API (`/v1/chat/completions`) | Status |
|---|---|---|---|---|
| Quality-first default | Every configured frontier and specialist role joins Pro fusion | Full panel for every nontrivial Pro request; quality code workflow | Full panel for every nontrivial Pro request; GLM floor only for trivial prompts | Implemented; needs live eval |
| Evidence-based role prompts | Distinct prompt per GLM/DeepSeek/Kimi/MiniMax/Gemini/Luna/Sol/Grok/Nemotron capability | Same distinct role matrix | Same distinct role matrix | Implemented; conformance-tested |
| Lite multi-stage quality | Two allowlisted drafts, synthesis, independent verification | Two allowlisted drafts, Qwen synthesis, Nemotron verification/correction | Same bounded Lite pipeline | Implemented; needs live eval |
| Parallel specialist work | `asyncio.gather` in fusion | `Promise.allSettled` panel and parallel code plan/draft/review | `Promise.all` on hard panel | Implemented |
| Aggregation | Dynamic task aggregator | GLM structured fusion | GLM aggregation | Implemented |
| Independent quality gate | QA/PRM pathways | Nemotron LLM-as-judge | Nemotron LLM-as-judge | Implemented; an LLM judge is not ground truth |
| Tool-based code verification | Available in Python only | No general sandbox execution | No general sandbox execution | Gap for website/API users |
| Z3/SMT verification | Python only | Not live | Not live | Gap for website/API users |
| Web-grounded factual verification | Not wired by default | Web search for selected tasks | Not present | Gateway inconsistency |
| Adaptive controller/promotion | Shadow recommendation only | Not shared | Not shared | Not a runtime quality gate |
| Frontier escalation | Credential/config gated | Conditional | Conditional | Availability and quality must be measured |

## Corrections made in this change

- Python `Temuclaude.complete()` now defaults to `max_quality`; legacy
  `balanced` is quality-first for compatibility. `max_savings` remains explicit.
- Python Pro fusion expands from three roles to every configured frontier and
  complementary specialist. Unavailable direct providers safely resolve to
  strong in-pool routes and are deduplicated.
- The FastAPI contract exposes `budget_profile` and securely forwards it
  through the security wrapper.
- Playground code generation now performs parallel architecture planning,
  implementation drafting, product/UX review, synthesis, independent review,
  and conditional Grok repair.
- Playground Pro short answers use GLM rather than DeepSeek Flash; medium work
  receives the quality panel.
- The public OpenAI-compatible API treats code generation as hard work, removes
  its direct-code shortcut, promotes every medium request to the full quality
  pipeline, and uses GLM—not Flash—for the Pro trivial floor.
- Both Pro gateways invoke frontier, reasoning, creative/long-context,
  multimodal, coding-agent, orchestration, and verification roles in parallel.
- OpenRouter Pro calls prefer high-throughput BF16/FP16/FP8 endpoints instead
  of the gateway's default price-weighted provider ordering.
- If no strict-precision endpoint is currently routable, the connection layer
  retries the exact same approved model without the precision filter before
  moving through explicit model/provider fallbacks. Authentication and
  permission errors are surfaced immediately rather than retried blindly.
- Live endpoint auditing found that GPT-5.6 Luna and Sol do not advertise the
  `temperature` parameter. With `require_parameters=true`, sending it excluded
  every healthy endpoint. Both Python and TypeScript adapters now omit
  temperature for fixed-sampling GPT-5.6 routes; all nine Pro role IDs returned
  HTTP 200 with exact model identity in the post-fix OpenRouter audit.
- Regression contracts cover the policy, panel composition, gateway forwarding,
  and code-generation path.
- GLM remains the planning/project-engineering/synthesis lead. Kimi is live for
  coding-driven UI/UX, MiniMax for multimodal/creative/long-context review,
  Gemini for visual UI/accessibility, Luna for a fast independent GPT-family
  proposal, Sol for frontier adjudication, Grok for repair, DeepSeek for the
  hard technical core, and Nemotron for independent verification.
- Nontrivial Lite requests no longer stop after one cheap draft: both gateways
  run complementary Lite drafts concurrently, synthesize them, and verify the
  result inside the Lite allowlist.
- Playground requests such as “create webpage …” are classified as hard code
  artifacts, not trivial creative prompts. If the Pro concise-response floor
  receives an empty provider message, it escalates to the full quality panel
  instead of exposing the transport error to the user.

## Required work before any “beats frontier” claim

1. Create one versioned benchmark packet per supported claim: coding with real
   tests, math with exact checking, source-grounded research with citation
   checks, and long-context retrieval with hidden needles.
2. Run the *same prompts, tools, token ceilings, and timeout budget* against
   TemuClaude Pro and named frontier baselines. Record model revisions,
   provider, prompt hash, samples, failures, cost, and latency.
3. Use tool outcomes or blind human evaluation where possible; do not promote
   an LLM-as-judge score as proof by itself.
4. Require a predeclared promotion threshold and confidence interval. The
   existing promotion gate now blocks any measured quality drop; benchmark
   packets still need statistically meaningful provider-backed samples.
5. Make the public API and Playground call one shared orchestration service, or
   add shared conformance tests that prove equivalent routing/verification.

## Prohibited claims until then

- “beats frontier models” without naming the task class, baseline, sample size,
  metric, and date;
- tool verification, Z3, MCTS, or self-play as live Vercel features;
- universal frontier replacement or general-intelligence superiority;
- cost savings that are obtained by a quality regression or by an unlabelled
  Pro downgrade.
