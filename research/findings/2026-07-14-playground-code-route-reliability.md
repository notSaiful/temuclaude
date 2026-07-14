# Playground code-route reliability — 2026-07-14

## Finding

The primary `deepseek/deepseek-v4-pro` code route was available, but the sequential
`x-ai/grok-4.5` repair request returned HTTP 400 because that endpoint requires
reasoning and the Playground explicitly disabled it. A primary timeout therefore
led directly to the user-facing unavailable message instead of a working repair.

Live, minimal OpenRouter probes confirmed that these configured routes accepted
the Playground request shape:

- `deepseek/deepseek-v4-pro`
- `deepseek/deepseek-v4-flash`
- `z-ai/glm-5.2`

## Implementation implication

Code generation should use DeepSeek V4 Pro with the Flash and GLM routes as
parameter-compatible provider fallbacks inside one bounded request. Grok 4.5 may
remain a final repair route only when its mandatory reasoning is left enabled.
All attempts must share a deadline below the Vercel function's 60-second limit.

The Playground Project UI was also removed at the user's request. Existing
project records and server APIs were left untouched so this UI change does not
destroy account data.

## Production follow-up

Vercel runtime logs later showed the remaining “currently unavailable” report
was a platform timeout, not an OpenRouter outage: `POST /api/chat` was terminated
at exactly 60 seconds. Direct minimal probes returned HTTP 200 for every active
Pro and Lite route (GLM-5.2, DeepSeek V4 Pro/Flash, MiniMax M3, Gemini 3.5 Flash,
GPT-5.6 Luna, Grok 4.5, Nemotron 3 Ultra, and Qwen 3.7 Plus).

The transport had interpreted `timeoutMs` per fallback attempt. A three-model
fallback could therefore run for roughly three times its declared budget. The
transport now shares one deadline across all provider/model attempts. The
Playground runtime is 120 seconds, independent PRM/step checks run in parallel,
and Pro uses a quality-first task-aware panel: MiniMax for creative work, Gemini
for knowledge/legal/health, and Nemotron for math/reasoning, always alongside
GLM and DeepSeek. Lite remains intentionally cost-bounded.
