# Deep Research: Frontier-Orchestration Breakthroughs for TemuClaude

Generated: 2026-07-08

## Executive Finding

The current frontier pattern is not only bigger base models. The strongest public evidence points to compound systems that adaptively allocate model calls, verification, search depth, and memory per step. Sakana Fugu's June 2026 technical report is the clearest current example: a trained orchestrator over frontier worker models reports state-of-the-art or near-state-of-the-art results across SWE Bench Pro, Terminal Bench 2.1, LiveCodeBench Pro, GPQA Diamond, CharXiv, long-context reasoning, and MRCRv2.

TemuClaude already has the right skeleton: `src/unified_routing.py`, `src/reasoning_tree.py`, `src/verifier.py`, `src/self_moa.py`, `src/fusion.py`, `src/gepa.py`, and the research swarm. The breakthrough is to stop treating these as independent tricks and turn them into a cost-aware per-step controller with hard Pareto gates.

## Highest-Impact Findings

### 1. Per-Step Adaptive Orchestration Is Now a Frontier-Class Lever

Source: Sakana Fugu Technical Report, arXiv:2606.21228
URL: https://arxiv.org/html/2606.21228v1

Finding: Fugu reports large gains by learning when to call different models at different stages of the same task. The most relevant detail for TemuClaude is not the exact benchmark table; it is the trajectory-level adaptivity. The report states that on Terminal Bench, Fugu alternates between GPT-5.5 and Claude Opus 4.8 and calls Claude at critical debugging points.

TemuClaude implication:
- Upgrade `src/unified_routing.py` from request-level routing to step-level routing.
- Route separately for plan, code search, patch generation, debugging, final verification, and explanation.
- Track which model won at each step type, not only which model answered the whole user request.

Expected upside:
- Higher coding-agent score without always paying for the most expensive model.
- Better use of specialization: one model for math, another for repo navigation, another for patch synthesis, another for critique.

### 2. Verifier-Guided Test-Time Compute Beats Blind Best-of-N

Sources:
- rStar-Math, arXiv:2501.04519: https://arxiv.org/abs/2501.04519
- ThinkPRM, arXiv:2504.16828: https://arxiv.org/html/2504.16828v1
- Reward-Guided Speculative Decoding, arXiv:2501.19324: https://arxiv.org/abs/2501.19324

Finding: The most valuable reasoning loop is policy model plus process verifier plus selective search. rStar-Math shows small models can become much stronger on math with MCTS and PRM-guided self-evolution. ThinkPRM shows a generative/verbalized verifier can beat judge baselines while using far fewer process labels. Reward-guided speculative decoding shows a PRM can decide when to invoke a stronger target model and reports up to 4.4x fewer FLOPs on reasoning workloads.

TemuClaude implication:
- Keep `src/reasoning_tree.py`, but make PRM scoring produce structured labels: `correct`, `unsupported`, `arithmetic_error`, `logic_gap`, `needs_tool`, `unsafe`.
- Add a budget controller: cheap verifier first, expensive verifier only when disagreement or high benchmark value.
- Cache verifier judgments by normalized `(task, step, context_hash)`.

Expected upside:
- Better math, code, and science reasoning per dollar.
- Lower false positives from simple scalar judge scores.

### 3. Cost-Aware Agent Benchmarks Are Becoming Mandatory

Source: Claw-SWE-Bench, arXiv:2606.12344
URL: https://arxiv.org/html/2606.12344v1

Finding: Newer coding-agent evaluation argues that Pass@1 alone is misleading because agent systems consume very different token budgets, wall-clock time, and tool calls. The paper reports accuracy together with total API cost, duration, and cache hit rate under a fixed outer budget.

TemuClaude implication:
- Add a local Pareto benchmark harness for every major change: quality, cost, latency, calls, retry count, cache hit rate.
- A finding should not be promoted from research to integration unless it improves Pareto position or has a strategic reason.
- Current `research/CHANGELOG.md` shows too many staged or reverted integrations. This needs a stronger gate before code mutation.

Expected upside:
- Prevents "benchmark wins" that quietly bankrupt inference.
- Makes the fraction-of-frontier-cost objective measurable.

### 4. GEPA Should Replace the Current Simplified Prompt Evolution

Source: GEPA, arXiv:2507.19457
URL: https://arxiv.org/abs/2507.19457

Finding: GEPA uses full execution traces, natural-language reflection, mutation, and Pareto selection. The reported claim is that it can outperform GRPO and MIPROv2 with far fewer rollouts on several tasks.

TemuClaude implication:
- `src/gepa.py` is currently a placeholder-level implementation: it generates three prompts and keeps the first valid variation.
- Replace it with trace-based prompt evolution:
  - collect failure traces from `verifier`, `reasoning_tree`, `fusion`, and `unified_routing`;
  - ask a reflector to identify reusable failure rules;
  - mutate prompts/policies;
  - keep a Pareto frontier by quality, cost, and latency.

Expected upside:
- Continuous improvement without weight training.
- Especially useful for compound tasks where prompt and orchestration policies matter more than a single model call.

### 5. KV Cache Optimization Is a First-Order Cost Lever for Long Context

Source: KV Cache Optimization Strategies, arXiv:2603.20397
URL: https://arxiv.org/abs/2603.20397

Finding: KV cache cost scales linearly with context length and becomes a bottleneck for million-token tasks. Recent surveys organize practical options into eviction, compression, hybrid memory, attention changes, and combinations. No one method dominates; the right choice depends on workload and hardware.

TemuClaude implication:
- For API-only models, prioritize prompt caching, prefix caching, semantic context trimming, and retrieval compression.
- For self-hosted models, evaluate vLLM/SGLang with paged attention, quantized KV cache, and prefix cache.
- Add `context_cost_profile` to routing decisions: long-context tasks should be routed by cache behavior, not only model intelligence.

Expected upside:
- Major savings for long research, coding, and memory-heavy sessions.

## Recommended Next Implementation Queue

1. Step-level orchestration telemetry
   - Add event schema: `task_id`, `step_type`, `model`, `cost_estimate`, `latency_ms`, `verifier_score`, `accepted`.
   - Feed this into `src/preference_router.py` and `src/pareto_tracker.py`.

2. Pareto promotion gate for research findings
   - Before any integrator patch, run a cheap benchmark packet.
   - Promote only if quality is non-regressing and cost/latency improves, or if quality gain is large enough to justify cost.

3. Structured PRM labels
   - Replace scalar-only PRM results with typed failure labels.
   - Use labels to decide whether to retry, branch, call tools, escalate model tier, or ask for clarification.

4. Real GEPA loop
   - Use full traces instead of selecting the first prompt candidate.
   - Maintain a Pareto frontier of prompt/orchestration variants.

5. Cost-aware coding-agent eval
   - Build a small local benchmark inspired by Claw-SWE-Bench Lite: 20-40 repo tasks with fixed budget and cost accounting.
   - Track resolved rate, total token cost, wall time, tool calls, and regression failures.

## Strategic Takeaway

The path to beating Fable/Mythos-class single models at lower cost is not to imitate one giant model. It is to become a better intelligence allocator: route each step to the cheapest model that can solve it, spend extra reasoning only where verifier uncertainty says it is worth it, and automatically evolve prompts and policies from failure traces.

