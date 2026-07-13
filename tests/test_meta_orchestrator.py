import asyncio

import pytest

from src.meta_orchestrator import (
    Capability,
    MetaOrchestrator,
    MetaOrchestratorError,
    NodeResult,
    NodeState,
    RunMode,
)


def test_plan_coordinates_research_and_media_with_a_final_verifier():
    plan = MetaOrchestrator().plan("Research sustainable materials and create an illustration", max_cost_units=1.0)

    assert plan.task_type == "research"
    assert [node.id for node in plan.nodes] == ["text", "deep_research", "media_image", "verifier"]
    assert plan.nodes[-1].dependencies == ("text", "deep_research", "media_image")
    assert plan.nodes[-1].approval_required is False
    assert next(node for node in plan.nodes if node.id == "deep_research").approval_required is True


def test_workspace_execution_is_planned_but_cannot_run_without_each_approval():
    orchestrator = MetaOrchestrator()
    plan = orchestrator.plan("Fix the website code and deploy it", max_cost_units=1.0)
    workspace = next(node for node in plan.nodes if node.id == "workspace")

    assert workspace.approval_required is True
    run = asyncio.run(orchestrator.execute(plan, handlers={}, mode=RunMode.APPROVED))
    assert run.results["workspace"].state == NodeState.BLOCKED
    assert run.results["workspace"].failure_label == "approval_required"
    assert run.results["verifier"].state == NodeState.SKIPPED


def test_shadow_mode_never_calls_worker_handlers():
    plan = MetaOrchestrator().plan("Summarize this product strategy", max_cost_units=1.0)
    calls = []

    async def handler(node, results):
        calls.append(node.id)
        return NodeResult(NodeState.SUCCEEDED, quality_score=1.0)

    run = asyncio.run(MetaOrchestrator().execute(plan, handlers={"text": handler, "verifier": handler}))
    assert calls == []
    assert all(result.state == NodeState.SHADOWED for result in run.results.values())


def test_approved_handlers_run_in_order_and_feed_quality_controller():
    orchestrator = MetaOrchestrator()
    plan = orchestrator.plan("Fix a website bug", max_cost_units=1.0)
    calls = []

    def handler(node, results):
        calls.append(node.id)
        return NodeResult(NodeState.SUCCEEDED, quality_score=0.95, cost_units=0.01)

    run = asyncio.run(
        orchestrator.execute(
            plan,
            handlers={"text": handler, "workspace": handler, "verifier": handler},
            mode=RunMode.APPROVED,
            approvals={Capability.FILE_WRITE, Capability.COMMAND_RUN},
        )
    )
    assert calls == ["text", "workspace", "verifier"]
    assert run.results["verifier"].state == NodeState.SUCCEEDED
    assert run.controller_decision.action == "stop"


def test_budget_and_contract_inputs_are_bounded():
    orchestrator = MetaOrchestrator()
    with pytest.raises(MetaOrchestratorError):
        orchestrator.plan("x", max_cost_units=0.01)
    with pytest.raises(MetaOrchestratorError):
        orchestrator.plan("x" * 8_001)
    plan = orchestrator.plan("Summarize", max_cost_units=1.0)
    with pytest.raises(MetaOrchestratorError):
        asyncio.run(orchestrator.execute(plan, handlers={}, approvals={Capability.TEXT}))


def test_shadow_telemetry_excludes_worker_output(monkeypatch):
    orchestrator = MetaOrchestrator()
    plan = orchestrator.plan("Summarize safely", max_cost_units=1.0)
    run = asyncio.run(orchestrator.execute(plan, handlers={}))
    events = []

    monkeypatch.setattr("src.meta_orchestrator.record_step_event", lambda **event: events.append(event))
    orchestrator.record_shadow_telemetry(plan, run)

    assert len(events) == len(plan.nodes)
    assert all(event["strategy"] == "meta_orchestrator" for event in events)
    assert all("output" not in event for event in events)
    assert all(event["query"] == plan.goal for event in events)
