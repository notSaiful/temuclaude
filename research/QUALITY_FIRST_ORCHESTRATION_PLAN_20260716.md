# TemuClaude Upgrade Plan: Quality-First Specialist Orchestration

## Research Inputs

- Source: OpenRouter provider routing documentation (16 July 2026).
- Finding: provider selection is price-oriented by default and supports explicit fallbacks and parameter requirements.
- TemuClaude implication: quality policy must be owned by the application, not delegated to a price-oriented gateway.
- Source: Mixture-of-Agents (arXiv:2406.04692).
- Finding: layered agents improve generation by consuming the diverse outputs of the preceding layer.
- TemuClaude implication: nontrivial Pro work uses a diverse parallel panel followed by synthesis and verification.
- Source: Self-Consistency (arXiv:2203.11171).
- Finding: sampling and selecting consistent reasoning paths improves several reasoning benchmarks.
- TemuClaude implication: math retains specialist self-consistency in addition to heterogeneous panel evidence.

## Objective

- Quality metric: every Pro generation receives specialist planning/drafting/review rather than a cheap single-model route.
- Cost metric: low-cost routing is available only through `max_savings` or Lite.
- Latency metric: independent worker stages run concurrently; Pro retains a 300-second execution ceiling.
- Safety/reliability metric: every generated code artifact receives an independent verifier before repair or delivery.

## Evidence-Based Capability Matrix

| Model | Assigned role | Primary evidence |
|---|---|---|
| GLM-5.2 | long-horizon planning, project software engineering, synthesis | Z.AI describes the GLM line as coding/agent capable; the live OpenRouter registry describes GLM-5.2 as suited to long-horizon agents and project-level software engineering. |
| DeepSeek V4 Pro | math, STEM, coding, rigorous reasoning | DeepSeek's V4 release reports open-model leadership in math/STEM/coding and enhanced agentic coding. |
| Kimi K2.6 | coding-driven UI/UX and multi-agent implementation | The live OpenRouter registry describes K2.6 as designed for long-horizon coding, coding-driven UI/UX generation, and multi-agent orchestration. |
| MiniMax M3 | image/video understanding, creative/product review, long context | MiniMax documents native image/video input and 1M context; the live registry identifies M3 as a multimodal foundation model. |
| Gemini 3.5 Flash | visual UI, accessibility, computer interaction, multimodal/tool review | Google recommends Gemini 3.5 Flash for computer use across browser/mobile/desktop and documents its multimodal/tool capabilities. |
| GPT-5.6 Luna | fast independent GPT-family proposal and tool work | OpenAI classifies Luna as the cost-sensitive/high-volume GPT-5.6 tier with broad tool support. It is not labelled the frontier adjudicator. |
| GPT-5.6 Sol | frontier adjudication for complex professional reasoning/coding | OpenAI identifies Sol as the GPT-5.6 frontier model for complex professional work. |
| Grok 4.5 | coding agent, bug critic, repair, tool-heavy work | xAI identifies Grok 4.5 as its flagship for code and agentic tasks with function calling, search, and code execution. |
| Nemotron 3 Ultra | independent QA/falsification, reasoning, long-context/high-stakes review | NVIDIA identifies Nemotron 3 Ultra for frontier reasoning, complex agents, 1M context, high-stakes RAG, coding, and planning. |

Primary references: https://ai.google.dev/gemini-api/docs/computer-use,
https://api-docs.deepseek.com/news/news260424/,
https://docs.x.ai/developers/grok-4-5,
https://developers.openai.com/api/docs/models/gpt-5.6-luna,
https://developers.openai.com/api/docs/models/gpt-5.6-sol,
https://build.nvidia.com/nvidia/nemotron-3-ultra-550b-a55b/modelcard,
and the live OpenRouter `/api/v1/models` registry inspected 16 July 2026.

## Repo Touchpoints

- model/orchestration: `src/orchestrator.py`, `src/fusion.py`, `api_server.py`
- product runtime: `website/app/api/chat/route.ts`, `website/app/v1/chat/completions/route.ts`, `website/lib/openrouter.ts`
- tests: `tests/test_playground_code_generation_contract.py`, `tests/test_quality_first_orchestration.py`

## Implementation Phases

1. **Shadow telemetry:** implemented—retain per-model strategy and outcome logs for the new panel.
2. **Runtime gate:** implemented—quality-first is the Pro default and savings is explicitly opt-in.
3. **Provider quality policy:** implemented—Pro first avoids price-weighted and low-precision endpoints, then retries the exact approved model without the precision filter if strict endpoint availability would otherwise fail.
4. **Role specialization:** implemented—each Pro panel call receives a distinct capability prompt; Sol is the frontier adjudicator, Luna is a separate fast GPT worker, and GLM remains planner/synthesizer.
5. **Lite quality pipeline:** implemented—nontrivial Lite work uses two complementary allowlisted drafts in parallel, Qwen synthesis, Nemotron verification, and an allowlisted correction when needed.
6. **Benchmark promotion:** pending provider-backed evaluation of artifact completion, verifier pass rate, latency, and failure rate against the former direct route and named frontier baselines.
7. **Website/GitHub sync:** implementation docs updated; public superiority claims remain blocked until benchmark evidence exists.

## Rollback Plan

- Config/API: callers may set `budget_profile=max_savings` or select Lite.
- Fallback: model/provider availability fallbacks remain bounded to approved specialist routes.
- Failure threshold: provider or verifier failures keep the best successful deliverable; no failed critique can erase it.

## Verification Commands

```bash
PYTHONPATH=. pytest -q tests/test_orchestrator.py tests/test_updated_model_stack.py tests/test_playground_code_generation_contract.py
python3 -m py_compile src/orchestrator.py src/fusion.py api_server.py
cd website && npm run build
```
