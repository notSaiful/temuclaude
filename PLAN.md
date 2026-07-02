# Timuclaude — Frontier Intelligence at Wholesale Prices

## Architecture & Implementation Plan

**Created:** 2026-07-02
**Author:** Ggs (Mohammad Saiful Haque)
**Mission:** Orchestrate cheap open-source models via Ollama Cloud to match frontier model performance at a fraction of the cost.

---

## 1. The Problem

Frontier model subscriptions cost $200-500/month. Small businesses can't afford that. They settle for mediocre models and fall behind competitors with deep pockets.

## 2. The Solution

Timuclaude orchestrates multiple cheap open-source models — each with different strengths — using proven research methods to achieve frontier-level performance at ~5-15% of the cost.

The name: **Timu** (cheap wholesale) + **Claude** (frontier intelligence). Cheap Claude.

## 3. Research Foundation

Five proven orchestration methods, backed by peer-reviewed papers:

### 3.1 Mixture-of-Agents (MoA)
**Paper:** arXiv:2406.04692 — "Mixture-of-Agents Enhances Large Language Model Capabilities"

Multiple models generate independently in Layer 1. Their outputs are aggregated and fed to Layer 2 models for refinement. Stack 2-3 layers.

**Results:** 6 open-source models in 3-layer MoA surpassed GPT-4o on AlpacaEval 2.0 (65.1% vs 57%) and matched it on MT-Bench (9.08 vs 9.0).

**Key insight:** Model diversity matters more than individual quality. Different architectures catch each other's blind spots.

### 3.2 Cascading / Routing
**Paper:** arXiv:2305.05176 — "FrugalGPT: How to Use Large Language Models While Reducing Cost"

A cheap model tries first. If confidence is low, escalate to a stronger model. Only hard questions reach the expensive tier.

**Results:** Up to 98% cost reduction while maintaining performance within 2% of the best model.

**Key insight:** 80% of queries are easy. Handle them cheap. Save the firepower for the 20% that need it.

### 3.3 Multi-Agent Debate
**Paper:** arXiv:2305.14325 — "Improving Factuality and Reasoning through Multiagent Debate"

Models critique each other's outputs across 2-3 rounds. Each model sees the others' answers and revises. Final answer via vote or judge.

**Results:** LLaMA-3 70B with debate matched GPT-4 on math reasoning. 5-15% improvement over single-model baselines.

**Key insight:** Debate forces self-correction that single-model self-reflection cannot achieve. Models catch each other's errors.

### 3.4 Sakana Fugu
**Blog:** Sakana AI — "Can a Swarm of Cheap LLMs Beat a Frontier Model?"

Fugu = MoA applied specifically to small/cheap models. Proved that a swarm of small models can match GPT-4o at 10-20x lower cost.

**Key insight:** Diversity > individual strength. Use different model families for maximum complementary benefit.

### 3.5 RouteLLM
**Paper:** arXiv:2403.16859 — "Learning to Route LLMs with Preference Data"

Open-source router that decides between strong/expensive and weak/cheap models. Reports ~2x cost reduction with minimal quality loss.

**Key insight:** Routing is the cheapest method for high-volume workloads. Use MoA/debate only for queries that actually need it.

---

## 4. Model Roster

Based on benchmark research, here's what each model is best at:

| Model | Strengths | Context | Role in Timuclaude |
|-------|-----------|---------|---------------------|
| **GLM-5.2** | Tool use, coding, fast classification, Chinese | 128K+ | Router + Aggregator (fast, versatile) |
| **DeepSeek R1** | Deep reasoning, math, competitive coding | 128K | Reasoning specialist (hard problems) |
| **Kimi K2.6** | Ultra-long context (2M), repo-level analysis | 2M | Long-context specialist |
| **MiniMax M3** | Long context (1M), coding, structured tasks | 1M | Generator + verifier |
| **Nemotron 3 Ultra** | Enterprise safety, instruction following | 128K | Critic + safety checker |

**All hosted via Ollama Cloud** — no local hardware needed.

---

## 5. Architecture

```
                        ┌─────────────┐
     User Query ──────► │   ROUTER     │ GLM-5.2 classifies query type + difficulty
                        └──────┬──────┘
                               │
                    ┌──────────┼──────────┐
                    │          │          │
                    ▼          ▼          ▼
             ┌─────────┐ ┌─────────┐ ┌─────────┐
             │  SIMPLE │ │ MEDIUM  │ │   HARD  │
             │  (60%)  │ │ (30%)   │ │  (10%)  │
             └────┬────┘ └────┬────┘ └────┬────┘
                  │           │           │
                  ▼           ▼           ▼
            ┌─────────┐ ┌─────────┐ ┌─────────────┐
            │DIRECT   │ │  MoA     │ │  MoA +     │
            │SINGLE   │ │  2-LAYER│ │  DEBATE    │
            │MODEL    │ │         │ │  3 ROUNDS  │
            └────┬────┘ └────┬────┘ └──────┬──────┘
                 │           │              │
                 │           │              │
                 │     ┌─────┘              │
                 │     ▼                    │
                 │  ┌────────┐              │
                 │  │L1: GLM │              │
                 │  │+ Kimi  │              │
                 │  │+ Minimax│             │
                 │  └───┬────┘              │
                 │      │                   │
                 │      ▼                   │
                 │  ┌────────┐              │
                 │  │L2: DeepS│             │
                 │  │+ Nemot │              │
                 │  └───┬────┘              │
                 │      │                   │
                 │      │     ┌─────────────┘
                 │      │     │
                 │      ▼     ▼
                 │  ┌─────────────┐
                 │  │  AGGREGATOR │ GLM-5.2 synthesizes
                 │  │  + CRITIC   │ Nemotron checks safety
                 │  └──────┬──────┘
                 │         │
                 └─────────┘
                        │
                        ▼
                   ┌─────────┐
                   │  OUTPUT  │
                   └─────────┘
```

### 5.1 Layer 0 — Router (GLM-5.2)

Every query enters here. GLM-5.2 classifies:
- **Type:** coding, reasoning, creative, factual, long-context, conversation
- **Difficulty:** simple, medium, hard (based on query complexity signals)
- **Route decision:** which path to take

This is a single fast call. Costs ~nothing.

### 5.2 Path A — Simple (60% of queries)

Route directly to the best single model for the task type:
- Factual/short → GLM-5.2
- Coding → DeepSeek V3 (fast mode)
- Chinese → GLM-5.2

One call. Done. Maximum efficiency.

### 5.3 Path B — Medium (30% of queries)

**Mixture-of-Agents, 2 layers:**

**Layer 1 (parallel):**
- GLM-5.2 generates
- Kimi K2.6 generates (different architecture = diversity)
- MiniMax M3 generates

All three run in parallel (async). Responses are aggregated.

**Layer 2 (refinement):**
- DeepSeek R1 sees all three responses, produces refined answer
- Nemotron 3 Ultra reviews for safety and instruction compliance

**Aggregation:** GLM-5.2 takes the best elements and produces final output.

### 5.4 Path C — Hard (10% of queries)

**MoA + Multi-Agent Debate:**

**Round 1:**
- All 5 models independently generate answers (parallel)
- All 5 models see each other's answers and critique (parallel)

**Round 2:**
- All 5 models revise based on critiques (parallel)
- GLM-5.2 + DeepSeek R1 debate the two best candidates

**Round 3:**
- Final synthesis: GLM-5.2 picks the best answer
- Nemotron 3 Ultra does final safety check

### 5.5 Confidence Escalation

At any point, if the aggregator's confidence is low (detected via:
- Models disagree significantly
- Low token probability on key claims
- Explicit uncertainty markers), the query escalates:

Simple → Medium → Hard → (if still stuck) return best available + flag for review

---

## 6. Implementation Plan

### Phase 1: Foundation (Week 1-2)

**Goal:** Router + single-model routing working end-to-end.

1. Set up Ollama Cloud connections for all 5 models
2. Build the router classifier (GLM-5.2 with structured output)
3. Implement task-type routing logic
4. Create a simple API: `POST /query { prompt } → { answer, model_used, cost }`
5. Benchmark against frontier models on 100 test queries
6. Log all results for analysis

**Deliverable:** Working router that sends queries to the right model.

### Phase 2: Mixture-of-Agents (Week 3-4)

**Goal:** MoA 2-layer pipeline for medium-difficulty queries.

1. Implement parallel model calls (async HTTP to Ollama Cloud)
2. Build aggregation prompt ("Here are N responses. Produce the best answer.")
3. Add Layer 2 refinement (DeepSeek R1 as refiner)
4. Add confidence scoring (how much do Layer 1 responses agree?)
5. Benchmark MoA path against Phase 1 routing
6. Optimize: which model combinations give best MoA results?

**Deliverable:** MoA pipeline that beats single-model routing on quality.

### Phase 3: Debate (Week 5-6)

**Goal:** Multi-agent debate for hard queries.

1. Implement Round 1: parallel generation + parallel critique
2. Implement Round 2: revision based on critiques
3. Implement Round 3: final synthesis + safety check
4. Add debate trigger logic (when to escalate from MoA to debate)
5. Benchmark debate vs MoA on hard reasoning tasks (math, complex coding)
6. Tune: how many rounds? How many participants? When to stop?

**Deliverable:** Full 3-path system (simple/MoA/debate) with auto-escalation.

### Phase 4: Production (Week 7-8)

**Goal:** Deployable product.

1. Build OpenAI-compatible API wrapper (drop-in replacement for GPT-4)
2. Add cost tracking and usage analytics
3. Build a dashboard (reuse the portfolio site aesthetic)
4. Add user management + API keys
5. Write documentation
6. Load test: latency, cost, quality at scale
7. Deploy (Fly.io or Vercel — you already use both)

**Deliverable:** Timuclaude as a service. Users point their app at it instead of OpenAI.

---

## 7. Tech Stack

| Component | Technology |
|-----------|-----------|
| Orchestrator | Python + asyncio (parallel model calls) |
| API Server | FastAPI (OpenAI-compatible endpoints) |
| Model Backend | Ollama Cloud (https://ollama.com) |
| Proxy/Router | LiteLLM (Ollama-compatible, built-in routing) |
| Deployment | Fly.io (backend) + Vercel (dashboard) |
| Monitoring | Built-in cost/quality tracking |
| Frontend | The portfolio site aesthetic, extended with dashboard |

---

## 8. Cost Model

### Per-query cost estimate (Ollama Cloud pricing):

| Path | Model Calls | Estimated Cost | Latency |
|------|------------|----------------|---------|
| Simple (60%) | 1 | ~$0.001-0.005 | 1-3s |
| Medium MoA (30%) | 5 | ~$0.005-0.025 | 5-15s |
| Hard Debate (10%) | 12-15 | ~$0.015-0.075 | 20-60s |

**Weighted average:** ~$0.005-0.015 per query
**Frontier model comparison:** ~$0.05-0.15 per query (GPT-4o)

**Cost reduction: ~90-95%** vs frontier models.

Monthly cost for 10,000 queries: ~$50-150 (vs $500-1,500 for GPT-4o).

---

## 9. Quality Targets

| Benchmark | Target | Method |
|-----------|--------|--------|
| MT-Bench | ≥ 9.0 (match GPT-4o) | MoA 2-layer |
| AlpacaEval 2.0 | ≥ 60% win rate | MoA 2-layer |
| HumanEval (coding) | ≥ 90% | Route to DeepSeek |
| GSM8K (math) | ≥ 92% | Debate path |
| MMLU | ≥ 88% | MoA 2-layer |
| Latency (simple) | < 3s | Direct routing |
| Latency (medium) | < 15s | Parallel MoA |
| Latency (hard) | < 60s | Debate (acceptable) |

---

## 10. Competitive Advantage

1. **Price:** 10-20x cheaper than frontier APIs
2. **Privacy:** Ollama Cloud models don't train on your data
3. **Flexibility:** Swap models anytime — no vendor lock-in
4. **Transparency:** Open-source models, open orchestration logic
5. **Self-improving:** Log disagreements, tune routing, add models over time
6. **Branding:** "Timuclaude" — the name sells itself

---

## 11. Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Latency on hard queries (60s) | Cache common patterns; parallel execution; timeout fallback |
| Model disagreement produces worse output | Confidence scoring; fallback to single best model |
| Ollama Cloud rate limits | Queue management; retry with backoff |
| Model availability changes | Abstract behind LiteLLM; swap models via config |
| Quality gap vs frontier on edge cases | Continuous benchmarking; add new models as released |

---

## 12. Key Papers

1. **MoA:** arXiv:2406.04692 — "Mixture-of-Agents Enhances LLM Capabilities"
2. **FrugalGPT:** arXiv:2305.05176 — cost reduction via cascading
3. **Multi-Agent Debate:** arXiv:2305.14325 — reasoning improvement
4. **RouteLLM:** arXiv:2403.16859 — routing with preference data
5. **AutoGen:** arXiv:2308.08143 — multi-agent conversation framework
6. **MetaGPT:** arXiv:2308.00352 — structured multi-agent collaboration
7. **Sakana Fugu:** Sakana AI blog — cheap model swarms matching frontier

---

## 13. Phase 1 Immediate Action Items

1. Verify all 5 models are available on Ollama Cloud (`ollama list`)
2. Set up the Python project structure
3. Build the router classifier
4. Create 100-query benchmark suite (mix of coding, reasoning, creative, factual)
5. Implement single-model routing
6. Measure baseline quality + cost

**Start date:** Now.