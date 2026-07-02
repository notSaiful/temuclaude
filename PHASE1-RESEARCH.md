# Phase 1 Research Findings

## Ollama Cloud — Confirmed Available Models

| Model | Cloud Tag | Architecture | Parameters | Context | Capabilities |
|-------|-----------|-------------|-----------|---------|-------------|
| GLM-5.2 | glm-5.2:cloud | glm5.2 | 756B | 1M | thinking, completion, tools |
| DeepSeek V4 Pro | deepseek-v4-pro:cloud | deepseek4 | 1.6T | — | — |
| DeepSeek V4 Flash | deepseek-v4-flash:cloud | deepseek4 | 158B | — | — |
| Kimi K2.6 | kimi-k2.6:cloud | kimi-k2 | 1.04T | — | — |
| Kimi K2.7 Code | kimi-k2.7-code:cloud | kimi-k2 | 1.04T | — | — |
| MiniMax M3 | minimax-m3:cloud | minimax-m3 | — | — | — |
| MiniMax M2.7 | minimax-m2.7:cloud | minimax-m2 | 229B | — | — |
| Nemotron 3 Ultra | nemotron-3-ultra:cloud | — | 550B | 262K | — |
| Nemotron 3 Super | nemotron-3-super:cloud | nemotron_h_moe | 120B | — | — |
| GPT-OSS 120B | gpt-oss:120b-cloud | gptoss | 117B | — | — |
| Qwen3 Coder 480B | qwen3-coder:480b-cloud | qwen3moe | 480B | — | — |

## Ollama Cloud Pricing (confirmed from ollama.com/pricing)

| Tier | Price | Cloud Models | Concurrent | Usage |
|------|-------|--------------|------------|-------|
| Free | $0 | Limited | 1 at a time | Basic |
| Pro | $20/mo or $200/yr | All | 3 at a time | 50x more than Free |
| Max | $100/mo | All | 10 at a time | 5x more than Pro |
| Team | Coming soon | All | Shared | — |

**KEY FINDING: Max tier ($100/mo) allows 10 concurrent cloud models.**
This means we can run 5 models in parallel for Fusion. Pro ($20/mo) only allows 3 concurrent — we'd need Max for full 5-model fusion.

**For development: start with Pro ($20/mo, 3 concurrent). Upgrade to Max ($100/mo) for full 5-model fusion and benchmark testing.**

## Ollama API Format
- OpenAI-compatible endpoint: `http://localhost:11434/v1/chat/completions`
- Model listing: `http://localhost:11434/v1/models`
- Cloud models use `:cloud` or `:Xb-cloud` suffix
- Currently only glm-5.2:cloud is pulled locally

## LiteLLM Proxy Research

### Configuration for Ollama:
```yaml
model_list:
  - model_name: timuclaude
    litellm_params:
      model: ollama_chat/glm-5.2:cloud
      api_base: http://localhost:11434
  - model_name: deepseek-v4-pro
    litellm_params:
      model: ollama_chat/deepseek-v4-pro:cloud
      api_base: http://localhost:11434
  # ... etc for each model
```

### Key Features Available:
- **Routing strategies**: simple-shuffle, least-busy, usage-based-routing, latency-based-routing
- **Fallbacks**: if model fails, automatically try next
- **Cost tracking**: per-request, per-user, per-model spend tracking
- **Rate limiting**: RPM/TPM limits per model
- **Caching**: Redis-backed response caching
- **Logging**: success_callback for Langfuse, custom callbacks
- **Adaptive Router**: bandit algorithm learns best model per task type (requires Postgres)
- **Virtual keys**: create API keys with spend limits

### For Timuclaude:
- Use `model_name: timuclaude` as the user-facing model
- Route to different Ollama Cloud models based on task
- Fallbacks: if one model fails, try another
- Cost tracking: track spend per query
- Logging: log every query for self-improvement

## Project Structure

```
/Users/saiful/timuclaude/
├── src/
│   ├── __init__.py
│   ├── orchestrator.py       # Main orchestration logic
│   ├── router.py              # Task classification + routing
│   ├── fusion.py              # Multi-model fusion pattern
│   ├── verifier.py            # Code execution + verification
│   ├── self_qa.py             # Self-QA gate
│   ├── consistency.py         # Self-consistency voting
│   ├── skills.py              # Skill auto-loading
│   └── logger.py              # Query logging
├── config/
│   ├── litellm.yaml           # LiteLLM proxy config
│   └── models.yaml            # Model pool configuration
├── tests/
│   └── test_orchestrator.py   # Basic tests
├── benchmarks/
│   ├── hle/                   # HLE eval scripts
│   ├── gdpval/                # GDPval eval scripts
│   └── mrcr/                  # MRCR eval scripts
├── research/                  # All research docs (already created)
├── hermes-backup/             # Memory backup
├── litellm_config.yaml        # Main config
├── requirements.txt
└── README.md
```

## Logging Schema

Each query logs:
```json
{
  "query_id": "uuid",
  "timestamp": "ISO-8601",
  "user_query": "the original question",
  "task_type": "math|coding|knowledge|reasoning|creative|agentic",
  "routing_tier": "trivial|medium|hard",
  "models_used": ["glm-5.2:cloud", "deepseek-v4-pro:cloud"],
  "strategy": "direct|fusion|self_consistency|code_verify",
  "responses": {...},
  "final_answer": "the synthesized response",
  "self_qa_score": 8,
  "confidence": 0.85,
  "latency_ms": 4500,
  "cost_estimate": 0.002,
  "success": true
}
```

## Phase 1 Research Summary

1. **Ollama Cloud**: 11 cloud models confirmed available. Max tier ($100/mo) needed for 5-model fusion (10 concurrent). Pro ($20/mo) for development (3 concurrent).
2. **LiteLLM**: Full proxy with routing, fallbacks, cost tracking, Adaptive Router. OpenAI-compatible. Configured via YAML.
3. **API**: Ollama provides OpenAI-compatible endpoint at localhost:11434/v1. LiteLLM proxy adds another OpenAI-compatible layer at localhost:4000.
4. **Architecture**: User → LiteLLM proxy (port 4000) → orchestration logic → Ollama Cloud models (port 11434).
5. **No blockers found.** Everything is available. Ready to build.