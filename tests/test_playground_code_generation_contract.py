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


def test_code_panel_bounds_old_artifact_history_and_reports_the_whole_panel():
    route = (ROOT / "website/app/api/chat/route.ts").read_text()
    generation = route[route.index("async function runQualityCodeGeneration"):route.index("// === FULL STACK")]
    playground = (ROOT / "website/app/playground/page.tsx").read_text()

    assert "const codeMessages = compactArtifactMessages(messages);" in generation
    assert "const panelResults = [plan, draft, artifactCompletion" in generation
    assert "const completedRoles = panelResults.filter" in generation
    assert "function compactArtifactMessages" in route
    assert "maxCharacters = 18_000" in route
    assert "panel roles completed" in playground


def test_playground_pro_pipeline_is_quality_first_and_has_runtime_headroom():
    route = (ROOT / "website/app/api/chat/route.ts").read_text()

    assert "export const maxDuration = 300" in route
    assert "quality-first-pro-panel" in route
    assert "taskType === 'creative'" in route
    assert "['knowledge', 'legal', 'health'].includes(taskType)" in route
    assert "qaScore < 0.82" in route
    assert "Promise.all(samples.map((sample) => scoreAnswer(query, sample)))" in route
    assert "Promise.all(steps.slice(0, 5).map" in route


def test_playground_profiles_use_modal_when_modal_is_enabled():
    route = (ROOT / "website/app/api/chat/route.ts").read_text()

    assert "callModalChatCompletions" in route
    assert "const useModalOrchestration = isModalConfigured();" in route
    assert "techniques.push('modal-pro-orchestration')" in route
    assert "'modal-moa'" in route
    assert "profile === 'lite'" in route


def test_playground_counts_completed_modal_roles_not_the_gateway_request():
    route = (ROOT / "website/app/api/chat/route.ts").read_text()
    playground = (ROOT / "website/app/playground/page.tsx").read_text()

    assert "completed_models" in route
    assert "completedModels.map" in route
    assert "roles completed" in playground
    assert "execution details unavailable" in playground


def test_webpage_requests_are_code_artifacts_and_pro_never_single_routes():
    route = (ROOT / "website/app/api/chat/route.ts").read_text()

    assert "website|webpage|web page|site|web app" in route
    assert "if (isCodeGenerationRequest(query)) return 8;" in route
    assert "Every Pro request receives the full specialist panel" in route
    assert "pro-quality-floor" not in route


def test_every_profile_preserves_multi_model_orchestration_contracts():
    playground = (ROOT / "website/app/api/chat/route.ts").read_text()
    public_api = (ROOT / "website/app/v1/chat/completions/route.ts").read_text()

    assert "const useLitePanel = true;" in playground
    assert "pro-quality-floor" not in playground
    assert "Every Pro request receives the full specialist panel" in playground
    assert "Pro is an all-model product" in public_api
    assert "const toolPanelModels = [M_GLM, M_DEEPSEEK, M_MINIMAX, M_GEMINI, M_LUNA, M_GROK, M_NEMOTRON, M_KIMI];" in public_api


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
    assert "Pro is an all-model product" in route
    assert "call(M_LUNA, messages, temp, maxTok)" in route
    assert "call(M_KIMI, messages, temp, maxTok)" in route
    assert "M_SOL" not in route
    assert "call(M_KIMI, messages, temp, maxTok)" in route
    assert "call(M_GEMINI, messages, temp, maxTok)" in route
    assert "call(M_GROK, messages, temp, maxTok)" in route
    assert "timeoutMs: 25_000" in route


def test_openai_tool_adapter_accepts_hermes_write_file_kimi_and_deepseek_tool_shapes():
    route = (ROOT / "website/app/v1/chat/completions/route.ts").read_text()

    assert "names.includes('write_file')" in route
    assert "arg_value" in route
    assert "DeepSeek-family models can ignore the requested XML wrapper" in route
    assert "const dsmlInvoke = content.match" in route
    assert "<｜DSML｜parameter" in route
    assert "function firstJsonObject" in route
    assert "const jsonCall = firstJsonObject(rawCall)" in route
    assert "tool_calls" in route
    assert "toolCalls.length > 0 ? 'tool_calls' : 'stop'" in route
    assert "Tool turns are protocol-bound agent actions" in route
    assert "const toolResult = await call(M_KIMI, toolMessages, 0" in route
    assert "const toolPanelModels = [M_GLM, M_DEEPSEEK, M_MINIMAX, M_GEMINI, M_LUNA, M_GROK, M_NEMOTRON, M_KIMI];" in route
    assert "const toolMaxTokens = Math.max(4096" in route
    assert "fallbacks: [M_DEEPSEEK, M_GLM]" in route
    assert "timeoutMs: 180_000" in route
    assert "disableReasoning: true" in route


def test_both_pro_and_lite_use_capability_aware_quality_paths():
    playground = (ROOT / "website/app/api/chat/route.ts").read_text()
    public_api = (ROOT / "website/app/v1/chat/completions/route.ts").read_text()

    assert "lite-parallel-specialist-panel" in playground
    assert "const useLitePanel" in public_api
    assert "const [primaryDraft, complementaryDraft] = await Promise.all" in public_api
    for source in (playground, public_api):
        assert "synthesi" in source.lower()
        assert "gpt-5.6-sol" not in source
        assert "moonshotai/kimi-k3" in source
        assert "moonshotai/kimi-k2.6" not in source


def test_lite_uses_the_full_modal_panel_when_modal_is_configured():
    playground = (ROOT / "website/app/api/chat/route.ts").read_text()
    public_api = (ROOT / "website/app/v1/chat/completions/route.ts").read_text()

    assert "const useModalOrchestration = isModalConfigured();" in playground
    assert "completed = await runQualityCodeGeneration" in playground
    assert "profile === 'pro'\n          && process.env.TEMUCLAUDE_USE_MODAL_BACKEND" not in playground
    assert "if (isLiteModel(model) && !(useModalBackend && isModalConfigured()))" in public_api
    assert "const M_KIMI_FRONTIER = '~moonshotai/kimi-latest';" in public_api
    assert "call(M_KIMI_FRONTIER, messages, temp, maxTok)" in public_api


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
