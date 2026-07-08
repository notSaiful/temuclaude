# Deep Research: Budget-Aware Step Router for TemuClaude

Generated: 2026-07-08

## Executive Finding

The newest routing research is converging on a stronger claim than "send easy prompts to cheap models." Frontier-class affordability requires sequential budget control: every model/tool/verifier call is an action in a longer trajectory, and the controller must preserve budget for future high-stakes steps while adapting to model drift, pricing shifts, and new endpoints.

This pass turns TemuClaude's new step telemetry into usable training material by adding normalized step datasets and transparent route recommendations in `src/step_telemetry.py`.

## Finding 1: State-Aware Routing Is Now the Right Unit of Learning

Source: STRMAC v2, arXiv:2511.02200
URL: https://arxiv.org/html/2511.02200v2

STRMAC's current version reinforces the earlier signal: rigid agent scheduling leaves performance on the table. It separately encodes interaction history and agent knowledge, then selects a single agent at each step. Reported gains remain high: up to 23.8% better accuracy and up to 90.1% less data-collection overhead than exhaustive path search.

TemuClaude implication:
- Use step telemetry as the first state-action-outcome dataset.
- Train a router over `context_key = task_type:tier:step_type`.
- Later add richer state: previous step outcome, uncertainty, remaining budget, and available tools.

## Finding 2: Sequential Routing Needs Remaining-Budget State

Source: SeqRoute, arXiv:2605.25424
URL: https://arxiv.org/html/2605.25424v1

SeqRoute formalizes multi-turn routing as a finite-horizon Markov Decision Process and includes remaining budget in the state. It reports 6.0-73.5% operational cost reductions while maintaining or improving quality, with bankruptcy rates below 1%. The key warning is that myopic single-turn routers can overspend early and fail when a hard turn arrives later.

TemuClaude implication:
- Add `remaining_budget` and `session_spend` to future telemetry.
- Treat expensive verification and debate as budgeted actions, not automatic quality rituals.
- Make the router conserve budget during low-stakes steps and spend aggressively only when uncertainty or benchmark value justifies it.

## Finding 3: Production Routers Must Adapt to Non-Stationarity

Source: ParetoBandit, arXiv:2604.00136
URL: https://arxiv.org/html/2604.00136v1

ParetoBandit uses cost-aware contextual bandits, online budget pacing, geometric forgetting, and hot-swappable model registries. This matters because model quality, provider pricing, and endpoint availability change constantly. A static router becomes stale.

TemuClaude implication:
- Step recommendations should not become hardcoded forever.
- Add forgetting/decay to step stats once enough data exists.
- Force exploration for new models, but reject them quickly if they fail quality/cost utility.

## Finding 4: Progress Advantage May Reduce the Need for Dedicated Agent PRMs

Source: Progress Advantage for LLM Agents, arXiv:2606.26080
URL: https://arxiv.org/html/2606.26080v1

This paper argues that RL post-training already contains a step-level progress signal: a log-probability ratio between an RL-trained policy and its reference policy can recover an advantage-like score. It reports strong results for test-time scaling, uncertainty quantification, and failure attribution without dedicated reward-model training.

TemuClaude implication:
- If self-hosted RL and reference policies become available, compute a cheap progress score for each step.
- Until then, approximate progress through observable events: tests passing, error count dropping, verifier confidence rising, fewer unresolved files, and reduced uncertainty.

## Finding 5: Domain PRMs Must Be Environment-Aware

Source: DataPRM, arXiv:2604.24198
URL: https://arxiv.org/html/2604.24198v1

DataPRM finds that general PRMs struggle with dynamic data analysis: they miss silent logical errors and can wrongly penalize useful exploration. Its environment-aware process reward model distinguishes correctable grounding errors from irrecoverable mistakes and improves downstream agents on data-analysis benchmarks.

TemuClaude implication:
- Do not use one generic PRM label everywhere.
- For coding/data/science tasks, record environment signals: command run, test result, interpreter output, file touched, error class.
- Add typed labels instead of scalar-only step scores.

## Implementation Added in This Pass

`src/step_telemetry.py` now exposes:
- `get_step_dataset(success_only=False)`: normalized rows for future state-aware routing.
- `get_step_route_recommendations(...)`: a transparent utility model over success, latency, token use, and optional quality score.

The recommendation is deliberately conservative:
- If evidence is below `min_count`, it returns `collect_more_data`.
- If enough evidence exists, it returns `use_observed_best` with ranked candidates.
- Utility is transparent and tunable, preparing the path toward ParetoBandit/SeqRoute-style routing without changing live behavior prematurely.

Tests added in `tests/test_step_telemetry.py` verify:
- Dataset generation.
- Context keys.
- Success-only filtering.
- Best-model recommendation under success/cost tradeoff.
- Insufficient-data behavior.

## Next Implementation Queue

1. Add `remaining_budget` and `session_spend` to step telemetry.
2. Add `failure_label` and `progress_delta` to verifier/code-execution steps.
3. Build a step-level router in `src/preference_router.py` that consumes `get_step_dataset()`.
4. Add decay/forgetting to recommendations to handle model and price drift.
5. Add a small forced-exploration registry for new candidate models.

## Strategic Takeaway

TemuClaude should evolve from "router plus verifier stack" into a budget-aware sequential controller. The model that wins is not the one that spends the most thinking tokens; it is the one that knows when a step is worth spending on.

