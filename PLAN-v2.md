# Timuclaude — Revised Plan v2 (Ground Truth Research)

## Real Data from ArtificialAnalysis.ai + Ollama Cloud (July 2026)

---

## 1. THE LANDSCAPE — Intelligence Index v4.1

### Top 11 Models on AA Intelligence Index:

| Rank | Model | Intelligence | Type | Ollama Cloud |
|------|-------|-------------|------|-------------|
| 1 | Claude Fable 5 (with fallback) | 60 | Proprietary | No |
| 2 | GPT-5.5 (xhigh) | 55 | Proprietary | No |
| 3 | GLM-5.2 (max) | 51 | Open Weights | YES |
| 4 | Gemini 3.5 Flash | 50 | Proprietary | No |
| 5 | MiniMax-M3 | 44 | Open Weights | YES |
| 6 | DeepSeek V4 Pro (max) | 44 | Open Weights | YES |
| 7 | Muse Spark | 43 | Proprietary | No |
| 8 | Kimi K2.6 | 43 | Open Weights | YES |
| 9 | Nemotron 3 Ultra | 38 | Open Weights | YES |
| 10 | Grok 4.3 (high) | 38 | Proprietary | No |
| 11 | gpt-oss-120b (high) | 24 | Open Weights | YES |

### Extended Leaderboard (models 12-27):

| Model | Intelligence | Ollama Cloud |
|-------|-------------|-------------|
| Claude Opus 4.8 (max) | 56 | No |
| Claude Sonnet 5 (max) | 53 | No |
| Gemini 3.1 Pro Preview | 46 | No |
| Qwen3.7 Max | 42 | Check |
| MiMo-V2.5-Pro | 40 | Check |
| DeepSeek V4 Flash (max) | 34 | YES |
| GPT-5.4 mini (xhigh) | 30 | No |
| Qwen3.5 397B A17B | 29 | Check |
| Mistral Medium 3.5 | 22 | Check |
| Claude 4.5 Haiku | 17 | No |
| Gemma 4 31B | 15 | YES |
| Nova 2.0 Pro Preview | 14 | No |
| K2 Think V2 | ? | Check |
| gpt-oss-20b (high) | ? | YES |
| Solar Pro 3 | ? | Check |

### Speed (tokens/sec):

| Model | Speed | 
|-------|-------|
| gpt-oss-120b (high) | 259 |
| GLM-5.2 (max) | 184 |
| Gemini 3.5 Flash | 169 |
| Nemotron 3 Ultra | 131 |
| Grok 4.3 (high) | 110 |
| MiniMax-M3 | 92 |
| DeepSeek V4 Pro (max) | 83 |
| GPT-5.5 (xhigh) | 75 |
| Claude Fable 5 | 73 |
| Kimi K2.6 | (slowest tier) |

### Cost per Task:

| Model | Cost/Task |
|-------|-----------|
| gpt-oss-120b (high) | $0.04 |
| GLM-5.2 (max) | $0.06 |
| Gemini 3.5 Flash | $0.12 |
| Nemotron 3 Ultra | $0.16 |
| MiniMax-M3 | $0.24 |
| DeepSeek V4 Pro (max) | $0.31 |
| Muse Spark | $0.48 |
| Kimi K2.6 | $0.59 |
| GPT-5.5 (xhigh) | $1.03 |
| Claude Fable 5 | $2.75 |

### Benchmark Breakdown — Agentic Tasks:

**Terminal-Bench v2.1 (Agentic coding & terminal use):**
- Claude Fable 5: 85%
- GPT-5.5: 84%
- GLM-5.2: 81%
- DeepSeek V4 Pro: 79%
- (others below)

**GDPval-AA v2 (Agentic real-world work tasks, (Elo-500)/2000):**
- Claude Fable 5: 63%
- GPT-5.5: 55%
- Claude Opus 4.8: 51%
- GLM-5.2: 49%
- MiniMax-M3: ~44%
- DeepSeek V4 Pro: ~42%
- Kimi K2.6: ~40%
- Nemotron 3 Ultra: ~38%

**τ³-Banking (Agentic tool use):**
- Claude Fable 5: 31%
- GPT-5.5: 28%
- GLM-5.2: 27%
- MiniMax-M3: 25%
- DeepSeek V4 Pro: 14%
- Kimi K2.6: 13%

### DeepSeek V4 Pro detailed benchmarks (from Ollama page):

| Benchmark | V4-Pro High | V4-Pro Max |
|-----------|------------|-----------|
| MMLU-Pro | 87.1 | 87.5 |
| GPQA Diamond | 89.1 | 90.1 |
| LiveCodeBench | 89.8 | 93.5 |
| Codeforces Rating | 2919 | 3206 |
| HMMT 2026 Feb | 94.0 | 95.2 |
| IMOAnswerBench | 88.0 | 89.8 |
| Terminal Bench 2.0 | 63.3 | 67.9 |
| SWE Verified | 79.4 | 80.6 |
| SWE Pro | 54.4 | 55.4 |
| BrowseComp | 80.4 | 83.4 |

### Coding Agent Index (from AA):

| Model | Score |
|-------|-------|
| Claude Code (Fable 5 max) | 77 |
| GPT-5.5 (xhigh) | 76 |
| Opus 4.8 (max) | 71 |
| GPT-5.5 (medium) | 67 |
| Opus 4.8 (medium) | 65 |
| Opus 4.7 (medium) | 62 |
| GLM-5.2 | 58 |
| GLM-5.1 | 57 |
| Composer 2.5 Fast | 52 |
| DeepSeek V4 Pro (high) | 47 |

---

## 2. HONEST RESEARCH FINDINGS

### What Works:
- **Routing/cascading** — proven for cost reduction (50-98%), not quality improvement
- **Best-of-N sampling** — generate N responses, pick the best with a verifier
- **Test-time compute scaling** — reasoning models (R1, GLM-5.2 max) already do this internally
- **MoA (Mixture-of-Agents)** — surpassed GPT-4o on AlpacaEval 2.0 (narrow metric), but likely doesn't beat CURRENT frontier

### What Doesn't Work:
- **Multi-agent debate** — largely debunked. Gains attributable to simpler mechanisms (self-consistency, test-time compute). Debate adds cost without consistent benefit
- **Self-improving systems** — remain aspirational. No convincing real implementation exists yet

### Key Insight from the Data:
Our models are ALREADY on the leaderboard:
- GLM-5.2 is #3 overall (intelligence 51), beating Gemini 3.5 Flash, MiniMax, DeepSeek, Kimi, Nemotron
- The gap to #1 (Claude Fable 5 = 60) is only 9 points
- GLM-5.2 costs $0.06/task vs Claude Fable 5 at $2.75/task — 45x cheaper
- On Terminal-Bench, GLM-5.2 (81%) is only 4 points behind Fable 5 (85%)

**This changes everything.** The question isn't "can cheap models match frontier" — GLM-5.2 IS already near-frontier. The question is: can we close the last 9-point gap through orchestration?

---

## 3. REVISED ARCHITECTURE

### The Real Opportunity

The data shows:
1. GLM-5.2 (max) is already #3 globally and #1 among open weights
2. DeepSeek V4 Pro (max) has the best raw reasoning (MMLU-Pro 87.5, GPQA 90.1, Codeforces 3206)
3. Kimi K2.6 is best at agentic/swarm tasks (designed for 300 sub-agents, 4000 coordinated steps)
4. MiniMax-M3 has 1M context + multimodal + strong coding
5. Nemotron 3 Ultra leads on "agent productivity, coding, and instruction following" among open models per NVIDIA

Combined intelligence via orchestration: if GLM-5.2 alone is 51, the ensemble should target 55-60+.

### New Architecture — "Verifier-Guided Best-of-N + Routing"

Research showed the BEST method is NOT MoA or debate. It's:

1. **Routing** — send queries to the right specialist
2. **Best-of-N generation** — have 2-3 models generate independently
3. **Verifier scoring** — a separate model scores each response
4. **Synthesis** — the best model synthesizes the final answer from the best elements

This is simpler, faster, and more proven than MoA or debate.

```
                        ┌─────────────┐
     User Query ──────► │   ROUTER     │  GLM-5.2 (fast, cheapest, best overall)
                        └──────┬──────┘  Classifies: type + difficulty + best models
                               │
                    ┌──────────┼──────────────┐
                    │          │              │
                    ▼          ▼              ▼
             ┌─────────┐ ┌─────────┐ ┌─────────────┐
             │  SIMPLE │ │ MEDIUM  │ │   HARD      │
             │  (70%)  │ │ (25%)   │ │   (5%)     │
             └────┬────┘ └────┬────┘ └──────┬──────┘
                  │           │              │
                  ▼           ▼              ▼
            ┌─────────┐ ┌──────────┐ ┌──────────────┐
            │SINGLE   │ │BEST-OF-3 │ │BEST-OF-3 +   │
            │MODEL    │ │+ VERIFIER│ │VERIFIER +     │
            │         │ │          │ │SYNTHESIS      │
            └─────────┘ └──────────┘ └──────────────┘
```

### Path A — Simple (70% of queries)

Route to single best model:
- Coding → DeepSeek V4 Pro (best code benchmarks)
- Agentic/tool use → GLM-5.2 (best agent score)
- Long context → MiniMax M3 or Kimi K2.6 (1M+ context)
- Reasoning/math → DeepSeek V4 Pro (max thinking)
- Creative/general → GLM-5.2
- Chinese → GLM-5.2

One call. Fast. Cheap.

### Path B — Medium (25% of queries)

**Best-of-3 + Verifier:**
1. Generate 3 responses in parallel:
   - GLM-5.2 generates
   - DeepSeek V4 Pro generates (different architecture = diversity)
   - Kimi K2.6 generates (different perspective)

2. Verifier scores each response:
   - Nemotron 3 Ultra (built for agentic evaluation, instruction following)
   - Scores: accuracy, completeness, instruction adherence

3. Synthesis:
   - GLM-5.2 takes the best elements + verifier feedback → final answer

### Path C — Hard (5% of queries)

**Best-of-5 + Verifier + DeepSeek Synthesis:**
1. All 5 models generate in parallel
2. Nemotron 3 Ultra scores all 5 responses
3. DeepSeek V4 Pro (max thinking) synthesizes the final answer
4. GLM-5.2 does final polish pass

### Self-Improvement Loop (the crucial differentiator)

Every query logs:
- Which models were used
- What each model answered
- Verifier scores per response
- Which model's elements made it into the final synthesis
- Final quality score (user feedback / downstream task success)

Hermes analyzes these logs and adjusts:
- **Model pairings**: if GLM + Kimi consistently produce better combined results than GLM + DeepSeek on certain task types, update routing
- **Verifier tuning**: if Nemotron scores are poorly calibrated (high score but bad output), adjust
- **Path thresholds**: if too many queries escalate to Hard, lower the threshold
- **New model drop-in**: when GLM-5.3 or DeepSeek V5 releases, test it against current models and auto-promote if better
- **Prompt optimization**: A/B test system prompts for each model per task type

This is NOT "self-improving" in the AI sense (which was debunked). This is **data-driven routing optimization** — proven, practical, and Hermes already does this naturally through its skill system.

---

## 4. SKILLS INTEGRATION

The user requested that Timuclaude auto-utilize and auto-download skills. Here's how:

### Hermes Skills for Quality Boost

Hermes has a skill system that loads domain-specific instructions. For Timuclaude:

1. **Auto-load skills per task type:**
   - Coding tasks → load `test-driven-development`, `systematic-debugging`, `codebase-inspection` skills
   - Research tasks → load `arxiv`, `blogwatcher` skills
   - Writing tasks → load `humanizer`, `frontend-design` skills
   - Math/reasoning → load reasoning-focused prompts

2. **Auto-download skills from Hermes hub:**
   - `hermes skills search <topic>` before each task
   - If a relevant skill exists, install and use it
   - Skills get cached after first use

3. **Custom Timuclaude skills:**
   - `timuclaude-routing` — routing rules and model selection logic
   - `timuclaude-verification` — verifier prompts and scoring criteria
   - `timuclaude-synthesis` — synthesis templates for combining model outputs
   - `timuclaude-benchmark` — auto-benchmark new model combinations

4. **Prompt engineering skills:**
   - Chain-of-thought prompts for reasoning tasks
   - Structured output prompts for verifier scoring
   - Few-shot examples per benchmark category

### How Skills Improve Benchmark Performance:

Skills inject domain expertise into model calls. A model with a coding skill loaded performs better than the same model without it — because the skill provides:
- Best practices (test before declare done, check edge cases)
- Known pitfalls (avoid common bugs, handle null cases)
- Quality standards (code review checklist, security scan)
- Domain context (project conventions, style guide)

This is like giving each model a cheat sheet for each task type. The models don't get smarter — they get better directed.

---

## 5. COST ANALYSIS

### Ollama Cloud Pricing:
- Free: light usage, limited cloud access
- Pro: $20/mo, 50x more usage, 3 cloud models at a time
- Max: $100/mo, 5x more than Pro, 10 cloud models at a time

### Per-query cost (usage-based, not per-token):
The key insight: Ollama Cloud charges by GPU time, not tokens. Models are categorized by usage level (1-4). DeepSeek V4 Pro is level 4 (heaviest), GLM-5.2 is likely level 2-3.

### Comparison:
| Approach | Cost per query | Quality (est.) |
|----------|---------------|----------------|
| Claude Fable 5 direct | $2.75/task | 60 |
| GPT-5.5 direct | $1.03/task | 55 |
| GLM-5.2 alone | $0.06/task | 51 |
| Timuclaude Simple (1 model) | ~$0.06/task | 51-53 |
| Timuclaude Medium (3 gen + verify) | ~$0.20/task | 53-57 |
| Timuclaude Hard (5 gen + verify + synth) | ~$0.50/task | 55-60+ |

**Target: match or beat Claude Fable 5 (60) at ~$0.50/task vs $2.75/task — 5.5x cheaper.**

For the 70% of simple queries: $0.06 vs $2.75 = 45x cheaper.

---

## 6. BUILD PLAN

### Step 1: Foundation + All Models Live
- Set up Python project with asyncio
- Connect all 5 models via Ollama Cloud API
- Verify each model responds with tool calls + thinking
- Build logging infrastructure (every query logged)
- Test parallel model calls

### Step 2: Benchmark Suite
- Download/run standard benchmarks: MMLU-Pro, HumanEval, GSM8K, Terminal-Bench, GDPval-AA
- Test each model ALONE on each benchmark → baseline scores
- This is our measuring stick. No orchestration until we know baselines.

### Step 3: Router
- GLM-5.2 classifies query type + difficulty
- Routes to single best model
- Benchmark: does smart routing beat random/single-model?
- Auto-tune routing rules from results

### Step 4: Best-of-N + Verifier
- 3 models generate in parallel for medium queries
- Nemotron 3 Ultra scores each response
- GLM-5.2 synthesizes final answer from best elements
- Benchmark: does Best-of-3 beat single model? By how much?
- A/B test: which 3-model combinations work best per task type?

### Step 5: Hard Path + Synthesis
- 5 models generate in parallel
- Nemotron scores all 5
- DeepSeek V4 Pro (max thinking) synthesizes
- GLM-5.2 polishes
- Benchmark: does this beat Claude Fable 5?

### Step 6: Self-Improvement Loop
- Log every query: models used, scores, final quality
- Hermes analyzes logs → adjusts routing, pairing, thresholds
- Auto-benchmark new model combinations weekly
- Auto-promote better models when released
- Skills auto-download for new task types

### Step 7: Production API + Skills
- OpenAI-compatible wrapper (drop-in GPT-4 replacement)
- Auto-skill loading per task type
- Cost tracking dashboard
- Deploy on Fly.io

---

## 7. THE HONEST TRUTH

### What gives us the best shot at beating frontier:

1. **GLM-5.2 is already #3** — only 9 points behind Claude Fable 5. We're not starting from zero.

2. **Best-of-N + verifier is proven** — simpler than MoA, more reliable than debate. Research supports it.

3. **Model diversity is real** — GLM (Chinese architecture), DeepSeek (MoE reasoning), Kimi (swarm agent), MiniMax (multimodal), Nemotron (enterprise safety). These are genuinely different model families with different blind spots.

4. **Skills add free intelligence** — a model with domain-specific instructions outperforms the same model without them. This is our secret weapon.

5. **Self-improvement via data** — not AI self-improvement (debunked), but data-driven optimization of routing rules (proven in production systems).

### What could go wrong:

1. **Orchestration overhead** — 3-5 model calls per query adds latency (5-30s for medium/hard). Acceptable for most use cases, not for real-time chat.

2. **Verifier quality** — if Nemotron can't accurately score which response is best, the system degrades to random selection. Need to calibrate verifier carefully.

3. **Diminishing returns** — going from 51 (GLM alone) to 55 (orchestrated) might be achievable. Going from 55 to 60 (beating Fable 5) might require fundamental breakthroughs, not just orchestration.

4. **The frontier keeps moving** — Claude Fable 5 is at 60 today. By the time we build this, it might be at 65. We need to move fast.

### Bottom line:

**Can we beat frontier?** Realistically, we can MATCH it (55-58 range) and be 5-10x cheaper. Beating it (60+) is the stretch goal — possible with skills + verifier + the right model combinations, but not guaranteed.

**Can we be #1 on cost-adjusted performance?** Yes, absolutely. GLM-5.2 alone at $0.06/task with intelligence 51 is already the best value on the planet. Orchestration only widens that gap.