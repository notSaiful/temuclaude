"""Permissioned, bounded coordination across TemuClaude specialist workers.

This module is intentionally a *control plane*, not another model provider.  It
turns a user goal into a small dependency graph, applies budget and capability
constraints, and can dispatch the graph only to explicitly supplied worker
adapters.  The default ``shadow`` mode never invokes an adapter.  That makes it
safe to observe and evaluate a multi-worker strategy before it is allowed to
change a repository, call a provider, or create a deployment.

The module does not accept shell commands, credentials, or arbitrary tool
names.  Privileged capabilities must be approved by the caller for every run.
"""

from __future__ import annotations

import asyncio
import hashlib
import inspect
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, FrozenSet, Iterable, Mapping, Optional, Sequence, Tuple

from src.budget_controller import ControllerDecision, recommend_controller_action
from src.step_telemetry import record_step_event


class Capability(str, Enum):
    """Capabilities a worker can request; not a mechanism for executing them."""

    TEXT = "text"
    RESEARCH = "research"
    MEDIA = "media"
    AUDIO = "audio"
    WORKSPACE_READ = "workspace_read"
    FILE_WRITE = "file_write"
    COMMAND_RUN = "command_run"
    NETWORK = "network"
    GITHUB = "github"
    DEPLOY = "deploy"
    VERIFICATION = "verification"


PRIVILEGED_CAPABILITIES: FrozenSet[Capability] = frozenset(
    {
        Capability.FILE_WRITE,
        Capability.COMMAND_RUN,
        Capability.NETWORK,
        Capability.GITHUB,
        Capability.DEPLOY,
    }
)


class MetaOrchestratorError(ValueError):
    """Raised when an untrusted or invalid coordination request is supplied."""


class RunMode(str, Enum):
    SHADOW = "shadow"
    APPROVED = "approved"


class NodeState(str, Enum):
    PLANNED = "planned"
    SHADOWED = "shadowed"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class WorkerSpec:
    """A fixed allow-listed specialist and its declared capabilities."""

    name: str
    capabilities: FrozenSet[Capability]
    cost_units: float
    description: str


@dataclass(frozen=True)
class TaskNode:
    """One bounded unit of specialist work in a plan."""

    id: str
    worker: str
    objective: str
    dependencies: Tuple[str, ...] = ()
    required_capabilities: FrozenSet[Capability] = frozenset()
    estimated_cost_units: float = 0.0
    verification_required: bool = True

    @property
    def approval_required(self) -> bool:
        return bool(self.required_capabilities & PRIVILEGED_CAPABILITIES)


@dataclass(frozen=True)
class MetaPlan:
    """Serializable bounded graph produced without invoking a provider."""

    id: str
    goal: str
    task_type: str
    nodes: Tuple[TaskNode, ...]
    max_cost_units: float
    estimated_cost_units: float
    mode: RunMode = RunMode.SHADOW

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "task_type": self.task_type,
            "max_cost_units": self.max_cost_units,
            "estimated_cost_units": self.estimated_cost_units,
            "mode": self.mode.value,
            "nodes": [
                {
                    **asdict(node),
                    "required_capabilities": sorted(cap.value for cap in node.required_capabilities),
                    "approval_required": node.approval_required,
                }
                for node in self.nodes
            ],
        }


@dataclass(frozen=True)
class NodeResult:
    """Minimal, provider-neutral result returned by a worker adapter."""

    state: NodeState
    quality_score: Optional[float] = None
    cost_units: float = 0.0
    failure_label: Optional[str] = None
    output_metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MetaRun:
    """Outcome of a shadow or explicitly approved execution attempt."""

    plan_id: str
    mode: RunMode
    results: Mapping[str, NodeResult]
    controller_decision: ControllerDecision

    @property
    def completed(self) -> bool:
        return bool(self.results) and all(
            result.state in {NodeState.SUCCEEDED, NodeState.SHADOWED, NodeState.SKIPPED}
            for result in self.results.values()
        )


WorkerHandler = Callable[[TaskNode, Mapping[str, NodeResult]], Awaitable[NodeResult] | NodeResult]


DEFAULT_WORKERS: Mapping[str, WorkerSpec] = {
    "text": WorkerSpec("text", frozenset({Capability.TEXT}), 0.08, "Core reasoning and synthesis"),
    "deep_research": WorkerSpec(
        "deep_research",
        frozenset({Capability.RESEARCH, Capability.NETWORK}),
        0.28,
        "Source-grounded research pipeline",
    ),
    "media_image": WorkerSpec("media_image", frozenset({Capability.MEDIA}), 0.30, "Image generation pipeline"),
    "media_video": WorkerSpec("media_video", frozenset({Capability.MEDIA}), 0.65, "Video generation pipeline"),
    "audio": WorkerSpec("audio", frozenset({Capability.AUDIO}), 0.22, "Speech and music pipeline"),
    "workspace": WorkerSpec(
        "workspace",
        frozenset({Capability.WORKSPACE_READ, Capability.FILE_WRITE, Capability.COMMAND_RUN}),
        0.24,
        "Permissioned repository planning and execution",
    ),
    "verifier": WorkerSpec("verifier", frozenset({Capability.VERIFICATION}), 0.06, "Independent quality gate"),
}


class MetaOrchestrator:
    """Create and dispatch small, auditable plans over known specialists.

    ``execute`` accepts worker handlers from the owning runtime.  Keeping the
    adapters outside this class prevents a planner response from gaining direct
    filesystem, shell, deployment, or credential access.
    """

    max_nodes = 6

    def __init__(self, workers: Optional[Mapping[str, WorkerSpec]] = None) -> None:
        self.workers = dict(workers or DEFAULT_WORKERS)
        self._validate_worker_registry()

    def _validate_worker_registry(self) -> None:
        if not self.workers:
            raise MetaOrchestratorError("At least one worker must be registered")
        for name, spec in self.workers.items():
            if name != spec.name or not name.replace("_", "").isalnum() or spec.cost_units < 0:
                raise MetaOrchestratorError("Worker registry contains an invalid worker specification")

    @staticmethod
    def _task_type(goal: str) -> str:
        text = goal.lower()
        if any(token in text for token in ("research", "investigate", "compare", "source", "citation")):
            return "research"
        if any(token in text for token in ("image", "illustration", "logo", "video", "animation")):
            return "media"
        if any(token in text for token in ("code", "website", "app", "bug", "repo", "deploy", "file")):
            return "workspace"
        if any(token in text for token in ("voice", "speech", "music", "podcast", "audio")):
            return "audio"
        return "general"

    @staticmethod
    def _contains(goal: str, tokens: Iterable[str]) -> bool:
        lowered = goal.lower()
        return any(token in lowered for token in tokens)

    @staticmethod
    def _plan_id(goal: str) -> str:
        normalized = " ".join(goal.split()).lower()
        return "meta-" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

    def _node(self, worker: str, objective: str, dependencies: Sequence[str] = ()) -> TaskNode:
        try:
            spec = self.workers[worker]
        except KeyError as error:
            raise MetaOrchestratorError("Plan requested a worker outside the allow-list") from error
        return TaskNode(
            id=worker,
            worker=worker,
            objective=objective[:500],
            dependencies=tuple(dependencies),
            required_capabilities=spec.capabilities,
            estimated_cost_units=spec.cost_units,
        )

    def plan(self, goal: str, *, max_cost_units: float = 1.0) -> MetaPlan:
        """Build a deterministic, bounded graph; no provider or tool is called."""
        clean_goal = " ".join((goal or "").split())
        if not clean_goal:
            raise MetaOrchestratorError("A non-empty goal is required")
        if len(clean_goal) > 8_000:
            raise MetaOrchestratorError("Goal exceeds the 8,000 character planning limit")
        if not isinstance(max_cost_units, (int, float)) or not 0 < float(max_cost_units) <= 10:
            raise MetaOrchestratorError("max_cost_units must be between 0 and 10")

        nodes = [self._node("text", "Frame the goal, constraints, and expected deliverable.")]
        task_type = self._task_type(clean_goal)
        if task_type == "research":
            nodes.append(self._node("deep_research", "Collect and synthesize authoritative evidence.", ("text",)))
        elif task_type == "workspace":
            nodes.append(self._node("workspace", "Prepare a bounded implementation proposal and verification plan.", ("text",)))
        elif task_type == "audio":
            nodes.append(self._node("audio", "Produce the requested audio artifact through the audio pipeline.", ("text",)))

        if self._contains(clean_goal, ("image", "illustration", "logo")):
            nodes.append(self._node("media_image", "Generate and evaluate the requested image artifact.", ("text",)))
        if self._contains(clean_goal, ("video", "animation")):
            nodes.append(self._node("media_video", "Generate and evaluate the requested video artifact.", ("text",)))

        # Preserve the verifier even when optional workers are trimmed for budget.
        verifier = self._node("verifier", "Check worker outputs against the goal, safety boundary, and quality bar.")
        selected = []
        total = 0.0
        for node in nodes:
            if total + node.estimated_cost_units + verifier.estimated_cost_units <= float(max_cost_units):
                selected.append(node)
                total += node.estimated_cost_units
        if not selected:
            raise MetaOrchestratorError("Budget is too small for the minimum safe planning path")
        verifier = TaskNode(
            **{**asdict(verifier), "dependencies": tuple(node.id for node in selected)}
        )
        selected.append(verifier)
        if len(selected) > self.max_nodes:
            raise MetaOrchestratorError("Plan exceeded its fixed node limit")
        total += verifier.estimated_cost_units
        return MetaPlan(
            id=self._plan_id(clean_goal),
            goal=clean_goal,
            task_type=task_type,
            nodes=tuple(selected),
            max_cost_units=float(max_cost_units),
            estimated_cost_units=round(total, 4),
        )

    @staticmethod
    def _approved(node: TaskNode, approvals: FrozenSet[Capability]) -> bool:
        return (node.required_capabilities & PRIVILEGED_CAPABILITIES).issubset(approvals)

    @staticmethod
    def _coerce_result(value: Any) -> NodeResult:
        if not isinstance(value, NodeResult):
            raise MetaOrchestratorError("Worker adapters must return NodeResult")
        if value.cost_units < 0:
            raise MetaOrchestratorError("Worker adapter returned a negative cost")
        return value

    def evaluate(self, plan: MetaPlan, results: Mapping[str, NodeResult]) -> ControllerDecision:
        """Convert aggregate results into the existing conservative budget signal."""
        relevant = [results[node.id] for node in plan.nodes if node.id in results]
        failures = [result for result in relevant if result.state in {NodeState.FAILED, NodeState.BLOCKED}]
        quality = [result.quality_score for result in relevant if result.quality_score is not None]
        spent = sum(result.cost_units for result in relevant)
        remaining = max(0.0, plan.max_cost_units - spent) / plan.max_cost_units
        verifier = results.get("verifier")
        verifier_passed = verifier is not None and verifier.state == NodeState.SUCCEEDED
        return recommend_controller_action(
            task_type=plan.task_type,
            tier="hard" if len(plan.nodes) >= 4 else "medium",
            step_type="verification",
            remaining_budget_ratio=remaining,
            progress_delta=1.0 if verifier_passed else 0.0,
            uncertainty=1.0 - (sum(quality) / len(quality)) if quality else 0.7,
            failure_label=failures[0].failure_label if failures else None,
            verifier_passed=verifier_passed,
            success=not failures,
        )

    def record_shadow_telemetry(self, plan: MetaPlan, run: MetaRun, *, model: str = "meta-orchestrator") -> None:
        """Persist minimal evaluation signals without storing worker output.

        Call this from an observability boundary after a run, never as an
        implicit side effect of planning or execution.  ``record_step_event``
        stores only a query hash and summary metrics, so neither the goal nor a
        worker response is added to the local telemetry payload.
        """
        total_cost = sum(result.cost_units for result in run.results.values())
        for index, node in enumerate(plan.nodes):
            result = run.results.get(node.id)
            if result is None:
                continue
            record_step_event(
                query=plan.goal,
                task_type=plan.task_type,
                tier="hard" if len(plan.nodes) >= 4 else "medium",
                step_type=f"meta_{node.worker}",
                model=model,
                strategy="meta_orchestrator",
                success=result.state in {NodeState.SUCCEEDED, NodeState.SHADOWED},
                quality_score=result.quality_score,
                initial_budget=plan.max_cost_units,
                remaining_budget=max(0.0, plan.max_cost_units - total_cost),
                budget_spent=total_cost,
                failure_label=result.failure_label,
                controller_action=run.controller_decision.action,
                controller_confidence=run.controller_decision.confidence,
                controller_reason=run.controller_decision.reason,
                cost_risk=run.controller_decision.cost_risk,
                verifier_state=run.results.get("verifier", NodeResult(NodeState.SKIPPED)).state.value,
                sequence_index=index,
            )

    async def execute(
        self,
        plan: MetaPlan,
        *,
        handlers: Mapping[str, WorkerHandler],
        mode: RunMode = RunMode.SHADOW,
        approvals: Iterable[Capability] = (),
    ) -> MetaRun:
        """Run supplied adapters in dependency order, or safely shadow the plan.

        ``RunMode.APPROVED`` is still bounded: only registered handlers can be
        called, and a node needing a privileged capability is blocked until the
        caller grants every corresponding capability for this individual run.
        """
        if mode not in {RunMode.SHADOW, RunMode.APPROVED}:
            raise MetaOrchestratorError("Unsupported run mode")
        approved = frozenset(approvals)
        if not approved.issubset(PRIVILEGED_CAPABILITIES):
            raise MetaOrchestratorError("Only privileged capabilities can be approved")
        results: Dict[str, NodeResult] = {}
        spent = 0.0
        for node in plan.nodes:
            # Shadow evaluation deliberately records every intended node.  It
            # must not make a dependency look unavailable merely because no
            # adapter was called in this non-executing mode.
            if mode == RunMode.SHADOW:
                results[node.id] = NodeResult(NodeState.SHADOWED, output_metadata={"reason": "shadow_mode"})
                continue
            # Report a missing consent boundary explicitly, even if another
            # prerequisite also has not run.  That gives the UI an actionable
            # approval request rather than hiding it behind a generic skip.
            if not self._approved(node, approved):
                results[node.id] = NodeResult(NodeState.BLOCKED, failure_label="approval_required")
                continue
            if any(results[dependency].state != NodeState.SUCCEEDED for dependency in node.dependencies):
                results[node.id] = NodeResult(NodeState.SKIPPED, failure_label="dependency_not_satisfied")
                continue
            handler = handlers.get(node.worker)
            if handler is None:
                results[node.id] = NodeResult(NodeState.BLOCKED, failure_label="worker_handler_missing")
                continue
            if spent + node.estimated_cost_units > plan.max_cost_units:
                results[node.id] = NodeResult(NodeState.BLOCKED, failure_label="budget_cap_reached")
                continue
            try:
                result = handler(node, results)
                if inspect.isawaitable(result):
                    result = await result
                normalized = self._coerce_result(result)
                results[node.id] = normalized
                spent += normalized.cost_units
            except (MetaOrchestratorError, asyncio.CancelledError):
                raise
            except Exception:
                results[node.id] = NodeResult(NodeState.FAILED, failure_label="worker_execution_failed")
        return MetaRun(plan.id, mode, results, self.evaluate(plan, results))
