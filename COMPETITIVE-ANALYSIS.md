# Temuclaude — Competitive Landscape Analysis

## All Known Fable 5 Killers / Alternatives / Competitors

---

## 1. PERPLEXITY MODEL COUNCIL

**What it is:** Perplexity's multi-model feature launched Feb 5, 2026. Runs your query through 3 frontier models (GPT-5.2, Claude Opus 4.6, Gemini 3.0) in parallel, then a "chair" model (Claude Opus 4.5) synthesizes one unified answer.

**How it works:**
- 3 models answer independently in parallel
- Chair model reviews all 3 outputs
- Produces structured analysis: convergence (agreement), divergence (disagreement), unique insights
- Result shows where models agree and disagree

**Price:** $200/month (Perplexity Max only)
**Platform:** Web only

**Key insight for Temuclaude:** This is the SAME pattern as OpenRouter's Fusion Router — panel + judge + structured analysis. But Perplexity charges $200/mo and only uses 3 closed models. We can do the same with 5 open models on Ollama Cloud at $20-100/mo.

**What we take from it:** The "convergence/divergence/unique insights" framing is powerful for users. We should present our output the same way — show where models agreed (high confidence) and where they disagreed (flag for user review).

**What they DON'T do that we DO:**
- No skills (domain expertise injection)
- No tool verification (code execution)
- No self-consistency (majority voting)
- No MCTS (tree search)
- No self-improvement (Adaptive Router)
- No OPRO (prompt optimization)
- No open models (only closed frontier)
- No flat cost (per-query pricing)

---

## 2. SAKANA FUGU

**What it is:** Trained orchestrator model (SFT + evolutionary strategies + RL). Uses TRINITY (evolved coordinator) + Conductor (RL-trained workflow designer). Two tiers: Fugu (balanced) and Fugu Ultra (quality-first).

**Benchmarks (Fugu Ultra):**
- SWE-Bench Pro: 73.7 (beats Opus 4.8: 69.2, GPT-5.5: 58.6)
- Terminal-Bench 2.1: 82.1 (beats Opus 4.8: 74.6, GPT-5.5: 78.2)
- LiveCodeBench: 93.2 (beats all)
- GPQA-D: 95.5 (beats all)
- Humanity's Last Exam: 50.0 (beats Opus 4.8: 49.8)
- SciCode: 58.7 (Fugu non-ultra: 60.1)

**Price:** Per-query API pricing (not disclosed publicly)
**Agent pool:** Publicly accessible models only (NOT Fable 5 or Mythos)

**Key weaknesses:**
- Closed API — no self-hosting
- No skills
- No tool verification
- No self-consistency
- No MCTS
- No OPRO
- EU-blocked (not GDPR compliant)
- Fixed model pool curated by Sakana
- Requires retraining to improve

**What we take from it:** The TRINITY (Thinker/Worker/Verifier roles) and Conductor (RL-learned workflow design) patterns. But we implement them via Hermes skill, not trained weights.

---

## 3. MAESTRO (Open-Source Fugu)

**What it is:** MIT-licensed open-source clone of Fugu, built from the same TRINITY and Conductor papers. Created by AY Automate. v0.1 (early).

**How it works:**
1. Classify: heuristic tags task type + difficulty
2. Route: filter models by capability/policy/region, pick starting tier, build escalation ladder
3. Execute: call chosen model via gateway
4. Verify: verifier judges answer (ACCEPT or REVISE)
5. Escalate: if REVISE and budget left, try next model up
6. Report: full route + per-model cost + savings vs frontier-only

**Key features:**
- Works with Ollama (LOCAL_OPENAI_BASE_URL)
- OpenAI AND Anthropic compatible (works in Claude Code)
- Per-request cost transparency
- Cheap-first, verify, escalate
- Model pool is 100% yours (JSON registry)
- No GPU needed (it's just the routing brain)
- Region control (EU-compatible)

**Benchmark (their own, offline mock):**
- Maestro: 92% pass, $0.00053 mean cost
- Best-single: 100% pass, $0.01507 mean cost
- Cheapest-single: 56% pass, $0.00016 mean cost
- Random: 88% pass, $0.00689 mean cost
- Result: 92% of best quality at 97% lower cost (26x more answers per dollar)

**Key weaknesses:**
- v0.1 — early, ~5 hour build
- No skills
- No tool verification (on roadmap)
- No self-consistency
- No MCTS
- No OPRO
- No Adaptive Router (learning)
- Heuristic classifier (not learned)
- No multi-model panel (single model per turn, escalate if fails)

**What we take from it:** The cheap-first-verify-escalate pattern. The cost transparency report (show users what they saved). The model registry approach (JSON config, swap models freely). The OpenAI+Anthropic dual compatibility.

**What they DON'T do that we DO:**
- No multi-model panel (they use 1 model, verify, escalate; we use N models in parallel, structured analysis, synthesize)
- No skills
- No tool verification
- No self-consistency
- No MCTS
- No Adaptive Router (learning over time)
- No OPRO
- No Hermes integration (they're a standalone proxy; we have full agent platform)

---

## 4. OPENROUTER FUSION ROUTER

**What it is:** Multi-model deliberation as a model slug. Panel of up to 8 models answer in parallel, judge model produces structured analysis (consensus, contradictions, partial coverage, unique insights, blind spots), outer model writes final answer.

**Key features:**
- Panel: 1-8 models, each with web_search + web_fetch
- Judge: compares responses, returns structured JSON
- Analysis includes: consensus, contradictions, partial_coverage, unique_insights, blind_spots
- Recursion protection (can't nest fusion)
- Cost: 4-5x single completion for 3-model panel
- Configurable: choose your own panel + judge

**Price:** Per-query (you pay for each panel model + judge)
**Models:** Any model on OpenRouter

**Key weaknesses:**
- Per-query cost (4-5x for 3 models)
- No skills
- No tool verification (only web search, not code execution)
- No self-consistency (runs once)
- No self-improvement
- No MCTS
- No OPRO

**What we take from it:** The structured analysis pattern (consensus/contradictions/insights/blind_spots). This is the best panel-judge design we've seen. We implement it with our own models via LiteLLM + Ollama Cloud, avoiding per-query costs.

---

## 5. OPENROUTER AUTO ROUTER (NotDiamond)

**What it is:** Powered by NotDiamond. Analyzes prompt, selects optimal model from curated pool. Session stickiness for consistency. Cost/quality tradeoff slider (0-10).

**Key features:**
- Prompt analysis by NotDiamond's routing system
- Model selection based on task requirements
- Session stickiness (same model for same conversation)
- Cost/quality slider (0=pure quality, 10=maximize cost savings)
- Configurable allowed models
- No extra fee (you pay for selected model)

**Key weaknesses:**
- Only routes to 1 model (no panel, no fusion)
- No skills, no verification, no self-improvement
- NotDiamond is a closed system
- Per-query pricing

**What we take from it:** The cost/quality tradeoff slider concept. Our Adaptive Router (LiteLLM) does this automatically with weights (quality=0.9, cost=0.1).

---

## 6. OPENROUTER PARETO ROUTER

**What it is:** Coding-specific router. Routes to cheapest model that meets a minimum coding score threshold. Uses Artificial Analysis coding percentiles.

**Key features:**
- min_coding_score parameter (0-1)
- Three tiers: high (top of AA coding field), medium, low
- Within tier: picks cheapest available model
- Session stickiness
- Nitro variant: picks fastest instead of cheapest

**What we take from it:** The percentile-based routing concept. We use AA benchmark data to set quality_tier per model in our Adaptive Router config.

---

## 7. LITELLM (Infrastructure)

**What it is:** Open-source library + proxy. Unified API to 100+ LLM providers. Routing, fallbacks, cost tracking, admin UI.

**Key features for Temuclaude:**
- Adaptive Router: LEARNS which model is best per request type (bandit algorithm)
- Auto Router: embedding-based semantic routing
- Fallbacks + retry + cooldowns
- Unified completion() API
- Cost tracking per model, per request
- Proxy server with virtual keys, admin UI, caching, guardrails
- Works with Ollama

**This is an infrastructure option.** Runtime choices must follow measured results.

---

## 8. CLAUDE OPUS 4.8 (Fable 5's predecessor)

**What it is:** Anthropic's previous flagship. The "safe" fallback when Fable 5's safeguards trigger.

**Relevance:** When Fable 5 was suspended (Jun 12 - Jul 1), Opus 4.8 was the drop-in replacement. This shows the vulnerability of single-model dependency — Fable 5 went down for 3 weeks. Our multi-model approach has no single point of failure.

---

## COMPETITIVE MATRIX

| Feature | Temuclaude | Fugu | Maestro | Fusion | Model Council | Auto Router |
|---------|-----------|------|---------|--------|---------------|-------------|
| Multi-model panel | ✅ 5 models | ✅ pool | ❌ 1+escalate | ✅ up to 8 | ✅ 3 | ❌ 1 |
| Structured analysis | ✅ | ❌ | ❌ | ✅ best | ✅ | ❌ |
| Skills | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Tool verification | ✅ | partial | roadmap | web only | ❌ | ❌ |
| Self-consistency | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| MCTS+PRM | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| OPRO | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Self-improvement | ✅ Adaptive | retrain | ❌ | ❌ | ❌ | ❌ |
| Cheap-first+escalate | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Cost transparency | ✅ | ❌ | ✅ best | ❌ | ❌ | ❌ |
| Open source | ✅ | ❌ | ✅ MIT | ❌ | ❌ | ❌ |
| Flat cost | ✅ $20-100/mo | per-query | free | per-query | $200/mo | per-query |
| Ollama Cloud | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Hermes integration | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| No vendor lock-in | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |

## WHERE WE WIN

Against Fugu: We have skills + tool verification + self-consistency + MCTS + OPRO + Adaptive Router + flat cost + open source. Fugu has a trained coordinator (we use Hermes as coordinator).

Against Maestro: We have multi-model panel (they use 1+escalate), skills, tool verification, self-consistency, MCTS, OPRO, Adaptive Router, Hermes integration. Maestro is v0.1 with a 5-hour build. We're building on their cheap-first pattern but going much further.

Against Fusion: We have skills, tool verification, self-consistency, MCTS, OPRO, Adaptive Router, flat cost (they're per-query). We take their structured analysis pattern (it's the best).

Against Model Council: We have 5 open models (they use 3 closed), skills, tool verification, self-consistency, MCTS, OPRO, Adaptive Router, flat cost (they're $200/mo). We take their convergence/divergence framing.

Against Auto Router: We have multi-model panel, structured analysis, skills, verification, self-consistency, MCTS, OPRO, Adaptive Router. They only route to 1 model.

## THE TEMUCLAUDE ADVANTAGE STACK

No single competitor has ALL of these. Temuclaude is the only system that combines:

1. Multi-model panel (like Fusion/Model Council) — 5 models in parallel
2. Structured analysis (like Fusion) — consensus/contradictions/insights/blind_spots
3. Cheap-first + verify + escalate (like Fugu/Maestro) — don't overspend on easy tasks
4. Skills (unique to us) — domain expertise injection per task type
5. Tool verification (unique to us) — code execution = ground truth
6. Self-consistency (unique to us) — majority voting, +10-20% on math
7. MCTS + PRM (unique to us) — tree search for hard reasoning
8. OPRO (unique to us) — LLM optimizes its own prompts
9. Adaptive Router (via LiteLLM) — learns which model is best per task type
10. Hermes integration (unique to us) — full agent platform, not just a proxy
11. Flat cost (unique to us) — $20-100/mo Ollama Cloud vs per-query everywhere else
12. Open source (like Maestro) — no vendor lock-in
13. Cost transparency (like Maestro) — show users what they saved

**Temuclaude = Fusion + Fugu + Maestro + skills + MCTS + self-consistency + OPRO + Hermes + flat cost**

Nobody else has this combination. This is our moat.
