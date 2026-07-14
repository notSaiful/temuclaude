"""Regression contracts for reliable Playground code generation."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_code_generation_has_parameter_compatible_fallbacks():
    route = (ROOT / "website/app/api/chat/route.ts").read_text()
    generation = route[route.index("async function runCodeGeneration"):route.index("// === FULL STACK")]

    assert "fallbacks: [POOL.fastRoute, POOL.orchestrator]" in generation
    assert "deadlineAt = t0 + 100_000" in generation
    assert "remainingMs() >= 6_000" in generation


def test_grok_repair_does_not_disable_mandatory_reasoning():
    route = (ROOT / "website/app/api/chat/route.ts").read_text()
    repair = route[route.index("result = await callModel(POOL.codeRepair"):route.index("const content = result.ok")]

    assert "disableReasoning: true" not in repair
    assert "timeoutMs: Math.min(30_000, remainingMs())" in repair


def test_playground_pro_pipeline_is_quality_first_and_has_runtime_headroom():
    route = (ROOT / "website/app/api/chat/route.ts").read_text()

    assert "export const maxDuration = 120" in route
    assert "quality-first-pro-panel" in route
    assert "taskType === 'creative'" in route
    assert "['knowledge', 'legal', 'health'].includes(taskType)" in route
    assert "qaScore < 0.82" in route
    assert "Promise.all(samples.map((sample) => scoreAnswer(query, sample)))" in route
    assert "Promise.all(steps.slice(0, 5).map" in route


def test_openrouter_timeout_is_shared_by_all_fallback_attempts():
    transport = (ROOT / "website/lib/openrouter.ts").read_text()

    assert "const deadlineAt = Date.now() + Math.max(1, timeoutMs)" in transport
    assert "const remainingTimeoutMs = () => Math.max(0, deadlineAt - Date.now())" in transport
    assert transport.count("if (attemptTimeoutMs < 250) break") >= 4
    assert "postAiml(candidate, messages, temperature, maxTokens, attemptTimeoutMs)" in transport


def test_openai_compatible_code_route_has_bounded_quality_fallbacks():
    route = (ROOT / "website/app/v1/chat/completions/route.ts").read_text()
    code_route = route[route.index("if (isCodeGen(q))"):route.index("// ── TRIVIAL")]

    assert "fallbacks: [M_GLM, M_GROK]" in code_route
    assert "timeoutMs: 100_000" in code_route
    assert "timeoutMs: 25_000" in route
    assert "}, 85_000);" in route


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
