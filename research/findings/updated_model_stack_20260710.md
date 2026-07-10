# Updated Model Stack Research Gate

Generated: 2026-07-10

## Decision

Promote an eight-role *candidate* stack to shadow-capable routing. Do not make
an unconditional claim that it beats Claude Fable 5. The claim that can be
tested is narrower: TemuClaude should seek the best observed quality/cost
Pareto point by using premium models only at steps where the expected gain is
larger than their incremental cost.

## Selected Roles

| Role | Model | Why | Runtime constraint |
|---|---|---|---|
| High-volume worker | DeepSeek V4 Flash | Lowest-cost capable long-context/tool worker | Default cheap route |
| Reasoning | DeepSeek V4 Pro | Strong math, coding, and technical reasoning | Direct specialist |
| Planning/synthesis | GLM-5.2 | Top open-weight intelligence signal and planning strength | Default orchestrator |
| Budget multimodal | MiniMax M3 | Image/video and million-token route at lower cost | Default multimodal |
| Premium multimodal | Gemini 3.5 Flash | Strong UI/tool/multimodal candidate | Requires `GOOGLE_API_KEY` |
| General escalation | GPT-5.6 Luna | Lower-cost closed frontier escalation | Requires `OPENAI_API_KEY`; only after QA failure |
| Coding escalation | Grok 4.5 | High-end coding-agent candidate | Requires `XAI_API_KEY` |
| Independent verifier | Nemotron 3 Ultra | Separate model family for critique/verification | Conditional verifier |

GPT-5.6 Terra is excluded from the active stack and additionally requires
`TEMUCLAUDE_ENABLE_TERRA_FALLBACK=true`. GPT-5.6 Sol is excluded.

## Evidence Summary

- DeepSeek's official pricing page lists V4 Flash at $0.14/M uncached input
  and $0.28/M output, and V4 Pro at $0.435/M and $0.87/M, with 1M context,
  tools, JSON output, and thinking modes.
- OpenRouter's June 2026 open-weight review places GLM-5.2 at 51 on the
  referenced Artificial Analysis index, above Nemotron 3 Ultra (48), MiniMax
  M3 (44), DeepSeek V4 Pro (44), and Kimi K2.6 (43). It identifies GLM as the
  planning/long-horizon coding option, M3 as the low-cost multimodal option,
  and DeepSeek Flash as the cost/performance route.
- Google's Gemini 3.5 Flash model card reports strong agentic, coding, UI, and
  multimodal results. Its $1.50/M input and $9/M output price means it is a
  specialist, not the default worker.
- xAI prices Grok 4.5 at $2/M input and $6/M output, and reports strong coding
  and terminal-agent results. It belongs in targeted repair/escalation rather
  than broad fusion.
- OpenAI prices GPT-5.6 Luna at $1/M input and $6/M output. Access is limited
  preview, so the route must degrade safely when unavailable. Terra costs
  $2.50/M input and $15/M output and remains emergency-only.
- Claude Fable 5 remains the peak single-model reference. Its $10/M input and
  $50/M output price makes it a poor default for a product whose objective is
  frontier-like quality at much lower blended cost.

## Implementation Implications

1. Do not route from a static eight-model panel. The default hard fusion panel
   is three diverse open models. The third cross-review layer is reserved for
   explicit max-quality mode.
2. Do not attempt premium calls without a provider key. Resolve unavailable
   Gemini, Luna, Grok, and Terra routes to an existing open-model fallback
   before sending a network request.
3. Do not invoke Luna based on query labels alone. Invoke it after the hard
   response fails the independent QA gate.
4. Do not enable Terra based on a model ID alone. Require a separate emergency
   feature flag in addition to the OpenAI credential.
5. Do not promote benchmark claims from vendor results. TemuClaude's existing
   promotion gate requires quality, cost, latency, and failure-rate evidence.

## Implemented Routing Controls

- The ordinary fusion panel is bounded to DeepSeek V4 Pro, GLM-5.2, and
  Nemotron 3 Ultra. Configuring a Gemini or xAI key no longer turns either
  premium model into an always-on fusion cost.
- Grok 4.5 is wired as a coding repair escalation. It is used only after the
  self-play critic finds a concrete flaw, and resolves to GLM-5.2 when the xAI
  provider credential is unavailable.
- Gemini 3.5 Flash is wired to screenshot-grounded UI review. When a screenshot
  is actually captured and the Google credential is present, the reviewer gets
  the image payload; otherwise the normal budget multimodal route or text
  verifier is used.
- The UI subagent research lane now uses DeepSeek V4 Flash rather than Kimi
  K2.6. Kimi remains a compatibility fallback rather than an active cost lane.
- GPT-5.6 Luna remains a QA-failure escalation, while Terra remains disabled
  behind both its provider credential and `TEMUCLAUDE_ENABLE_TERRA_FALLBACK`.

## Validation Status

Offline regression coverage verifies provider gating, budget-bounded fusion,
vision payload construction, and fallback behavior. This validates safety and
integration only; it is not a benchmark claim. Production promotion remains
blocked on a representative task packet with measured quality, token cost,
latency, and failure rates.

## Sources

- DeepSeek API pricing: https://api-docs.deepseek.com/quick_start/pricing/
- OpenRouter open-weight analysis: https://openrouter.ai/blog/insights/the-open-weight-models-that-matter-june-2026/
- Gemini 3.5 Flash model card: https://deepmind.google/models/model-cards/gemini-3-5-flash/
- Gemini API pricing: https://ai.google.dev/gemini-api/docs/pricing
- Grok 4.5: https://x.ai/news/grok-4-5
- GPT-5.6 preview, availability, and pricing: https://help.openai.com/en/articles/20001325-a-preview-of-gpt-5-6-sol-terra-and-luna
- RouteLLM: https://arxiv.org/abs/2406.18665
- FrugalGPT: https://arxiv.org/abs/2305.05176
