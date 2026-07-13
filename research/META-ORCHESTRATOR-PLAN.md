# Meta-Orchestrator: Safe Specialist Coordination Plan

## Research

The repository already contains capable but separate workers:

- `src/orchestrator.py` for text reasoning, routing, verification, and repair.
- `src/deep_research.py` for source-grounded research.
- `src/media/orchestrator.py` plus audio/TTS modules for media generation.
- `src/budget_controller.py` for conservative, shadow-only budget decisions.
- `src/step_telemetry.py` for privacy-light, step-level learning data.

The missing component was a shared control plane that can decide which worker
should contribute, in which dependency order, under what budget, and only after
which approvals.  Directly letting a model select arbitrary tools or commands
would violate the existing permissioned agent direction and create a deployment
and credential-risk boundary.

## Architecture

`src/meta_orchestrator.py` provides a typed, allow-listed task DAG:

1. It deterministically derives a small plan from the goal.
2. It assigns only fixed workers: text, deep research, image/video media,
   audio, workspace, and verifier.
3. Every node carries a declared capability and estimated cost units.
4. Filesystem writes, commands, network calls, GitHub, and deployments are
   blocked unless the caller grants the exact capability for that run.
5. Worker execution is adapter-based. The coordinator itself never receives a
   shell command, provider secret, or deployment credential.
6. The final verifier feeds the current budget controller, which recommends
   accept/refine/escalate rather than making an irreversible decision itself.

## Rollout

The default is `shadow` mode. It produces the complete plan and result-shaped
telemetry without calling a worker. The application observability boundary can
explicitly call `record_shadow_telemetry`; it records only hashed query metrics
and no worker output. Promote only after offline and staging evaluation show all
of the following:

- zero privileged adapter calls without a matching explicit approval;
- no plan over its configured cost cap;
- plan construction p95 under 10 ms in the application process;
- verifier pass rate and task quality not worse than the direct single-worker
  baseline for the same test set.

The rollback is immediate: keep or restore `RunMode.SHADOW`; no customer-facing
routing or execution path depends on this module yet.

## Integration Contract

The owning runtime supplies a handler for each worker it wants to enable. A
handler receives a `TaskNode` and prior `NodeResult` values, then returns a
minimal `NodeResult`. This keeps provider SDKs, E2B, GitHub, Vercel, and Cloud
Run credentials outside the coordinator. The production gateway should first
surface the graph and request an approval record for privileged nodes; only the
approved action endpoint may call `RunMode.APPROVED`.

## Verification

`tests/test_meta_orchestrator.py` checks graph composition, default non-
execution, capability approval gates, dependency ordering, budget boundaries,
and the controller handoff. Run it together with the existing budget and step
telemetry tests before attaching live adapters.
