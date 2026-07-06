# TEMUCLAUDE — ai/ml API MODEL RESEARCH
## Deep research into ai/ml API catalog for models that improve the stack
## Date: July 6, 2026

---

## METHODOLOGY

1. Fetched full ai/ml API model catalog (216 LLM chat models from 22 developers)
2. Filtered for non-OpenAI/Google/Anthropic models (103 alternative/open-weight models)
3. Cross-referenced against current Temuclaude stack (FINAL-MODEL-POOL.md)
4. Scraped ai/ml pricing page for per-model pricing
5. Identified models that could improve specific roles in the stack
6. Categorized by priority (HIGH/MEDIUM/LOW) based on clear improvements

---

## CURRENT STACK (for comparison)

| Role | Model | IQ | Cost | Context |
|------|-------|----|------|---------|
| Orchestrator | GLM-5.2 | 51 | $0.93/$3.00/M | 1M |
| Reasoning | DeepSeek V4 Pro | 44 | $0.435/$0.87/M | 1M |
| Fast/cheap | DeepSeek V4 Flash | 40 | $0.09/$0.18/M | 1M |
| Vision/Verifier | MiniMax M3 | 44 | $0.30/$1.20/M | 1M (524K on ai/ml) |
| Verifier (free) | Nemotron 3 Ultra | 38 | FREE (OpenRouter) | 262K on ai/ml |
| Long context | Kimi K2.6 | 43 | REJECTED ($0.66/$3.41, slow) | 262K |

---

## MODELS ADDED TO AIML_MODELS IN models.py

### HIGH PRIORITY (clear improvements)

#### 1. Qwen3.5-Flash (alibaba/qwen3.5-flash)
- **Price:** $0.13/M (ai/ml)
- **Context:** 1M tokens
- **Role:** Fast/cheap tier alternative to DeepSeek V4 Flash
- **Why:** Same 1M context as DeepSeek V4 Flash, similar price. Having both gives fallback redundancy across two providers.
- **Risk:** IQ unverified on ArtificialAnalysis, but Qwen3.5 series is well-established

#### 2. Nemotron 3 Super 120B (nvidia/nemotron-3-super-120b-a12b)
- **Price:** $0.117/M (ai/ml) — 5x cheaper than Nemotron Ultra on ai/ml ($0.65)
- **Context:** 262K tokens
- **Role:** Ultra-cheap verifier fallback
- **Why:** When OpenRouter free tier is rate-limited, this is the cheapest verifier. 120B/12B MoE is smart enough for QA gating.
- **Risk:** Lower IQ than Nemotron Ultra, but for QA checking (not generating), sufficient

#### 3. Nemotron 3 Nano 30B (nvidia/nemotron-3-nano-30b-a3b)
- **Price:** $0.065/M (ai/ml) — CHEAPEST model available
- **Context:** 262K tokens
- **Role:** Ultra-cheap trivial router
- **Why:** For "what is 2+2" level queries. 30B/3B MoE at $0.065/M is unbeatable for trivial tier.
- **Risk:** Low intelligence, but trivial queries don't need high IQ

#### 4. Qwen3 VL Plus (alibaba/qwen3-vl-plus)
- **Price:** $0.26/M (ai/ml) — cheaper than MiniMax M3 ($0.39/M on ai/ml)
- **Context:** 262K tokens
- **Role:** Vision specialist — cheaper alternative to MiniMax M3
- **Why:** Vision-language with hybrid thinking. 33% cheaper than MiniMax M3 on ai/ml. Can serve as vision fallback.
- **Risk:** 262K context vs MiniMax M3's 524K. But most vision queries don't need 524K.

### MEDIUM PRIORITY (situational improvements)

#### 5. LongCat 2.0 (meituan/longcat-2.0) — UNIQUE TO ai/ml
- **Price:** $0.975/M (ai/ml)
- **Context:** 1M tokens
- **Output:** 128K tokens
- **Role:** Long-context specialist (replaces rejected Kimi K2.6)
- **Why:** Trillion-parameter MoE, 1M context, native tool calling. Kimi K2.6 was rejected for cost/speed. LongCat is unique to ai/ml, cheaper, and has 1M context.
- **Risk:** No ArtificialAnalysis IQ score yet. Intelligence unverified.

#### 6. Qwen3-Coder 480B (alibaba/qwen3-coder-480b-a35b-instruct)
- **Price:** $1.95/M (ai/ml)
- **Context:** 262K tokens
- **Role:** Coding specialist for hardest tasks
- **Why:** 480B params, 35B active MoE — massive coding specialist. For hardest coding tasks where DeepSeek V4 Pro (IQ 44) might not be enough.
- **Risk:** 4x more expensive than DeepSeek V4 Pro ($0.435). Use only for hardest coding tier.

#### 7. Perplexity Sonar Pro (perplexity/sonar-pro) — UNIQUE CAPABILITY
- **Price:** Unknown (not on pricing page)
- **Context:** 200K tokens
- **Role:** Search-augmented queries (NEW CAPABILITY)
- **Why:** Built-in web search. Temuclaude currently CANNOT handle "latest", "current", "today", "recent" queries. Sonar Pro adds this capability — route time-sensitive queries to it.
- **Risk:** This is a new capability, not a replacement. Needs routing logic update.

#### 8. Qwen3.7-Max (alibaba/qwen3.7-max)
- **Price:** $2.6/M (ai/ml)
- **Context:** 1M tokens
- **Role:** Potential orchestrator alternative to GLM-5.2
- **Why:** Alibaba's flagship reasoning and agentic LLM. 1M context. If IQ is competitive with GLM-5.2 (51), could serve as orchestrator fallback.
- **Risk:** IQ unverified. More expensive than GLM-5.2 ($2.6 vs $1.82 output on ai/ml).

### LOW PRIORITY (monitor for benchmarks)

#### 9. Step 3.7 Flash (stepfun/step-3.7-flash)
- **Price:** $0.26/M (ai/ml)
- **Context:** 256K tokens
- **Role:** Cheap multimodal option
- **Why:** Multimodal MoE (text+image+video). Cheapest multimodal at $0.26/M.
- **Risk:** MiniMax M3 and Qwen3 VL Plus are better established. Only use as ultra-cheap multimodal fallback.

#### 10. ByteDance Seed 2.0 Pro/Lite (bytedance/seed-2-0-pro, bytedance/seed-2-0-lite)
- **Price:** Pro $0.65/M, Lite $0.325/M (ai/ml)
- **Context:** 256K tokens
- **Role:** General reasoning — unproven
- **Why:** Completely new family, unique to ai/ml. If benchmarks are competitive, could be cheaper alternatives.
- **Risk:** NO benchmark data available. Do NOT route to these until IQ is verified.

---

## MODELS REJECTED (not added)

| Model | Reason |
|-------|--------|
| Fugu Ultra (sakana) | $6.5/M — too expensive. Multi-agent system, not a standard LLM. Already a target to beat, not to use. |
| ERNIE 5.0 (baidu) | 128K context (too short). No pricing data. No benchmarks. |
| Command A (cohere) | Enterprise-focused, no pricing data, no benchmarks. |
| Hermes 4 405B (nousresearch) | 131K context (short). Open-weight, better suited for Ollama self-hosting than API. |
| Grok 4.3 (x-ai) | $3.25/M — more expensive than GLM-5.2 with no clear advantage. |
| Grok Code Fast 1 | $0.26/M, but Qwen3-Coder is better established for coding. |
| MiniMax M2 | Newer than M3 but no benchmarks. M3 is proven (IQ 44). |
| MiMo V2.5/V2.5 Pro (xiaomi) | No pricing data available. 1M context is good but can't evaluate without cost. |

---

## PRICING COMPARISON (ai/ml API, per 1M tokens)

| Model | ai/ml Price | OpenRouter Price | Notes |
|-------|------------|-----------------|-------|
| GLM-5.2 | $1.82 (output) | $0.93/$3.00 | OpenRouter cheaper for input |
| DeepSeek V4 Pro | $0.565 | $0.435/$0.87 | OpenRouter slightly cheaper |
| MiniMax M3 | $0.39 | $0.30/$1.20 | ai/ml cheaper for output |
| Nemotron 3 Ultra | $0.65 | FREE | OpenRouter FREE tier wins |
| Qwen3.5-Flash | $0.13 | N/A | Unique to ai/ml |
| Nemotron 3 Super | $0.117 | N/A | Unique to ai/ml |
| Nemotron 3 Nano | $0.065 | N/A | Cheapest on ai/ml |
| Qwen3 VL Plus | $0.26 | N/A | Cheaper than MiniMax M3 |
| LongCat 2.0 | $0.975 | N/A | Unique to ai/ml |
| Qwen3-Coder | $1.95 | N/A | Unique to ai/ml |
| Qwen3.7-Max | $2.6 | N/A | Unique to ai/ml |
| Step 3.7 Flash | $0.26 | N/A | Unique to ai/ml |

---

## IMPLEMENTATION NOTES

1. All new models added to `AIML_MODELS` dict in `/Users/saiful/temuclaude/src/models.py`
2. The orchestrator already has ai/ml fallback logic (orchestrator.py lines with `_HAS_AIML_KEY`)
3. To activate ai/ml backend, set `AIML_API_KEY` in `.env`
4. The 3-backend fallback chain is: Ollama → OpenRouter → ai/ml
5. New models are available as fallbacks but routing logic still uses the original 5-model pool
6. To use new models in routing, update `TASK_MODEL_MAP` and `FUSION_PANEL` in models.py

---

## NEXT STEPS (when ready)

1. **Get ai/ml API key** at https://aimlapi.com/app/billing/
2. **Set AIML_API_KEY** in `/Users/saiful/temuclaude/.env`
3. **Test new models** with a simple query to verify they work
4. **Update routing logic** to use new models for specific roles:
   - Route "latest"/"current" queries to Sonar Pro
   - Route >500K token queries to LongCat 2.0
   - Route hardest coding to Qwen3-Coder
   - Route vision queries to Qwen3 VL Plus (cheaper)
5. **Benchmark new models** against current stack on HLE/GPQA/Terminal-Bench
6. **Update FINAL-MODEL-POOL.md** with verified results

---

*Research sources: ai/ml API /v1/models endpoint (216 models), ai/ml pricing page (101 models with pricing), Temuclaude FINAL-MODEL-POOL.md, ArtificialAnalysis Intelligence Index v4.1.*