# TemuClaude Research Implementation Status

Generated: 2026-07-08

This file consolidates the research-to-implementation trail from the current upgrade run. It is intentionally practical: each research theme is mapped to code, website/GitHub-facing updates, verification, and next work.

## Implemented

| Research theme | Status | Implemented artifacts | Verification |
|---|---:|---|---|
| Frontier-style per-step orchestration | Implemented foundation | `src/step_telemetry.py`, `src/orchestrator.py` hook | `tests/test_step_telemetry.py` |
| State-aware routing / AgentPRM trace data | Implemented foundation | Step events with task, tier, step type, model, success, latency, tokens | `tests/test_step_telemetry.py` |
| Budget-aware sequential routing | Implemented foundation | Step dataset builder and route recommendations | `tests/test_step_telemetry.py`, `tests/test_step_model_routing.py` |
| Budget/progress/failure telemetry | Implemented foundation | `initial_budget`, `remaining_budget`, `budget_spent`, `progress_delta`, `uncertainty`, `failure_label` | `tests/test_step_telemetry.py` |
| Runtime budget signal wiring | Implemented | `build_runtime_step_metadata(...)`, orchestrator telemetry metadata wiring | `tests/test_step_telemetry.py`, py_compile |
| Step-aware model selection | Implemented first pass | `get_model_for_step(...)`, hard-tier search/verification/consistency/QA model selection | `tests/test_step_model_routing.py`, py_compile |
| Structured PRM labels | Implemented first pass | `PRMVerdict`, `_score_step_structured(...)`, primary/peer label parsing in `src/reasoning_tree.py` | `tests/test_v3_breakthroughs.py`, `tests/test_v3_upgrades.py` |
| ParetoBandit-style recency decay | Implemented first pass | `recency_half_life_days` in `get_step_route_recommendations(...)` with stale-evidence confidence penalty | `tests/test_step_telemetry.py` |
| Active budget controller | Implemented shadow foundation | `src/budget_controller.py`, controller recommendation fields in step telemetry | `tests/test_budget_controller.py`, `tests/test_step_telemetry.py` |
| Benchmark-promotion gate | Implemented foundation | `src/benchmark_promotion.py` quality/cost/latency/failure gate | `tests/test_budget_controller.py` |
| Website/GitHub sync | Implemented first pass | `README.md`, `website/app/models/page.tsx`, `website/app/docs/page.tsx` | Website build/type check pending in this run |

## Partially Implemented

| Research theme | Current state | Remaining work |
|---|---|---|
| ParetoBandit-style non-stationary routing | Recency decay is implemented | Add forced exploration and model registry versioning |
| SeqRoute-style remaining-budget controller | Shadow action policy implemented; runtime gates still off | Enable only after benchmark-promotion gate passes |
| AgentPRM / progress reward | Heuristic `progress_delta` exists | Train or prompt a real progress critic over traces |
| Early-abort / escalation | Shadow controller now recommends stop/escalate/debate actions | Add runtime gate behind config flag after eval |
| Cost-aware local benchmark | Promotion gate exists | Build repo-local benchmark packet with quality, cost, latency, retries |
| GEPA trace optimization | Existing `src/gepa.py` remains simplified | Replace first-valid-prompt selection with trace reflection + Pareto frontier |
| Structured PRM labels | Implemented first pass | Next: feed labels into runtime route/escalation decisions |

## Not Yet Implemented

| Research theme | Why not yet | Next safe step |
|---|---|---|
| Full topology router | Needs more telemetry and eval guardrails; controller shadow labels now exist | Train a baseline classifier over `get_step_dataset()` |
| Provider usage-based token/cost accounting | Current providers do not consistently expose usage in this path | Capture usage metadata from OpenRouter responses where available |
| Tool-call and wall-clock budgets | Token budget is currently the main budget signal | Add `tool_call_budget`, `verifier_budget`, `wall_clock_budget` fields |
| Automatic model-pool replacement | Needs live benchmark guardrail to avoid regressions | Add staged model candidates plus benchmark-promotion gate |
| Playground orchestration telemetry UI | Backend telemetry exists | Expose step-router metadata in API response shape first |

## Current Model/Router Direction

Default role assignments remain conservative:

- Orchestrator/aggregator: `glm-5.2`
- Search/reasoning policy: `deepseek-v4-pro`
- Math/coding code-verification generator: `deepseek-v4-pro`
- QA/PRM verifier: `nemotron-3-ultra`
- Creative/generation: `minimax-m3`
- Repair/critic: `mistral-large-3`
- Long-context retrieval: `kimi-k2.6`
- Formal verification: local `z3`

The step router can override these only when telemetry has enough observations and the observed utility is better.

## Verification Commands

```bash
pytest -q tests/test_step_telemetry.py tests/test_step_model_routing.py
python3 -m py_compile src/step_telemetry.py src/adaptive.py src/orchestrator.py
cd website && npm run build
```

## Next Implementation Priority

1. Run the focused verification commands above.
2. Feed step-router/controller metadata into playground/API orchestration output.
3. Run benchmark-promotion gate on a local eval packet before enabling runtime controller gates.
4. Replace simplified GEPA with trace-based prompt/policy evolution.
5. Add controlled exploration for new candidate models.
