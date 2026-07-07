# Ollama API Integration — Discovered 2026-07-06

## API Endpoint

The correct Ollama API endpoint is `https://ollama.com/api/tags` (NOT `api.ollama.ai` which doesn't resolve).

Local Ollama proxy runs on `http://localhost:11434` and proxies to `ollama.com` cloud. Model names use `:cloud` suffix when accessed locally.

## Authentication

```
Authorization: Bearer <OLLAMA_API_KEY>
```

Ggs's key is stored in `/Users/saiful/temuclaude/.env`:
```
OLLAMA_API_KEY=451b60551d11471d8d7db094c4ad874d
OLLAMA_BASE_URL=http://localhost:11434
```

## Available Models (35 models as of 2026-07-06)

Key models with `:cloud` suffix for local proxy:

| Model | Context | Capabilities | Notes |
|-------|---------|-------------|-------|
| glm-5.2:cloud | 1M | completion, tools, thinking | Strongest general model |
| deepseek-v4-pro:cloud | 1M | completion, tools, thinking | Best for code |
| kimi-k2.6:cloud | 262k | completion, tools, thinking, vision | Multimodal |
| gpt-oss-120b:cloud | 131k | completion, tools, thinking | OpenAI open model |

Other notable models: qwen3-coder:480b, minimax-m3, mistral-large-3:675b, glm-5.1, kimi-k2.5, nemotron-3-ultra, deepseek-v3.2, gemini-3-flash-preview, devstral-2:123b, gpt-oss:20b, gemma4:31b, qwen3.5:397b

## API Calls

### List models
```bash
curl -H "Authorization: Bearer $OLLAMA_API_KEY" https://ollama.com/api/tags
# Or locally:
curl http://localhost:11434/api/tags
```

### Chat completion
```bash
curl http://localhost:11434/api/chat -d '{
  "model": "glm-5.2:cloud",
  "messages": [{"role": "user", "content": "Say hello"}],
  "stream": false,
  "options": {"num_predict": 100, "temperature": 0.0}
}'
```

### Response format
```json
{
  "model": "glm-5.2",
  "message": {"role": "assistant", "content": "...", "thinking": "..."},
  "done": true,
  "prompt_eval_count": 17,
  "eval_count": 10
}
```

Note: Ollama returns a `thinking` field separately from `content` — the content may be empty while thinking has the reasoning. Parse both.

## Cost

Ollama models cost $0 in the credit ledger. The model_optimizer_daemon should prefer Ollama free models first, only falling back to OpenRouter for models Ollama doesn't have. This eliminates or drastically reduces OpenRouter credit consumption — every credit saved is Ggs's tuition money.

## Direct Cloud API Access (no local daemon needed)

As of 2026-07-07, the Ollama cloud API can be called DIRECTLY without the local daemon. This means Hasan (and any deployed service) can use Ollama even when Ggs's device is off.

### Two Access Modes

1. **Local daemon** (device on): `http://localhost:11434/api/chat` — model names need `:cloud` suffix (e.g., `glm-5.2:cloud`)
2. **Direct cloud API** (anywhere): `https://ollama.com:443/api/chat` — model names have NO suffix (e.g., `glm-5.2`) — requires `Authorization: Bearer <key>` header

### Key That Works With Direct Cloud API

The original key (`451b60...`) only works with the local daemon (which uses SSH key auth to ollama.com internally). A new key (`eb9bdf...`, provided 2026-07-07) works directly with `https://ollama.com:443/api/chat`. If direct cloud API returns `{"error":"Unauthorized"}`, the key only works with the local daemon — get a key that works directly from the Ollama Max plan dashboard.

### Critical: num_predict Threshold

When `num_predict` is too low (5-10), ALL tokens go to the `thinking` field and `content` returns empty. With `num_predict: 100+`, content is populated. For chat responses, use `num_predict: 800` minimum.

### Response Parsing

Always check BOTH `content` and `thinking` fields:
```typescript
let response = data?.message?.content || '';
if (!response && data?.message?.thinking) {
  response = data.message.thinking;
}
```

### Model Priorities (Ggs's choice, 2026-07-07)

glm-5.2 is PRIMARY. Fallback order: deepseek-v4-pro -> kimi-k2.6 -> gpt-oss:120b. All 4 are on the Max plan. Round-robin distributes load to maximize weekly usage quotas.

### OpenRouter Free Tier Limitation

OpenRouter free models have a 50 requests/day limit that gets exhausted quickly. Do NOT rely on OpenRouter as the sole fallback. Ollama cloud direct API is the reliable path when the device is off. OpenRouter is a last resort that often returns 429 (rate limit exceeded).

### Next.js .env Override

Next.js `.env` file values OVERRIDE shell environment variables. To test with different env vars (e.g., dead Ollama URL for fallback testing), you must modify the `.env` file directly — setting `OLLAMA_BASE_URL=http://localhost:9999` in the shell won't work if `.env` has a different value.

### Timeout Budget

With `maxDuration: 60` (Next.js route limit) and 3 model fallback attempts, each fetch needs `AbortSignal.timeout(8000)` or less. 3 x 8s = 24s for Ollama, leaving 36s for OpenRouter fallback. Using 30s timeouts per model (90s total) causes the request to time out before reaching fallbacks.

## Cloud Deployment Consideration

On Oracle Cloud VM (production), there is no local Ollama. Set `OLLAMA_BASE_URL=https://ollama.com` directly. The API key authenticates to the cloud endpoint.