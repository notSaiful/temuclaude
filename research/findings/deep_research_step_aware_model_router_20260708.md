# Deep Research: Step-Aware Model Router Upgrade for TemuClaude

Generated: 2026-07-08

## Executive Finding

The model pool should not be static. The latest routing literature and current OpenRouter signals point to the same architecture: keep strong role defaults, collect state-action-outcome telemetry, and let the system switch models for specific orchestration steps only when there is enough evidence.

This pass implements that bridge. TemuClaude now has a step-aware model selector that can use per-step telemetry recommendations for search, verification, consistency, QA gates, and other orchestration states. When evidence is sparse, it falls back to role-aware defaults.

## Current Model Signals

OpenRouter's June 2026 open-weight analysis reports GLM-5.2 as the top open-weight model on the Artificial Analysis Intelligence Index, ahead of Nemotron 3 Ultra, MiniMax M3, DeepSeek V4 Pro, and Kimi K2.6. The same analysis frames GLM-5.2 as near frontier-class for agentic workflows at much lower cost.

DeepSeek V4 Flash remains a key cost lever: public pricing reports place it far below frontier models while retaining long context, structured output, prompt caching, function calling, and reasoning support.

The implication for TemuClaude is to avoid one permanent winner. GLM-5.2 is a strong orchestrator/aggregator default, DeepSeek V4 Pro remains the hard reasoning/search default, Nemotron is a verifier default, and cheaper flash/MoE models should be used when telemetry proves they preserve quality.

## Implementation Added

`src/adaptive.py`:
- Added `STEP_MODEL_DEFAULTS`
- Added `get_fallback_model_for_step(...)`
- Added `get_model_for_step(...)`

`src/orchestrator.py`:
- Hard-tier MCTS now asks the step router for search and PRM verification models.
- Code verification asks the step router for the verification model.
- PRM self-consistency asks the step router for consistency and verifier models.
- Self-QA gate asks the step router for the QA model.
- Strategy metadata marks `+step_model_router` when telemetry-driven selection is used.

`tests/test_step_model_routing.py`:
- Verifies fallback model choices.
- Verifies sparse telemetry does not override defaults.
- Verifies enough telemetry can switch a step model to the observed best candidate.

Website/GitHub-facing updates:
- `README.md` now describes step-aware model routing and budget/progress/failure telemetry.
- `website/app/models/page.tsx` now shows the Step-Aware Router panel.
- `website/app/docs/page.tsx` now documents step-level model routing and telemetry signals.

## Why This Matters

Whole-query routing misses the most important part of frontier orchestration: a hard task may need different models for planning, search, verification, consistency, repair, formal logic, and final prose. Step-aware routing lets TemuClaude spend expensive intelligence only where it has measurable marginal value.

## Next Implementation Queue

1. Thread `get_model_for_step(...)` into medium-tier self-QA and shepherding.
2. Add explicit tool-call and wall-clock budgets, not only token budget estimates.
3. Add decay/forgetting to step recommendations so stale model performance does not dominate.
4. Add controlled exploration for newly available OpenRouter models.
5. Surface step-router telemetry in the playground orchestration metadata.

## Sources

- OpenRouter Blog, "The Open Weight Models that Matter: June 2026"
- Dynamic Model Routing and Cascading for Efficient LLM Inference, arXiv:2603.04445
- TRouter, arXiv:2604.09377
- ParetoBandit, arXiv:2604.00136
- STRMAC, arXiv:2511.02200

