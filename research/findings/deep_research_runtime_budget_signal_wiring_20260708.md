# Deep Research: Runtime Budget Signal Wiring for TemuClaude

Generated: 2026-07-08

## Executive Finding

TemuClaude now has the first runtime bridge between orchestration and budget-aware learning. Previous work added fields for budget, progress, uncertainty, and failure labels; this pass wires the orchestrator so every completed response can populate those fields with coarse but real runtime metadata.

This matters because recent agent research consistently warns that post-hoc cost dashboards are not enough. Budget must be an active control signal attached to the same step trace that records routing, verification, and failure.

## Research Signals

### 1. Runtime Budget Control Needs Step-Level Accounting

Sources:
- BAGEN, arXiv:2606.00198: https://arxiv.org/html/2606.00198v1
- Inference-Time Budget Control, arXiv:2605.05701: https://arxiv.org/abs/2605.05701

The key finding is that agents should reason about internal and external budgets during execution, not only after completion. Search-time budget control provides the main gains because it changes how future budget is spent.

TemuClaude implication:
- Attach token budget, estimated spend, and remaining budget to each orchestration trace.
- Later use this to decide whether to search, verify, debate, answer, or stop.

### 2. Budget-Aware Search Needs Progress Signals

Source: Budget-Aware Value Tree Search, arXiv:2603.12634
URL: https://arxiv.org/html/2603.12634

BAVT uses step-level value estimation and remaining-budget ratios to shift from broad exploration to exploitation. It also emphasizes residual value: measure marginal progress, not absolute self-confidence.

TemuClaude implication:
- Add `progress_delta` to step traces.
- Start with heuristic progress from existing strategy markers; later replace with learned value critics.

### 3. Agent Observability Needs Typed Failure Surfaces

Sources:
- AgentAtlas, arXiv:2605.20530: https://arxiv.org/html/2605.20530v1
- Early Diagnosis of Wasted Computation, arXiv:2606.01365: https://arxiv.org/html/2606.01365v1
- Longitudinal Taxonomy of Silent Failures, arXiv:2606.14589: https://arxiv.org/html/2606.14589v1

Agent quality improves when control decisions and trajectory failures are explicit units of measurement. Silent failures and wasted computation require typed trace surfaces, not just final answer ratings.

TemuClaude implication:
- Infer coarse `failure_label` values now: `model_timeout`, `model_error`, `logical_contradiction`, `verification_failed`, `search_failed`, `unresolved_debate`, `empty_answer`, `unknown_failure`.
- Use labels to seed future failure attribution and eval generation.

## Implementation Added

`src/step_telemetry.py`:
- Added `infer_failure_label(...)`
- Added `infer_progress_delta(...)`
- Added `infer_uncertainty(...)`
- Added `build_runtime_step_metadata(...)`

`src/orchestrator.py`:
- The final `record_strategy_steps(...)` hook now passes:
  - `initial_budget=token_budget`
  - `remaining_budget=max(token_budget - estimated_tokens, 0)`
  - `budget_spent=estimated_tokens`
  - inferred `progress_delta`
  - inferred `uncertainty`
  - inferred `failure_label`

`tests/test_step_telemetry.py`:
- Added coverage for runtime metadata inference on verified success and timeout failure paths.

## Next Implementation Queue

1. Replace answer-length token estimates with provider usage metadata when available.
2. Thread separate budgets for tokens, tool calls, verifier calls, and wall-clock time.
3. Add per-step metadata at internal tool/model-call boundaries, not only final response completion.
4. Use `get_budget_alerts(...)` to surface conservative escalation/abort recommendations in logs.
5. Convert failure labels into eval cases for the research swarm.

## Strategic Takeaway

This is still a bootstrap signal, but it is the right kind of signal. TemuClaude can now begin learning not only which model answered, but how much budget remained, whether the orchestration path made progress, and what kind of failure occurred when it did not.

