# Deep Research: Budget, Progress, and Failure Telemetry for TemuClaude

Generated: 2026-07-08

## Executive Finding

The next leap in cost-efficient intelligence is not just routing to cheaper models. The controller must know the remaining budget, whether the last action made progress, and what kind of failure is unfolding. Recent papers converge on the same operational lesson: budget should be an active state variable, progress should be measured at the step level, and verifier/failure labels must be typed because scalar scores alone are too brittle.

This pass upgrades `src/step_telemetry.py` with optional budget, progress, uncertainty, and failure-label fields, plus low-budget failure alerts.

## Finding 1: Budget-Aware Value Trees Need Remaining-Budget Ratios

Source: Budget-Aware Value Tree Search, arXiv:2603.12634
URL: https://arxiv.org/html/2603.12634

Core result: BAVT uses a remaining-resource ratio to shift from broad exploration to greedy exploitation as budget depletes. It argues that intelligent budget management can outperform brute-force compute scaling under strict budgets.

TemuClaude implication:
- Record `initial_budget`, `remaining_budget`, and `remaining_budget_ratio` per step.
- Use the ratio to change behavior: explore early, exploit or stop late.
- Future MCTS/search should score nodes by value and remaining budget, not value alone.

## Finding 2: Budget Awareness Must Be Active, Not Post-Hoc

Source: BAGEN, arXiv:2606.00198
URL: https://arxiv.org/abs/2606.00198

Core result: BAGEN defines budget-aware agents as systems that treat budget as an active control signal. It reports that frontier agents are often over-optimistic and continue spending on tasks unlikely to succeed. Early stop saves 28-64% tokens on failed trajectories.

TemuClaude implication:
- Step telemetry should support early abort or escalation alerts when low budget and high failure rate co-occur.
- Budget should eventually become part of prompts and controller state, not only a metric after execution.

## Finding 3: Search Agents Need Value-of-Information Style Action Control

Source: Inference-Time Budget Control for LLM Search Agents, arXiv:2605.05701
URL: https://arxiv.org/html/2605.05701v1

Core result: Budgeted search should decide whether to search, decompose, or answer under explicit tool-call and token budgets. The paper emphasizes hard budget audits, explicit accounting, conservative finalization, and failure analysis.

TemuClaude implication:
- Add future step labels for `search`, `decompose`, `answer`, `verify`, and `finalize`.
- Track whether each step increased evidence/progress enough to justify its cost.

## Finding 4: Coding-Agent Verification Must Co-Evolve with the Generator

Source: Verification Horizon, arXiv:2606.26300
URL: https://arxiv.org/html/2606.26300v2

Core result: For modern coding agents, verification can be harder than generation. Fixed rewards are fragile because tests, rubrics, and automated judges are only proxies for user intent; verification must co-evolve with the generator.

TemuClaude implication:
- Store `failure_label` rather than only success/failure.
- Useful labels include `test_failure`, `proxy_mismatch`, `reward_hacking`, `silent_error`, `tool_loop`, `insufficient_evidence`, and `regression_detected`.
- Use labels to decide whether to add tests, switch verifier, ask for clarification, or escalate to a stronger model.

## Finding 5: Early Abort Needs Recall-Calibrated Evidence

Source: Early Abort of LLM Agent Episodes, arXiv:2607.06503
URL: https://arxiv.org/html/2607.06503v1

Core result: Eventual failure can be predicted early in agent episodes, and calibrated abort gates can save compute while preserving a target success recall. The key caution is that the data itself determines what promises can be certified.

TemuClaude implication:
- Do not auto-abort yet. First collect telemetry and surface alerts.
- Only deploy hard aborts once enough validation traces prove recall is preserved.

## Finding 6: Credit Assignment Needs Signed Local Signals

Source: Evaluation-Aligned Training Signals for Multi-LLM Agents, arXiv:2511.10687
URL: https://arxiv.org/html/2511.10687v3

Core result: Multi-agent learning needs to transform system-level outcomes into message-level credit and blame. The paper combines success credit with first-error localization and repair-aware preferences.

TemuClaude implication:
- Record `progress_delta` and `failure_label` now.
- Later derive signed local training signals: which step helped, which step hurt, and which repair fixed it.

## Implementation Added in This Pass

`src/step_telemetry.py` now records optional:
- `initial_budget`
- `remaining_budget`
- `budget_spent`
- `remaining_budget_ratio`
- `progress_delta`
- `uncertainty`
- `failure_label`

It also now provides:
- `calculate_remaining_budget_ratio(...)`
- `normalize_failure_label(...)`
- progress/uncertainty-aware route utility
- failure-label summaries
- `get_budget_alerts(...)` for low-budget/high-failure states

Tests in `tests/test_step_telemetry.py` cover:
- budget-ratio clipping
- failure-label normalization
- dataset propagation of budget/progress/failure fields
- progress-aware recommendations
- low-budget failure alerts

## Next Implementation Queue

1. Thread `initial_budget` and `remaining_budget` from `src/orchestrator.py` into `record_strategy_steps`.
2. Add `failure_label` from verifier/code execution outcomes.
3. Add `progress_delta` heuristics for code tasks:
   - tests failing -> tests passing: positive
   - fewer failing tests: positive
   - new syntax error: negative
   - repeated same error: negative
4. Add a conservative `should_escalate_or_abort` helper using `get_budget_alerts`.
5. Train a first step-router over `(task_type, tier, step_type, remaining_budget_ratio, progress_delta, uncertainty)`.

## Strategic Takeaway

TemuClaude's advantage should come from spending intelligence like capital. Every step should answer: how much budget remains, did this action move us closer, what failure pattern is emerging, and is another expensive call worth it?

