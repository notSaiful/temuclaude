"""Regression contracts for reliable Playground code generation."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_code_generation_has_parameter_compatible_fallbacks():
    route = (ROOT / "website/app/api/chat/route.ts").read_text()
    generation = route[route.index("async function runQualityCodeGeneration"):route.index("// === FULL STACK")]

    assert "Promise.all([" in generation
    assert "POOL.orchestrator" in generation
    assert "POOL.specialist" in generation
    assert "POOL.uiUx" in generation
    assert "POOL.gptWorker" in generation
    assert "POOL.frontier" in generation
    assert "POOL.verifier" in generation
    assert "fallbacks: [POOL.codeRepair, POOL.orchestrator]" in generation
    assert "deadlineAt = t0 + 180_000" in generation
    assert "remainingMs() >= 6_000" in generation


def test_grok_repair_does_not_disable_mandatory_reasoning():
    route = (ROOT / "website/app/api/chat/route.ts").read_text()
    repair = route[route.index("const repaired = await callModel(POOL.codeRepair"):route.index("if (!deliveryIsUsable && remainingMs()")]

    assert "disableReasoning: true" not in repair
    assert "timeoutMs: Math.min(35_000, remainingMs())" in repair


def test_webpage_delivery_preserves_kimi_output_before_optional_recovery():
    route = (ROOT / "website/app/api/chat/route.ts").read_text()
    generation = route[route.index("async function runQualityCodeGeneration"):route.index("// === FULL STACK")]

    assert "Kimi is the primary user-facing webpage deliverer" in generation
    assert "deliveryCandidates.find(isUsableDeliverable)" in generation
    assert "let deliveryIsUsable = isUsableDeliverable(initialDeliverable)" in generation
    assert "let result = initialDeliverable;" in generation
    assert "if (!deliveryIsUsable)" in generation
    assert "direct-quality-delivery" in generation
    assert "fallbacks: [POOL.codeRepair, POOL.orchestrator]" in generation
    assert "function hasCompleteHtmlDocument" in route


def test_playground_pro_pipeline_is_quality_first_and_has_runtime_headroom():
    route = (ROOT / "website/app/api/chat/route.ts").read_text()

    assert "export const maxDuration = 300" in route
    assert "quality-first-pro-panel" in route
    assert "taskType === 'creative'" in route
    assert "['knowledge', 'legal', 'health'].includes(taskType)" in route
    assert "qaScore < 0.82" in route
    assert "Promise.all(samples.map((sample) => scoreAnswer(query, sample)))" in route
    assert "Promise.all(steps.slice(0, 5).map" in route


def test_hermes_and_playground_use_bounded_agent_and_visible_work_log_contracts():
    api = (ROOT / "website/app/v1/chat/completions/route.ts").read_text()
    playground = (ROOT / "website/app/playground/page.tsx").read_text()
    chat = (ROOT / "website/app/api/chat/route.ts").read_text()
    readme = (ROOT / "README.md").read_text()

    assert "const TEMUCLAUDE_AGENT_MODEL = 'temuclaude/temuclaude-agent';" in api
    assert "async function completeAgentTurn" in api
    assert "tier: 'agent-bounded-degraded'" in api
    assert "if (isAgentModel(model) && !agentArtifactRequest)" in api
    assert "const agentArtifactRequest = isAgentModel(model) && isCodeGen(latestUserText);" in api
    assert "isProModel(model) && !isLiteModel(model) && !agentArtifactRequest" in api
    assert "Routine agent turns use a bounded route" in readme
    assert "Creating an execution plan" in chat
    assert "turn this into a complete deliverable" in playground
    assert "rounded-sm border border-border-subtle bg-bg-secondary/40" in playground


def test_full_specialist_panel_is_used_and_reported_for_code_artifacts():
    api = (ROOT / "website/app/v1/chat/completions/route.ts").read_text()
    route = (ROOT / "website/app/api/chat/route.ts").read_text()
    generation = route[route.index("async function runQualityCodeGeneration"):route.index("// === FULL STACK")]

    assert "agentArtifactRequest" in api
    assert "isCodeGen(latestUserText)" in api
    assert "specialistPanel = [plan, draft, artifactCompletion, technicalReview, productReview, gptReview, frontierReview, multimodalReview, codeReview]" in generation
    assert "Specialist panel complete" in generation
    assert "specialistPanel.map((candidate)" in generation


def test_webpage_requests_are_code_artifacts_and_empty_trivial_responses_recover():
    route = (ROOT / "website/app/api/chat/route.ts").read_text()

    assert "website|webpage|web page|site|web app" in route
    assert "if (isCodeGenerationRequest(query)) return 8;" in route
    assert "pro-empty-response-recovery" in route
    assert "completed = await runFullStack(query, messages, controller, encoder, taskType, 'medium', t0, techniques);" in route


def test_openrouter_timeout_is_shared_by_all_fallback_attempts():
    transport = (ROOT / "website/lib/openrouter.ts").read_text()

    assert "const deadlineAt = Date.now() + Math.max(1, timeoutMs)" in transport
    assert "const remainingTimeoutMs = () => Math.max(0, deadlineAt - Date.now())" in transport
    assert transport.count("if (attemptTimeoutMs < 250) break") >= 4
    assert "postAiml(candidate, messages, temperature, maxTokens, attemptTimeoutMs)" in transport


def test_lite_rejects_truncated_artifacts_and_allows_quality_time():
    transport = (ROOT / "website/lib/openrouter-lite.ts").read_text()
    playground = (ROOT / "website/app/api/chat/route.ts").read_text()

    assert "finishReason === 'length'" in transport
    assert "120_000" in transport
    assert "isCodeGeneration ? 4_096" in playground
    assert "isCodeGeneration ? 90_000" in playground


def test_openai_compatible_code_route_has_bounded_quality_fallbacks():
    route = (ROOT / "website/app/v1/chat/completions/route.ts").read_text()
    classifier = route[route.index("function classify("):route.index("function isMath")]

    assert "if (isCodeGen) return 'hard';" in classifier
    assert "tier: 'direct-code-generation'" not in route
    assert "classifiedDifficulty === 'medium' ? 'hard'" in route
    assert "call(M_LUNA, messages, temp, maxTok)" in route
    assert "call(M_SOL, messages, temp, maxTok)" in route
    assert "call(M_KIMI, messages, temp, maxTok)" in route
    assert "call(M_GEMINI, messages, temp, maxTok)" in route
    assert "call(M_GROK, messages, temp, maxTok)" in route
    assert "timeoutMs: 25_000" in route
    assert "}, 85_000);" in route


def test_both_pro_and_lite_use_capability_aware_quality_paths():
    playground = (ROOT / "website/app/api/chat/route.ts").read_text()
    public_api = (ROOT / "website/app/v1/chat/completions/route.ts").read_text()

    assert "lite-parallel-specialist-panel" in playground
    assert "const useLitePanel" in public_api
    assert "const [primaryDraft, complementaryDraft] = await Promise.all" in public_api
    for source in (playground, public_api):
        assert "synthesi" in source.lower()
        assert "gpt-5.6-sol" in source
        assert "moonshotai/kimi-k2.6" in source


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
