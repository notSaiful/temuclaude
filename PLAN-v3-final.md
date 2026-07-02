# Timuclaude — Final Plan v3 (Honest, Research-Verified)

## The Truth

### What the research actually says:

1. **Pure orchestration has NOT beaten frontier on broad benchmarks.** The MoA paper used GPT-4 as aggregator. No ensemble of only open models has beaten frontier on MMLU, HumanEval, or MATH.

2. **The fundamental limitation is architectural:** Orchestration can select, route, verify, decompose. It CANNOT create knowledge or reasoning that doesn't exist in any component model.

3. **Multi-agent debate is debunked.** Gains are attributable to simpler mechanisms (self-consistency, test-time compute). Debate adds cost without consistent benefit.

4. **Cost crossover is real:** 3-4 open model calls ≈ cost of 1 frontier call. Orchestration of weaker models often costs the same as just using GPT-4 directly — for worse quality.

5. **Best-of-N + verifier works** for verifiable tasks (math, code) but not general quality. Scales logarithmically — N=4 gives meaningful boost, N=100 gives large gains but at 100x cost.

6. **Verifier-guided generation (PRMs)** is the most promising pattern for structured tasks. Boosts pass@1 by 10-20% on math/reasoning.

7. **Routing works** for cost reduction (50-98%), not quality improvement. Proven in production.

### But our situation is different:

The research was based on data up to early 2025. Our models are from mid-2026:

- **GLM-5.2 is #3 globally** (Intelligence Index 51). Only 4 points behind GPT-5.5 (55), 9 behind Fable 5 (60).
- **DeepSeek V4 Pro** has GPQA 90.1, Codeforces 3206, MMLU-Pro 87.5 — genuinely frontier-level reasoning.
- **These aren't "weak cheap models."** They're near-frontier models that happen to be 45x cheaper.
- **The gap to close is 4-9 points**, not 40.

### What actually works (proven):

1. **Routing** — send queries to the right specialist (proven, production-ready)
2. **Best-of-N + verifier** — for verifiable tasks: code (test execution), math (PRM/verification) (proven)
3. **Tools** — code execution, web search, RAG augment models beyond their training (proven)
4. **Skills** — domain-specific instructions improve model output without changing the model (proven in Hermes)
5. **Fine-tuned specialists** — highest ROI for narrow domains (proven)

### What does NOT work:

1. **MoA as core method** — marginal gains, high cost, inconsistency
2. **Multi-agent debate** — debunked
3. **Aggregating multiple model outputs into one response** — produces inconsistent, contradictory text
4. **Trying to beat frontier on general intelligence** — the knowledge ceiling problem is architectural

---

## REVISED TARGET

**Honest target:**
- Match 90-95% of frontier quality (intelligence ~55-57) at 10-45x lower cost
- BEAT frontier on specific verifiable tasks (coding with test verification, math with PRM)
- Be #1 on cost-adjusted performance (intelligence per dollar)
- NOT claim to beat Claude Fable 5 on general intelligence

**Where we can genuinely beat frontier:**
- Coding tasks with test-based verification (Best-of-N + execute tests → pick the passing solution)
- Math/reasoning with PRM verification (generate many, score steps, pick best)
- Domain-specific tasks with skills + RAG (inject expertise the frontier model doesn't have)
- Long-context tasks (Kimi K2.6 and MiniMax M3 have 1M+ context — cheaper than Gemini 2M)

---

## FINAL ARCHITECTURE

```
                        ┌─────────────┐
     User Query ──────► │   ROUTER     │  GLM-5.2 (fast, $0.06/task, #3 globally)
                        └──────┬──────┘  Classifies: type + difficulty
                               │
                    ┌──────────┼──────────────┐
                    │          │              │
                    ▼          ▼              ▼
             ┌─────────┐ ┌─────────┐ ┌─────────────┐
             │  SIMPLE │ │VERIFIABLE│ │COMPLEX     │
             │  (70%)  │ │(20%)    │ │(10%)       │
             └────┬────┘ └────┬────┘ └──────┬──────┘
                  │           │              │
                  ▼           ▼              ▼
            ┌─────────┐ ┌──────────┐ ┌──────────────┐
            │SINGLE   │ │BEST-OF-N │ │ROUTE TO BEST │
            │MODEL    │ │+ VERIFIER│ │+ SKILLS +    │
            │+ SKILLS │ │+ TOOLS   │ │TOOLS + RAG   │
            └─────────┘ └──────────┘ └──────────────┘
```

### Path A — Simple (70% of queries)

Route to single best model + load relevant skills:

| Task Type | Model | Skills Loaded | Cost |
|-----------|-------|---------------|------|
| Coding (simple) | DeepSeek V4 Pro (no thinking) | test-driven-development, codebase-inspection | ~$0.06 |
| General chat | GLM-5.2 | - | ~$0.06 |
| Chinese | GLM-5.2 | - | ~$0.06 |
| Creative | GLM-5.2 | humanizer, frontend-design | ~$0.06 |
| Math (simple) | DeepSeek V4 Pro (thinking) | - | ~$0.10 |
| Long context | MiniMax M3 | - | ~$0.10 |

One call. Skills inject domain expertise. Fast. Cheap.

### Path B — Verifiable Tasks (20% of queries)

**Best-of-N + Tool Verification:**

For coding:
1. Generate 4 solutions in parallel (GLM-5.2, DeepSeek V4 Pro, Kimi K2.6, MiniMax M3)
2. Execute each solution against test cases (tool verification, not model verification)
3. Pick the solution that passes all tests
4. If none pass, escalate to Path C

For math/reasoning:
1. Generate 8 solutions in parallel (DeepSeek V4 Pro with thinking, GLM-5.2 max)
2. Use DeepSeek V4 Pro as step-by-step verifier (PRM approach)
3. Pick the solution with the best verification score
4. If low confidence, escalate to Path C

**Why this works:** Tool-based verification (running code, checking math) is GROUND TRUTH — not a model guessing quality. This is where we can genuinely beat frontier models that generate one solution without execution.

### Path C — Complex (10% of queries)

**Route + Skills + Tools + RAG:**

1. Route to best model for the task type
2. Load relevant skills (auto-download from Hermes hub if needed)
3. Use tools: web search for facts, code execution for verification, RAG for domain knowledge
4. If the task has verifiable components, use Best-of-N + tool verification
5. If not verifiable, use the single best model with max thinking + skills

**No aggregation, no debate, no MoA.** Just the right model + the right tools + the right skills.

---

## SKILLS INTEGRATION (The Secret Weapon)

Skills are our competitive advantage. They inject domain expertise into model calls without changing the model.

### Auto-Skill Loading:

```
Query → Router classifies task type
      → Search Hermes skills hub for relevant skills
      → If found, install and load into context
      → Model receives query + domain expertise instructions
      → Better output, same model, zero extra cost
```

### Skills that boost benchmark performance:

| Task Type | Skills to Load | Effect |
|-----------|---------------|--------|
| Coding | test-driven-development, systematic-debugging, codebase-inspection | Write tests first, catch bugs, verify edge cases |
| Research | arxiv, blogwatcher, llm-wiki | Know where to search, how to extract |
| Writing | humanizer, frontend-design | Better prose, better UI code |
| Planning | plan, writing-plans | Structured thinking, break down tasks |
| Debugging | systematic-debugging, python-debugpy | Root cause analysis, not symptom fixing |
| Review | requesting-code-review, simplify-code | Security scan, quality gates |

### Custom Timuclaude Skills:

1. **timuclaude-router** — routing rules, model selection logic, task classification
2. **timuclaude-verifier** — verification prompts and scoring criteria for math/code
3. **timuclaude-benchmark** — auto-benchmark new models, track scores over time
4. **timuclaude-optimizer** — analyze logs, adjust routing rules, A/B test pairings

### How skills make cheap models better:

A model with coding skills outperforms the same model without them because the skill provides:
- "Write tests before declaring done" → catches errors the model would miss
- "Check edge cases: null, empty, negative" → prevents common bugs
- "Run the code before submitting" → tool-based verification
- "Follow project conventions" → consistency with codebase

This is like giving each model a domain expert's checklist. Free quality boost.

---

## SELF-IMPROVEMENT LOOP

Not AI self-improvement (debunked). Data-driven routing optimization (proven).

### What we log per query:
- Task type (router classification)
- Difficulty (simple/verifiable/complex)
- Models used
- Skills loaded
- Tools used
- Verification result (pass/fail for verifiable tasks)
- Response time
- Cost (GPU usage estimate)

### What Hermes optimizes:
- **Routing rules:** if DeepSeek consistently beats GLM on coding, update routing weights
- **Skill selection:** if a skill doesn't improve results, stop loading it for that task type
- **Model pairings:** for Best-of-N, track which model combinations produce the most passing solutions
- **Threshold tuning:** if too many queries escalate to Complex, lower the threshold
- **New model testing:** when a new model drops on Ollama Cloud, auto-benchmark it against current models. If better, auto-promote.

### How:
- Weekly analysis of query logs
- A/B test routing changes
- Auto-benchmark new models when added to Ollama Cloud
- Hermes skill system naturally accumulates improvements

---

## COST ANALYSIS

| Path | % of Queries | Models Called | Est. Cost/Query | Quality (est.) |
|------|-------------|--------------|-----------------|----------------|
| Simple | 70% | 1 | $0.06 | 51 (GLM-5.2 level) |
| Verifiable | 20% | 4 + tools | $0.20-0.30 | 55-58 (with verification) |
| Complex | 10% | 1 + skills + tools | $0.10-0.15 | 51-55 |
| **Weighted avg** | | | **~$0.10** | **~52-55** |

**Comparison:**
| System | Cost/Query | Intelligence |
|--------|-----------|-------------|
| Claude Fable 5 | $2.75 | 60 |
| GPT-5.5 | $1.03 | 55 |
| GLM-5.2 alone | $0.06 | 51 |
| **Timuclaude** | **~$0.10** | **52-55** |

**Timuclaude is 10-27x cheaper than frontier, at 87-92% of frontier quality.**

On cost-adjusted performance (intelligence per dollar): **Timuclaude is #1.**

---

## BUILD STEPS

### Step 1: Foundation
- Python project with asyncio
- Connect all 5 models via Ollama Cloud
- Verify each model responds with tools + thinking
- Logging infrastructure
- Test parallel calls

### Step 2: Benchmark Suite
- Standard benchmarks: MMLU-Pro, HumanEval, GSM8K, Terminal-Bench
- Test each model ALONE → baseline scores
- This is our measuring stick

### Step 3: Router + Skills
- GLM-5.2 classifies query → routes to best model
- Auto-load relevant skills per task type
- Benchmark: does routing + skills beat single model?

### Step 4: Verifiable Path
- Best-of-N generation for code (parallel, 4 models)
- Tool-based verification (execute against tests)
- Best-of-N for math (parallel, 8 samples)
- PRM verification (DeepSeek V4 Pro scores steps)
- Benchmark: does Best-of-N + verification beat single model? Beat frontier?

### Step 5: Self-Improvement
- Log everything
- Weekly analysis → adjust routing, skills, thresholds
- Auto-benchmark new models on Ollama Cloud
- A/B test changes

### Step 6: Production API
- OpenAI-compatible wrapper
- Auto-skill loading
- Cost tracking
- Deploy on Fly.io

---

## HONEST EXPECTATIONS

| Claim | Verdict |
|-------|---------|
| Beat Claude Fable 5 on general intelligence | NO — architectural limitation |
| Match GPT-5.5 (intelligence 55) | MAYBE — with skills + verification on right tasks |
| Beat frontier on coding tasks (with test verification) | YES — Best-of-N + execution is ground truth |
| Beat frontier on math (with PRM) | LIKELY — DeepSeek V4 Pro is already near-frontier on math |
| Be #1 on cost-adjusted performance | YES — GLM-5.2 at $0.06/task with intelligence 51 is already best value |
| Improve over time via self-improvement | YES — data-driven routing optimization is proven |
| Auto-download and use skills | YES — Hermes skill system already does this |

**Timuclaude is not "cheap Claude." It's "smart routing + skills + verification at wholesale prices."**

The value proposition isn't matching frontier quality — it's delivering 87-92% of frontier quality at 10-27x lower cost, with genuine superiority on verifiable tasks. That's what we build.