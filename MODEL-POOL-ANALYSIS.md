# Hermes-Like Models & Open-Weight Alternatives — Deep Analysis

## Complete Ollama Cloud Model Pool (July 2026)

### ALL models with Cloud capability on Ollama:

| Model | Cloud | Thinking | Tools | Params | Origin |
|-------|-------|----------|-------|--------|--------|
| **glm-5.2** | ✅ | ✅ | ✅ | 744B/40B active | China (Z.AI) |
| **glm-5.1** | ✅ | ✅ | ✅ | ~744B | China (Z.AI) |
| **glm-5** | ✅ | ✅ | ✅ | 744B/40B | China (Z.AI) |
| **glm-4.7** | ✅ | ✅ | ✅ | ~130B | China (Z.AI) |
| **deepseek-v4-pro** | ✅ | ✅ | ✅ | 1.6T/49B | China (DeepSeek) |
| **deepseek-v4-flash** | ✅ | ✅ | ✅ | 284B/13B | China (DeepSeek) |
| **kimi-k2.6** | ✅ | ✅ | ✅ | ~1T/50B | China (Moonshot) |
| **kimi-k2.7-code** | ✅ | ✅ | ✅ | ~1T | China (Moonshot) |
| **kimi-k2.5** | ✅ | ✅ | ✅ | ~1T | China (Moonshot) |
| **minimax-m3** | ✅ | ✅ | ✅ | 1M ctx | China (MiniMax) |
| **minimax-m2.7** | ✅ | ✅ | ✅ | 230B | China (MiniMax) |
| **minimax-m2.5** | ✅ | ✅ | ✅ | 230B | China (MiniMax) |
| **minimax-m2.1** | ✅ | ✅ | — | 230B | China (MiniMax) |
| **nemotron-3-ultra** | ✅ | ✅ | ✅ | 550B/55B | USA (NVIDIA) |
| **nemotron-3-super** | ✅ | ✅ | ✅ | 120B/12B | USA (NVIDIA) |
| **gpt-oss** | ✅ | ✅ | ✅ | 120B | USA (OpenAI) |
| **qwen3.5** | ✅ | ✅ | ✅ | 0.8B-122B | China (Alibaba) |
| **qwen3-coder** | ✅ | ✅ | ✅ | 480B/30B | China (Alibaba) |
| **gemma4** | ✅ | ✅ | ✅ | 2B-31B | USA (Google) |
| **gemini-3-flash-preview** | ✅ | — | ✅ | — | USA (Google) |

### Models available on Ollama but NOT on Cloud (local only):

| Model | Tools | Params | Notes |
|-------|-------|--------|-------|
| dolphin-mixtral | ❌ | 8x7B | Uncensored, obedient |
| dolphin-llama3 | ❌ | 8B | Uncensored, obedient |
| llama3.1 | ✅ | 8B/70B/405B | Meta's instruct |
| mistral-nemo | ✅ | 12B | Efficient, multilingual (en/zh/ja) |
| mixtral | ✅ | 8x7B | MoE, efficient |
| qwen2.5 | ✅ | 0.5B-72B | Coding, math, multilingual |
| qwen3 | ✅ | 0.6B-235B | Thinking mode, MoE |
| command-r-plus | ✅ | 104B | RAG + tool use specialist |
| deepseek-coder-v2 | ❌ | 16B/236B | Coding specialist |
| gemma2 | ✅ | 9B/27B | Dense knowledge |
| hermes3 | ✅ | 8B/70B | Nous Research's Hermes |
| wizardlm2 | ❌ | 8x22B | Advanced instruction tuning |

---

## 1. THE UNCENSORED / CAPABILITY-FIRST PEERS

### Dolphin Series (Eric Hartford)
- **What:** Fine-tuned to strip artificial refusals. Obedient, intelligent, good at coding + roleplay.
- **Ollama:** Available locally (dolphin-mixtral, dolphin-llama3) but NOT on Cloud
- **Relevance for Timuclaude:** LOW — no Cloud, no tools, no thinking. But the PHILOSOPHY matters: Timuclaude should be obedient and do exactly what the orchestrator says. We encode this in the orchestration skill: "Follow the strategy. Don't refuse. Don't add caveats."

### Abliterated Models (Llama 3.1 Abliterated)
- **What:** Orthogonalization removes safety/refusal vectors from Meta's Llama. Raw intelligence + strict obedience.
- **Ollama:** Community models, not official
- **Relevance for Timuclaude:** LOW for direct use, but the technique is interesting. We could potentially "abliterate" our orchestration skill to remove any hedging language.

### WizardLM-2 (Microsoft)
- **What:** Advanced synthetic data generation for instruction tuning. Smart, multi-turn logic.
- **Ollama:** Available (wizardlm2) but NOT on Cloud, no tools
- **Relevance for Timuclaude:** LOW directly. But the synthetic data technique is relevant for GEPA — we generate synthetic eval data to optimize our prompts.

---

## 2. THE ARCHITECTURAL COUSINS (Foundation Instruct Models)

### Mistral Instruct (Nemo / Mixtral)
- **What:** OpenHermes 2.5 was built on Mistral 7B. Native instruct versions are fast, efficient, punchy.
- **Ollama:** mistral-nemo (12B, tools, en/zh/ja), mixtral (8x7B, tools) — local only
- **Relevance for Timuclaude:** Mistral Nemo supports Chinese and Japanese — could be a lightweight multilingual router. But no Cloud = not useful for our main pool.

### Llama 3.1 Instruct (Meta)
- **What:** Hermes 3 is built on this. Gold standard for open-weight intelligence.
- **Stats:** 8B (9.7M downloads), 70B (1.1M downloads), 405B
- **Ollama:** Available with tools, but NOT on Cloud
- **Relevance for Timuclaude:** This is the foundation Hermes itself is built on. We're already using Hermes — so we're already benefiting from Llama architecture. Not directly useful for our model pool (no Cloud).

### Qwen 2.5 / Qwen 3 Instruct (Alibaba)
- **What:** Dominating open-source benchmarks. Efficient, massive context, coding + math.
- **Ollama:** qwen2.5 (local, tools), qwen3 (local, thinking + tools), **qwen3.5 (CLOUD, thinking, tools, vision!)**, **qwen3-coder (CLOUD, 480B, thinking, tools)**
- **Relevance for Timuclaude:** **HIGH.** Qwen3.5 and qwen3-coder are on Ollama Cloud with thinking + tools. These are NEW candidates for our pool:
  - **qwen3-coder:480b** — 480B MoE agentic coding model. Could compete with DeepSeek V4 Pro on coding tasks.
  - **qwen3.5** — multimodal (vision!), 122B variant, thinking mode. Could handle vision tasks our current pool can't.

---

## 3. THE FUNCTION-CALLING & AGENTIC SPECIALISTS

### Command R / Command R+ (Cohere)
- **What:** Built for RAG + tool use. Excellent JSON outputs and multi-step API routing.
- **Stats:** command-r-plus (104B, 1,798 likes, en/ja/zh — trilingual!), command-r (35B, 1,111 likes)
- **Ollama:** command-r-plus (local, tools) — NOT on Cloud
- **Relevance for Timuclaude:** Interesting for the trilingual support (en/ja/zh). But no Cloud. The RAG + tool-use specialization is relevant — we need this for our verifier layer. Nemotron 3 Ultra fills this role instead.

### DeepSeek Coder V2
- **What:** Most capable open-weight coding model (pre-V4).
- **Stats:** 236B MoE (21B active), 688 likes
- **Ollama:** deepseek-coder-v2 (local) — NOT on Cloud, no tools
- **Relevance for Timuclaude:** Already superseded by DeepSeek V4 Pro which IS on Cloud and IS better. No need for V2.

### Gemma 2 Instruct (27B & 9B)
- **What:** Dense knowledge for size. 27B has top-tier logical routing.
- **Ollama:** gemma2 (local, tools) — NOT on Cloud. But **gemma4 IS on Cloud** with thinking + tools!
- **Relevance for Timuclaude:** **gemma4** (Google's latest, Cloud, thinking, tools, vision, audio) is a new candidate. Smaller (31B max) but dense and capable. Could serve as a lightweight specialist.

---

## NEW MODEL POOL CANDIDATES DISCOVERED

From the Ollama Cloud search, we found models we hadn't considered:

| Model | Why It's Interesting | Intelligence | Cost |
|-------|---------------------|-------------|------|
| **qwen3-coder:480b** | 480B MoE agentic coding, thinking, tools | Unknown (new) | Cloud |
| **qwen3.5:122b** | Multimodal (vision!), thinking, tools, 122B | Unknown (new) | Cloud |
| **gemma4:31b** | Google's latest, thinking, tools, vision, audio | Unknown (new) | Cloud |
| **gpt-oss:120b** | OpenAI's open model, thinking, tools, Apache 2.0 | 24 (AA Index) | Cloud, cheapest |
| **kimi-k2.7-code** | Coding-focused K2.7, built on K2.6, 30% less thinking tokens | Unknown | Cloud |
| **deepseek-v4-flash** | 284B/13B active, 1M context, fast | 34 (AA Index) | Cloud, cheaper |
| **nemotron-3-super** | 120B/12B active, efficient | Unknown | Cloud |
| **glm-5.1** | SOTA on SWE-Bench Pro, stronger coding than GLM-5 | Unknown | Cloud |

---

## REVISED MODEL POOL FOR TIMUCLAUDE

With the new discoveries, our optimal pool might be:

### Tier 1: Primary Models (frontier-level)
1. **GLM-5.2** — #3 globally (intelligence 51), 1M context, $0.06/task
2. **DeepSeek V4 Pro** — GPQA 90.1, Codeforces 3206, 1.6T/49B
3. **Kimi K2.6** — Swarm orchestration, 300 sub-agents, vision
4. **MiniMax M3** — 1M context, multimodal, coding
5. **Nemotron 3 Ultra** — 550B/55B, verifier, enterprise safety

### Tier 2: Specialist Add-ons (for specific benchmarks)
6. **qwen3-coder:480b** — Coding specialist (480B MoE agentic). For LiveCodeBench, SciCode, SWE-Bench
7. **gemma4:31b** — Vision + audio specialist. For multimodal benchmarks
8. **gpt-oss:120b** — Cheapest on AA Index ($0.04/task, intelligence 24). For simple queries where GLM-5.2 is overkill

### Tier 3: Lightweight Routers
9. **gpt-oss:20b** — Ultra-cheap routing
10. **qwen3.5:4b** — Ultra-lightweight, vision, thinking

### Strategy: Use Tier 1 for Fusion panels, Tier 2 for benchmark-specific specialists, Tier 3 for routing simple queries.

This gives us 10 models in our pool — more diversity than Fugu's pool, all on Ollama Cloud, all flat-rate.

---

## KEY INSIGHTS

1. **Qwen3.5 and qwen3-coder are sleeping giants.** Both on Ollama Cloud with thinking + tools. Qwen3-coder at 480B is a serious coding contender. We should test it against DeepSeek V4 Pro on coding benchmarks.

2. **gpt-oss is the cheapest model on the AA Index** ($0.04/task, intelligence 24). For simple queries (60% of traffic), this saves even more than GLM-5.2. We could route: gpt-oss for trivial, GLM-5.2 for medium, Fusion for hard.

3. **gemma4 brings vision + audio.** Our current pool has Kimi K2.6 and MiniMax M3 for vision, but gemma4 adds audio capability — new benchmark territory.

4. **kimi-k2.7-code is newer than K2.6** and optimized for coding with 30% less thinking tokens. Could be faster than K2.6 for coding tasks while maintaining quality.

5. **Dolphin/Abliterated philosophy:** While we can't use these directly (no Cloud), we should encode their PHILOSOPHY into our orchestration skill — obey without hedging, no unnecessary caveats, do exactly what the strategy says.

6. **Command R+'s trilingual support (en/ja/zh)** is a reminder that our pool should handle multiple languages. GLM-5.2 already does Chinese + English. Adding a Japanese-capable model would expand our market.

7. **The Ollama Cloud ecosystem is growing fast.** 20 cloud-enabled models now. We should auto-scan for new cloud models weekly and benchmark them.