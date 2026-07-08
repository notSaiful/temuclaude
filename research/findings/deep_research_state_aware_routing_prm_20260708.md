# Deep Research: State-Aware Routing and Agent PRMs for TemuClaude

Generated: 2026-07-08

## Executive Finding

The next frontier for TemuClaude is a state-aware controller: route each intermediate state of a task to the cheapest capable model, then use process rewards to decide whether to continue, verify, branch, retrieve, repair, or stop. This is a stronger target than whole-query routing because benchmark-winning systems now exploit the fact that a single task has multiple capability regimes.

This pass produced one implementation hook: `src/step_telemetry.py`, wired into `src/orchestrator.py`, so TemuClaude can start collecting per-step events from strategies such as `mcts_step_search`, `step_verify`, `prm_consistency`, `debate_escalation`, and `z3_verified`.

## Finding 1: State-Aware Routing Beats Static Agent Order

Source: STRMAC, arXiv:2511.02200
URL: https://arxiv.org/html/2511.02200v1

Core result: STRMAC encodes evolving problem-solving state and agent expertise, then selects the most suitable agent at each step. It reports up to 23.8% improvement over baselines and up to 90.1% lower data-collection overhead versus exhaustive path search.

TemuClaude implication:
- Whole-query routing in `src/preference_router.py` is useful but insufficient.
- The new step telemetry should become training data for a state router keyed by `(task_type, tier, step_type, previous_step_outcome, uncertainty)`.
- Start with cheap non-invasive learning: collect telemetry first, train later.

## Finding 2: Orchestration Topology Is an Optimization Target

Source: AdaptOrch, arXiv:2602.16873
URL: https://arxiv.org/html/2602.16873

Core result: AdaptOrch validates adaptive multi-agent orchestration across coding, GPQA-style reasoning, and RAG tasks, reporting 12-23% gains over static topologies with the same underlying models. The key lesson is that topology choice can matter as much as model choice.

TemuClaude implication:
- Track which topology was used: direct, shepherding, tree search, MCTS, fusion, debate, QA retry, formal verification.
- Add a future `topology_router` that predicts whether a prompt needs direct answer, search, debate, or verifier-heavy flow.
- Avoid always using heavy MoA; route topology based on expected marginal value.

## Finding 3: Cold-Start Routing Needs Synthetic Task Profiles

Source: TRouter, arXiv:2604.09377
URL: https://arxiv.org/html/2604.09377v1

Core result: TRouter addresses router cold start by generating a hierarchical task taxonomy and synthetic QA pairs. It models query-conditioned cost and performance through latent task-type variables instead of relying only on surface query features.

TemuClaude implication:
- Current feature extraction in `src/preference_router.py` is mostly lexical.
- Add synthetic task profiles for math, coding, reasoning, UI/UX, long context, media, professional domains, and safety-sensitive tasks.
- Use generated profiles to seed router priors before enough production telemetry exists.

## Finding 4: Role and Model Scale Should Be Routed Jointly

Source: OI-MAS, arXiv:2601.04861
URL: https://arxiv.org/html/2601.04861v2

Core result: OI-MAS uses a conductor to choose both the agent role and model backbone for each reasoning state, optimizing a confidence-aware objective and reducing compute while improving accuracy.

TemuClaude implication:
- The router should choose `(role, model, budget)`, not only `model`.
- Example roles: planner, coder, verifier, critic, retriever, formalizer, simplifier.
- Step telemetry should record `step_type` now; later it can add explicit `role`.

## Finding 5: Adaptive Test-Time Compute Should Be Budget-Constrained

Source: Adaptive Test-Time Compute Allocation, arXiv:2604.14853
URL: https://arxiv.org/html/2604.14853v1

Core result: The paper formalizes compute allocation as maximizing expected accuracy subject to average compute budget, then learns a lightweight real-time classifier from oracle allocation decisions.

TemuClaude implication:
- `src/pareto_tracker.py` should evolve from after-the-fact reporting into a budget controller.
- Step telemetry creates the missing state-action-cost-outcome records needed to learn when extra compute is worth it.
- The target policy should maximize benchmark lift per dollar, not raw benchmark score alone.

## Finding 6: Agent PRMs Are the Right Reward Signal for Long-Horizon Tasks

Sources:
- AgentPRM practical framework, arXiv:2502.10325: https://arxiv.org/abs/2502.10325
- AgentPRM via promise/progress, arXiv:2511.08325: https://arxiv.org/abs/2511.08325
- FreePRM, arXiv:2506.03570: https://arxiv.org/abs/2506.03570
- AURORA, arXiv:2502.11520: https://arxiv.org/abs/2502.11520
- PAPO, arXiv:2603.26535: https://arxiv.org/abs/2603.26535

Core result: Agent tasks need process rewards based on progress toward a goal, not just local step correctness. Newer PRM work reduces label cost through Monte Carlo rollouts, temporal-difference estimates, weak supervision from final outcomes, ensemble prompting, reverse verification, and decoupled process/outcome advantages to reduce reward hacking.

TemuClaude implication:
- For coding agents, score actions by promise/progress: did the step reduce uncertainty, inspect the right file, run the right test, localize the bug, or verify the patch?
- Do not train on scalar PRM scores alone. Store typed labels and outcome anchors.
- Short-term: extend telemetry with `progress_delta`, `uncertainty_before`, `uncertainty_after`, and `failure_label`.
- Medium-term: train a lightweight AgentPRM over TemuClaude traces and use it for MCTS/debate/cascade stopping.

## Implementation Added in This Pass

- `src/step_telemetry.py`
  - Records one event per strategy fragment.
  - Stores hashed query id, task type, tier, step type, model, success, latency, token estimate, and sequence index.
  - Summarizes step success rate, latency, token use, and top model.

- `src/orchestrator.py`
  - Calls `record_strategy_steps(...)` after existing Pareto and routing logs.
  - Telemetry failures are non-blocking.

- `tests/test_step_telemetry.py`
  - Covers strategy splitting, normalization, persistence, summaries, hashed query storage, and bounded history.

## Next Implementation Queue

1. Add typed PRM labels in `src/reasoning_tree.py`
   - Replace score-only PRM output with `{score, label, confidence, needs_escalation}`.

2. Feed step telemetry into router training
   - Add a step-level dataset builder next to `get_preference_dataset()`.
   - Train a simple baseline: predict best step model/topology from task type, tier, step type, and query features.

3. Add topology router
   - Predict direct vs search vs fusion vs debate vs verifier-heavy route.
   - Objective: maximize quality under budget, with kill switch through `pareto_tracker`.

4. Add synthetic cold-start task profiles
   - Generate task taxonomy and examples for frontier benchmarks: SWE-Bench Pro, Terminal-Bench, LiveCodeBench, GPQA Diamond, HLE, CharXiv, MRCR, long-context reasoning.

5. Add progress labels for coding-agent traces
   - `located_file`, `identified_bug`, `patch_applied`, `test_failed`, `test_passed`, `regression_detected`, `verified_fix`.

## Strategic Takeaway

TemuClaude should become a learning controller over intelligence actions. The immediate win is observability: collect the state-action-outcome-cost data needed to learn where extra reasoning pays for itself. Once that dataset exists, routing can move from query-level heuristics to Fugu-style state-aware orchestration with an explicit cost frontier.

