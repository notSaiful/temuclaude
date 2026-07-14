"""Regression contracts for reliable Playground code generation."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_code_generation_has_parameter_compatible_fallbacks():
    route = (ROOT / "website/app/api/chat/route.ts").read_text()
    generation = route[route.index("async function runCodeGeneration"):route.index("// === FULL STACK")]

    assert "fallbacks: [POOL.fastRoute, POOL.orchestrator]" in generation
    assert "deadlineAt = Date.now() + 55_000" in generation
    assert "remainingMs() >= 6_000" in generation


def test_grok_repair_does_not_disable_mandatory_reasoning():
    route = (ROOT / "website/app/api/chat/route.ts").read_text()
    repair = route[route.index("result = await callModel(POOL.codeRepair"):route.index("const content = result.ok")]

    assert "disableReasoning: true" not in repair
    assert "timeoutMs: Math.min(16_000, remainingMs())" in repair


def test_playground_project_surface_is_removed_without_removing_artifacts():
    page = (ROOT / "website/app/playground/page.tsx").read_text()

    for removed in (
        "/api/projects",
        "activeWorkspaceProjectId",
        "Save to project",
        ">Projects<",
        "Project preview",
    ):
        assert removed not in page

    for retained in ("Run isolated preview", "Download .html", "<CodeArtifact content={message.content} />"):
        assert retained in page
