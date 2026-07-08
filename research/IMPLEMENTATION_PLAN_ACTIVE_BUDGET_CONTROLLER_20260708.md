# TemuClaude Upgrade Plan: Active Budget Controller

Generated: 2026-07-08

## Research Inputs

- Source: Adaptive Test-Time Compute Allocation for Reasoning LLMs via Constrained Policy Optimization, arXiv:2604.14853
  - Finding: Adaptive compute allocation is framed as maximizing expected accuracy under an average compute budget; learned policies beat uniform allocation and reported up to 12.8% relative MATH accuracy gain under matched budgets.
  - TemuClaude implication: Replace static hard/medium/trivial compute schedules with a learned or heuristic controller over `remaining_budget_ratio`, `uncertainty`, `progress_delta`, and verifier state.
  - URL: https://arxiv.org/abs/2604.14853

- Source: Process Reward Agents for Steering Knowledge-Intensive Reasoning, arXiv:2604.09482
  - Finding: Online step-wise process rewards can steer and prune reasoning trajectories during inference, not only score final traces after the fact.
  - TemuClaude implication: Feed structured PRM verdicts into runtime decisions for MCTS expansion, debate escalation, and early stop.
  - URL: https://arxiv.org/abs/2604.09482

- Source: Reward-Guided Speculative Decoding for Efficient LLM Reasoning, ICML 2025 / arXiv:2501.19324
  - Finding: A lightweight draft model plus PRM-guided target invocation can reduce reasoning FLOPs up to 4.4x while improving average accuracy in reported reasoning benchmarks.
  - TemuClaude implication: Add a cheap draft/strong verify path for selected steps before invoking expensive frontier fallback.
  - URL: https://proceedings.mlr.press/v267/liao25f.html

- Source: OpenRouter, The Open Weight Models that Matter: June 2026
  - Finding: GLM 5.2, Nemotron 3 Ultra, MiniMax M3, DeepSeek V4 Pro, and Kimi K2.6 form the current high-value open-weight pool; GLM 5.2 is close to the frontier in agentic benchmarks while open-weight economics remain favorable.
  - TemuClaude implication: Keep the current role-specialized pool; improve orchestration policy before making broad model swaps.
  - URL: https://openrouter.ai/blog/insights/the-open-weight-models-that-matter-june-2026/

## Objective

- Quality metric: improve hard-tier reasoning pass rate or verifier agreement without reducing existing benchmark scores.
- Cost metric: reduce average hard-tier token spend by 15-30% in shadow/eval runs before enabling runtime gates.
- Latency metric: reduce unnecessary verification/debate calls on low-risk states; no more than 10% p95 latency increase on hard-tier tasks.
- Reliability metric: lower failed-verification and contradiction-labeled traces; no increase in timeout/error failure labels.

## Repo Touchpoints

- Model/orchestration:
  - `src/step_telemetry.py`
  - `src/adaptive.py`
  - `src/orchestrator.py`
  - `src/reasoning_tree.py`
  - new `src/budget_controller.py`

- Tests:
  - `tests/test_step_telemetry.py`
  - `tests/test_step_model_routing.py`
  - new `tests/test_budget_controller.py`

- Research docs:
  - `research/CHANGELOG.md`
  - `research/IMPLEMENTATION_STATUS_20260708.md`
  - this plan

- Website:
  - `website/app/docs/page.tsx`
  - `website/app/models/page.tsx`
  - Do not change global theme files unless explicitly requested.

- Deployment/GitHub:
  - Push only after tests/build pass.
  - Verify `origin/main` hash and live `temuclaude.com` strings if website docs change.

## Implementation Phases

### 1. Shadow Controller

Create `src/budget_controller.py` with a pure decision function:

```text
input:
  task_type, tier, step_type, remaining_budget_ratio,
  progress_delta, uncertainty, failure_label,
  prm_label, prm_confidence, verifier_passed

output:
  action in [continue, verify, debate, stop, escalate, cheap_draft]
  reason
  confidence
  cost_risk
```

In phase 1, do not alter runtime behavior. Only record the action recommendation into step telemetry or response metadata.

### 2. Runtime Metadata Enrichment

Extend step telemetry with optional controller fields:

- `controller_action`
- `controller_confidence`
- `controller_reason`
- `cost_risk`
- `verifier_state`
- `prm_label`
- `prm_confidence`

Tests must confirm old telemetry files still load and events remain bounded.

### 3. Conservative Gates

Enable runtime decisions only for low-risk, high-confidence states:

- `stop`: allowed only after QA/pass or high-confidence PRM correct label.
- `verify`: trigger when uncertainty is high or PRM label is ambiguous.
- `debate`: trigger on contradiction, low PRM confidence, or repeated verifier disagreement.
- `escalate`: trigger only when hard-tier budget remains and failure labels indicate high-value recovery.
- `cheap_draft`: use a cheaper draft path before strong verification when confidence is moderate and budget is low.

Every gate must have a fallback to current behavior.

### 4. Benchmark Promotion Gate

Add a local evaluation packet before default-on:

- small math/reasoning set
- coding verification smoke set
- knowledge/RAG reasoning set
- adversarial ambiguity set

Record:

- quality score
- cost estimate
- latency
- controller action distribution
- fallback/escalation rate
- failure label distribution

Promotion threshold:

- quality: non-regression or improvement
- cost: 15%+ reduction where controller takes action
- reliability: no increase in failed verification, contradiction, timeout, or model error labels

### 5. Website/GitHub Sync

After runtime gates are implemented and verified:

- Update README architecture: "Active Budget Controller".
- Update docs page: explain telemetry-driven continue/verify/debate/stop decisions.
- Update models page only if model roles change.
- Keep all benchmark language labeled as projected until live evals exist.

### 6. Publication Verification

Required commands:

```bash
PYTHONPATH=. pytest -q tests/test_budget_controller.py tests/test_step_telemetry.py tests/test_step_model_routing.py tests/test_v3_breakthroughs.py tests/test_v3_upgrades.py
python3 -m py_compile src/budget_controller.py src/step_telemetry.py src/adaptive.py src/orchestrator.py src/reasoning_tree.py
cd website && npm run build
git diff --cached --stat
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

If website changes are pushed:

```bash
curl -L -s https://temuclaude.com/docs | rg -n "Active Budget Controller|step-aware routing|remaining budget"
curl -I -L https://temuclaude.com/docs
```

## Rollback Plan

- Add a config flag before runtime enablement:
  - `config/routing_preferences.json`
  - key: `active_budget_controller_enabled`
  - default: `false`

- Fallback:
  - if controller errors, use existing orchestration path.
  - if promotion gate fails, keep controller in shadow mode.

- Failure threshold:
  - disable runtime controller if quality score drops >2%, timeout/error labels rise >1%, or average hard-tier cost rises instead of falling.

## Success Criteria

- Controller recommendations are logged in shadow mode with no behavior change.
- Targeted tests pass.
- No unrelated dirty files are staged.
- Runtime gates are enabled only after benchmark promotion.
- Website docs remain warm-light themed and accurately describe only implemented behavior.
