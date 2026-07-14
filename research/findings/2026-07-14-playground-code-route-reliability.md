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
