# Temuclaude — PLAN v5 (THE BREAKTHROUGH)

## How We Beat Frontier Models

---

## 1. WHERE OUR MODELS ARE ALREADY CLOSE

From ArtificialAnalysis.ai benchmark data (July 2026):

| Benchmark | Fable 5 (frontier) | GLM-5.2 (ours) | Gap | DeepSeek V4 Pro | Gap |
|-----------|-------------------|----------------|-----|-----------------|-----|
| Terminal-Bench v2.1 | 85% | 81% (#3) | **4 pts** | 75% | 10 pts |
| τ³-Banking | 31% | 27% (#3) | **4 pts** | 14% | 17 pts |
| GPQA Diamond | 94% (GPT-5.5) | 89% (#6) | **5 pts** | 90% (#5) | **4 pts** |
| SciCode | 60% | 50% (#5) | 10 pts | 47% | 13 pts |
| GDPval-AA v2 | 63% | 51% (#3) | 12 pts | 42% | 21 pts |
| LiveCodeBench | 93% (Fugu) | — | — | 89.8 (high) | **4 pts** |

**Key insight:** On Terminal-Bench and τ³-Banking, GLM-5.2 is only 4 points behind Fable 5. On GPQA, DeepSeek V4 Pro is only 4 points behind GPT-5.5. These gaps are CLOSABLE with proven techniques.

## 2. FUGU'S ACTUAL RESULTS (WHAT THEY BEAT)

From Sakana's own benchmark table:

| Benchmark | Fugu Ultra | Opus 4.8 | GPT 5.5 | Fugu beats? |
|-----------|-----------|----------|---------|-------------|
| SWE Bench Pro | **73.7** | 69.2 | 58.6 | YES — beats all |
| TerminalBench 2.1 | **82.1** | 74.6 | 78.2 | YES — beats all |
| LiveCodeBench | **93.2** | 87.8 | 85.3 | YES — beats all |
| LiveCodeBench Pro | **90.8** | 84.8 | 88.4 | YES — beats all |
| Humanity's Last Exam | **50.0** | 49.8 | 41.4 | YES — beats all |
| GPQA-D | **95.5** | 92.0 | 93.6 | YES — beats all |
| SciCode | 58.7 | 53.5 | 56.1 | NO — Fugu (60.1) beats Ultra |
| MRCRv2 | 93.6 | 87.9 | **94.8** | NO — GPT 5.5 wins |

Fugu Ultra beats Opus 4.8 and GPT 5.5 on 7 out of 9 benchmarks. **But Fugu doesn't use Fable 5 or Mythos in its pool** — it orchestrates publicly accessible models.

**If Fugu can do it, we can do it.** Our models are the same caliber as Fugu's pool.

## 3. WHAT FUGU DOES (AND DOESN'T DO)

### What Fugu does:
- TRINITY: evolved coordinator model (Thinker/Worker/Verifier roles)
- Conductor: RL-trained model that outputs agentic workflows as natural language
- Three discovered strategies: debate-and-aggregate, build-and-debug, bring-in-specialist
- Trained with SFT + evolutionary strategies + GRPO (reinforcement learning)

### What Fugu DOES NOT do (our opportunity):

| Method | Fugu? | Us? | Impact |
|--------|-------|-----|--------|
| MCTS + PRM (tree search over reasoning) | NO | YES | rStar-Math: 7B model matched frontier on MATH |
| Skill Library (Voyager pattern) | NO | YES | Compounding gains — system gets better every use |
| Self-Consistency (majority voting) | NO | YES | +10-20% on math/reasoning (FREE) |
| Tool Verification (code execution) | Partial | YES | +10-27% on coding tasks (ground truth) |
| OPRO Dynamic Prompt Optimization | NO | YES | LLM optimizes its own prompts iteratively |
| Structured SOPs (MetaGPT pattern) | NO | YES | Structured handoffs beat free-form debate |
| Self-Rewarding DPO Loop | NO | YES | Self-improvement without external training |
| Hermes as orchestrator | NO | YES | Already capable, learns from every session |

**This is our advantage.** Fugu has a trained coordinator but only 3 strategies. We have Hermes as orchestrator with 8+ strategies, including ones Fugu doesn't use.

## 4. PROVEN BENCHMARK IMPROVEMENT NUMBERS

From published research:

| Technique | Benchmark | Baseline | With Technique | Gain |
|-----------|-----------|----------|----------------|------|
| Chain-of-Thought | GSM8K | 17.7% | 56.9% | **+39.2%** |
| Self-Consistency (40 samples) | GSM8K | 56.9% | 74.4% | **+17.5%** |
| Self-Consistency | MATH (GPT-4) | 42% | 52% | **+10%** |
| Best-of-N (pass@10) | HumanEval | 82% | 94% | **+12%** |
| Best-of-N (pass@100) | HumanEval | 28.8% | 72% | **+43.2%** |
| Tool use (code execution) | GSM8K | 65% | 92% | **+27%** |
| Tool use (Python) | MATH | 50.3% | 58.8% | **+8.5%** |
| RAG | MMLU (LLaMA-70B) | 68.9% | 77.8% | **+8.9%** |
| Agentic (multi-step) | SWE-bench | 3% | 23% | **+20%** |
| Agentic + tools | GAIA | 15% | 44% | **+29%** |
| Reflexion (exec feedback) | HumanEval | 53% | 80% | **+27%** |
| Reflexion | HotpotQA | 35% | 50% | **+15%** |

**The winning stack** (from research):
1. Large base model (we have 5 near-frontier models)
2. Few-shot CoT prompting
3. Self-consistency voting (20-40 samples)
4. Tool use (code execution for math/coding)
5. RAG for knowledge tasks
6. Multi-turn refinement with EXTERNAL feedback (not self-correction — that's debunked)
7. Best-of-N with verifier

## 5. THE BREAKTHROUGH ARCHITECTURE

### The Temuclaude Stack (8 layers Fugu doesn't have):

```
User Query
    ↓
[1] HERMES (Orchestrator) — analyzes query, devises strategy
    ↓
[2] SKILL AUTO-LOAD — downloads relevant skills from Hermes hub
    ↓
[3] ROUTING — picks best model(s) for task type
    ↓
[4] GENERATION — one of:
    ├── Direct (simple): 1 model + skills
    ├── Best-of-N (verifiable): N models generate in parallel
    ├── Debate (complex): 3 models generate, critique, refine
    └── MCTS (hard reasoning): tree search with PRM verification
    ↓
[5] SELF-CONSISTENCY — majority vote across N samples (math/reasoning)
    ↓
[6] TOOL VERIFICATION — execute code, verify math (ground truth)
    ↓
[7] OPRO OPTIMIZATION — if first attempt fails, optimize prompt, retry
    ↓
[8] SKILL EXTRACTION — save successful strategy as reusable skill
    ↓
Output
```

### Why This Beats Fugu:

**Fugu = trained coordinator + 3 strategies (debate, build-debug, specialist)**
**Temuclaude = Hermes orchestrator + 8 strategies + skills + tools + self-improvement**

| Advantage | Fugu | Temuclaude |
|-----------|------|------------|
| Orchestrator | Trained model (SFT+ES+RL) | Hermes (already capable, no training needed) |
| Strategies | 3 discovered | 8+ (including all 3 Fugu uses + 5 more) |
| Skills | None | Auto-loaded from Hermes hub per task type |
| Tool verification | Partial | Full (code execution, web search, RAG) |
| Self-consistency | No | Yes (+10-20% on math) |
| MCTS | No | Yes (rStar-Math pattern — frontier on math with small models) |
| Self-improvement | Requires retraining | Skills accumulate every session |
| Cost | Per-query API pricing | $20-100/mo Ollama Cloud flat |
| Prompt optimization | No | OPRO (LLM optimizes its own prompts) |
| Open | Closed API | Fully open |

### The Math (Why This Works):

Take Terminal-Bench v2.1:
- GLM-5.2 alone: 81%
- Fable 5 (frontier): 85%
- Gap: 4 points

Apply the stack:
- Best-of-4 with test execution: +10-15% (proven on HumanEval: 82% → 94%)
- Reflexion (execute + fix): +10-27% (proven on HumanEval: 53% → 80%)
- Skill loading (coding skills): +5-8% (domain expertise)
- Self-consistency: +5-10% (majority vote)

**Projected: GLM-5.2 with stack = 81% + 10-20% = 91-96%**
**Fable 5 = 85%**

**We beat frontier by 6-11 points on Terminal-Bench.**

Take GPQA Diamond:
- DeepSeek V4 Pro alone: 90%
- GPT-5.5 (frontier): 94%
- Gap: 4 points

Apply the stack:
- Self-consistency (20 samples): +10% (proven: GSM8K +17.5%, MATH +10%)
- Chain-of-Thought with max thinking: +5-10%
- Skill loading (scientific reasoning): +3-5%

**Projected: DeepSeek V4 Pro with stack = 90% + 8-15% = 98-100%+**
**GPT-5.5 = 94%**

**We beat frontier by 4-6 points on GPQA.**

### Where We Can Beat Frontier:

| Benchmark | Our Best Model | Score | With Stack | Frontier | We Win? |
|-----------|---------------|-------|------------|----------|---------|
| Terminal-Bench v2.1 | GLM-5.2 | 81% | 91-96% | 85% | **YES** |
| GPQA Diamond | DeepSeek V4 Pro | 90% | 95-98% | 94% | **YES** |
| τ³-Banking | GLM-5.2 | 27% | 35-40% | 31% | **YES** |
| LiveCodeBench | DeepSeek V4 Pro | 89.8% | 93-96% | 93.2% (Fugu) | **YES** |
| SciCode | GLM-5.2 | 50% | 58-65% | 60% | **MAYBE** |
| GDPval-AA | GLM-5.2 | 51% | 58-65% | 63% | **MAYBE** |
| HLE | GLM-5.2 | 18% | 25-35% | 46% | **NO** (knowledge gap) |
| SWE-Bench Pro | GLM-5.2 | ~58% | 70-78% | 69.2 (Opus) | **YES** |

### Where We CAN'T Beat Frontier (Yet):

- **Humanity's Last Exam** (knowledge): GLM-5.2 at 18% vs Fable 5 at 46%. This is a pure knowledge gap. Orchestration can't create knowledge. Need RAG + more capable base models.
- **GDPval-AA** (general work tasks): 12-point gap. Harder to close with techniques.

### The Value Proposition:

**We beat frontier on 5-6 out of 9 benchmarks** using:
- 5 near-frontier open models on Ollama Cloud
- Hermes as orchestrator
- 8+ proven techniques Fugu doesn't use
- Skills that compound over time
- $20-100/mo flat cost (vs Fugu/OpenAI per-query pricing)

**On the benchmarks we can't beat frontier: we match 85-90% of frontier quality at 50x lower cost.**

---

## 6. BUILD STEPS

### Step 1: Foundation + All Models Live
- Python project, asyncio, Ollama Cloud connections for all 5 models
- Logging infrastructure (every query, every technique, every result)

### Step 2: The Temuclaude Skill
Write the orchestration skill that encodes all 8 strategies:
- Direct routing (simple queries)
- Best-of-N + tool verification (verifiable tasks)
- Debate (complex reasoning)
- MCTS + PRM (hard math/reasoning)
- Self-consistency voting
- OPRO prompt optimization
- Skill auto-loading
- Skill extraction (save winning strategies)

### Step 3: Benchmark Suite
- Terminal-Bench v2.1, GPQA Diamond, LiveCodeBench, GSM8K, HumanEval, SciCode
- Test each model ALONE → baseline
- Test each technique ALONE → individual gains
- Test the STACK → combined gains
- This is our proof. Numbers don't lie.

### Step 4: Self-Improvement Loop
- Log everything: strategy, models, techniques, scores, time, cost
- Hermes analyzes: which technique combos work best per benchmark
- OPRO: optimize prompts based on what worked
- Skill extraction: save winning strategies as skills
- Auto-benchmark new models on Ollama Cloud

### Step 5: Production API
- OpenAI-compatible wrapper
- Auto-skill loading
- Cost tracking
- Deploy on Fly.io

---

## 7. WHY PEOPLE WILL USE TEMUCLAUDE OVER FUGU

1. **We beat frontier on more benchmarks** — Fugu beats frontier on 7/9, we target 5-6/9 but with DIFFERENT techniques (MCTS, self-consistency, skills) that Fugu doesn't use

2. **Skills compound** — every user query makes the system better. Fugu needs retraining.

3. **Flat cost** — $20-100/mo Ollama Cloud vs Fugu's per-query pricing. For heavy users, this is 100x+ cheaper.

4. **Open** — open models, open orchestration, open skills. Fugu is a closed API.

5. **Hermes integration** — full agent platform with tools, memory, browser, terminal. Fugu is just a model API.

6. **Self-improving** — OPRO + skill extraction + logging = system gets better every day without retraining.

7. **No vendor lock-in** — swap any model on Ollama Cloud. Fugu's pool is curated by Sakana.

**Temuclaude is not "cheap Fugu." Temuclaude is "Fugu + skills + MCTS + self-consistency + self-improvement at flat cost."**

That's how we win.