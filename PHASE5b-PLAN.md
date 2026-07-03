# Phase 5b Plan — OpenRouter Production Backend

## Why

Ollama Cloud limits concurrency (3 on Pro, 10 on Max). Can't serve multiple users.
OpenRouter has no concurrency limits — scales to thousands of concurrent requests.

## OpenRouter Pricing (verified from API, July 2026)

All 5 of our models are available on OpenRouter:

| Model | OpenRouter ID | Prompt $/token | Completion $/token |
|-------|--------------|----------------|-------------------|
| GLM-5.2 | z-ai/glm-5.2 | $0.00000093 | $0.000003 |
| DeepSeek V4 Pro | deepseek/deepseek-v4-pro | $0.000000435 | $0.00000087 |
| Kimi K2.6 | moonshotai/kimi-k2.6 | $0.00000066 | $0.00000341 |
| MiniMax M3 | minimax/minimax-m3 | $0.0000003 | $0.0000012 |
| Nemotron 3 Ultra | nvidia/nemotron-3-ultra-550b-a55b | $0.0000005 | $0.0000022 |
| GPT-OSS 120B | openai/gpt-oss-120b | $0.00000003 | $0.00000015 |

Also available FREE on OpenRouter:
- nvidia/nemotron-3-ultra-550b-a55b:free
- nvidia/nemotron-3-super-120b-a12b:free
- openai/gpt-oss-120b:free
- openai/gpt-oss-20b:free
- qwen/qwen3-coder:free
- qwen/qwen3-next-80b-a3b-instruct:free

## Cost Per Query (2K input + 1K output)

| Mode | Cost/query | vs Fable 5 ($0.07) |
|------|-----------|-------------------|
| Trivial (gpt-oss) | $0.0002 | 350x cheaper |
| Medium (single model) | $0.0017 | 41x cheaper |
| Hard (Fusion 3+1) | $0.0189 | 3.7x cheaper |
| Weighted avg (60/30/10) | $0.0025 | 28x cheaper |

## Pricing Tiers (adjusted for positive margins)

| Tier | Price | Queries/mo | Our Cost | Margin | Per Query |
|------|-------|-----------|----------|--------|-----------|
| Free | $0 | 100 | $0.25 | loss leader | $0 |
| Pro | $15 | 3,000 | $7.62 | 49% | $0.005 |
| Team | $99 | 20,000 | $50.82 | 49% | $0.005 |
| Enterprise | $499 | 200,000 | $508 | ~0% | $0.0025 |

Enterprise at 200K queries barely breaks even. Solution: Enterprise uses more trivial queries (80% trivial = lower cost). Or cap at 100K queries for $499.

## What We're Building

### 1. config/litellm-openrouter.yaml — OpenRouter LiteLLM config
- Same model mapping as Ollama config
- Uses OpenRouter API base: https://openrouter.ai/api/v1
- Auth: OPENROUTER_API_KEY env var
- Can use free models for trivial tier (gpt-oss:free, nemotron:free)

### 2. config/litellm-ollama.yaml — Rename current config
- Keep Ollama for local development
- Rename current litellm.yaml to litellm-ollama.yaml

### 3. config/litellm.yaml — Auto-detect backend
- If OPENROUTER_API_KEY is set → use OpenRouter
- If Ollama is running locally → use Ollama
- This is the default config that picks the right backend

### 4. src/models.py — Update model IDs
- Add OpenRouter model IDs alongside Ollama IDs
- Provider detection: which backend to use

### 5. .env.example — Add OPENROUTER_API_KEY

### 6. tests/test_phase5b.py — Test OpenRouter config
- Test config loads valid YAML
- Test all models present in OpenRouter config
- Test .env.example has OPENROUTER_API_KEY
- Test auto-detection logic

### 7. README — Update pricing with real OpenRouter numbers

### 8. landing_page.html — Update pricing section

## File Changes
1. NEW: config/litellm-openrouter.yaml
2. RENAME: config/litellm.yaml → config/litellm-ollama.yaml
3. NEW: config/litellm.yaml (auto-detect)
4. MODIFY: src/models.py (add OpenRouter IDs)
5. MODIFY: .env.example (add OPENROUTER_API_KEY)
6. NEW: tests/test_phase5b.py
7. MODIFY: README.md (update pricing)
8. MODIFY: landing_page.html (update pricing)