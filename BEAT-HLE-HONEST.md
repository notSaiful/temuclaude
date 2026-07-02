# How to Beat HLE — The Honest Strategy (Revised)

## What Fugu Actually Does on HLE (from their technical report, Section 4.4)

Fugu uses three strategies for HLE, chosen PER QUESTION:

### 1. Debate and Aggregation (for knowledge questions)
- Produces a TREE topology per question
- One model at the HEAD (aggregator) synthesizes multiple leaf attempts
- The aggregator is chosen based on the question type:
  - Trivia/knowledge → Gemini (SOTA niche factual recall) as aggregator
  - Math → GPT as aggregator (math expertise)
- Leaf nodes: 2+ models attempt independently
- Aggregator identifies partial correctness in each leaf answer and synthesizes
- **Key example**: Both leaf agents got PARTIALLY correct answers. The aggregator combined the correct parts from both to produce a fully correct answer. Neither leaf alone could solve it.

### 2. Build and Debug (for agentic/coding tasks)
- GPT builds, Opus verifies/debugs
- Per-step alternation between models
- Opus exposes vulnerabilities in GPT's work, feeds back, GPT fixes

### 3. Bringing in a Specialist (for cross-domain questions)
- Start with one model's expertise (e.g., Opus for cybersecurity)
- Bring in another model for a different domain (e.g., GPT for math)
- Combine cross-domain expertise

### The Critical Insight Fugu Reveals:
> "Dynamic adaptation of an aggregator role is precisely the kind of adaptation unavailable to existing multi-agent systems (MoA, OpenRouter Fusion), which necessitate a fixed model to always act as a final synthesizer, regardless of whether that model is suitable for the task or not. Such systems are thereby bottlenecked by that rigidity."

**Fugu's advantage is DYNAMIC AGGREGATOR SELECTION.** It picks the right aggregator per question. Fixed-aggregator systems (Fusion, MoA) can't do this.

---

## What Fugu Does NOT Do (our opportunity)

1. **No web search / RAG.** Fugu doesn't use web search or retrieval on HLE. It relies purely on model knowledge. The paper says questions "resist simple internet lookup" — Fugu took this literally. We don't have to.

2. **No code execution.** Fugu doesn't execute code to verify math answers. It relies on model reasoning. For 41% of questions (math), this is a missed opportunity.

3. **No self-consistency.** Fugu doesn't sample multiple times and vote. It runs each topology once.

4. **No skills.** Fugu doesn't inject domain expertise via skills.

5. **No GEPA.** Fugu doesn't evolve its prompts.

6. **No Hermes.** Fugu uses a trained orchestrator model. We use Hermes with a skill.

---

## Our Honest Strategy for HLE

### What we CAN replicate from Fugu:
- Dynamic aggregator selection: Hermes (as orchestrator) picks the right aggregator per question. Math question → DeepSeek as aggregator. Knowledge question → GLM-5.2 as aggregator.
- Tree topology: 2+ models attempt, aggregator synthesizes
- Build and debug: for agentic tasks
- Bring in specialist: route to domain-specific model

### What we ADD that Fugu doesn't have:
1. **Web search + RAG** (deep research, not "simple lookup"): For knowledge questions, search for the specific topic, retrieve relevant papers/articles, feed as context. This is multi-step research — different from "simple internet lookup."
2. **Code execution for math** (41% of questions): Generate Python to solve, execute, verify. Ground truth.
3. **Self-consistency**: Run each topology N times, vote on final answer. Proven +10-20% on reasoning.
4. **Skills**: Domain-specific reasoning strategies per subject
5. **GEPA prompt evolution**: Optimize HLE-specific prompts weekly

### The honest math:

**Starting point**: GLM-5.2 alone gets 40.1% on HLE.

**What Fugu proves**: Dynamic orchestration with public models (Opus 49.8%, GPT 41.4%, Gemini 44.4%) gets 50.0%. That's +0.2 to +8.6 above the best individual model. The gain is small because HLE is knowledge-limited, not strategy-limited.

**Our challenge**: Our models are weaker individually (GLM 40.1% vs Fugu's best at 49.8%). We start 9.7 points behind Fugu's pool. Fugu's orchestration adds ~0.2-8.6 points. Our orchestration adds techniques Fugu doesn't use — but on a knowledge benchmark, those techniques have uncertain impact.

**What could work**:
- Web search + RAG: if the knowledge IS findable with deep research (multi-step, not simple lookup), this could add 5-15% on knowledge questions. The paper says questions resist "simple" lookup. Multi-step research is not simple.
- Code execution for math: for the 41% that's math, executing code eliminates computation errors. Could add 3-8%.
- Self-consistency: +10-20% on reasoning, but uncertain on HLE specifically.
- Dynamic aggregator: Fugu proves this helps. We replicate it.

**Honest projection**:
- Conservative: 45-50% (orchestration + code + some RAG benefit)
- Moderate: 50-55% (if RAG + self-consistency work well on HLE)
- Aggressive: 55-60%+ (if deep research + code + self-consistency + skills all compound)

**Fable 5: 53.3%. We MIGHT beat it. We might not. But we will be close.**

### The key unknown:
Does deep web research actually help on HLE? The paper says questions resist "simple internet lookup" — but nobody has tested whether MULTI-STEP research (search → retrieve → reason → search again → synthesize) helps. This is our unique bet. If it works, we beat Fable 5. If it doesn't, we get ~50% (matching Fugu).

### What we need to test:
1. Run GLM-5.2 alone on HLE → baseline (should be ~40%)
2. Add self-consistency (N=20) → measure improvement
3. Add code execution for math → measure improvement
4. Add web search + RAG → measure improvement
5. Add dynamic aggregator (Fugu pattern) → measure improvement
6. Add skills → measure improvement

We won't know until we test. But every technique has published evidence of helping on SOME benchmark. The question is whether they transfer to HLE.

---

## The Honest Truth

I was wrong to project "55-75%" with confidence. The truth is:

- Fugu gets 50% with orchestration alone (proven)
- Our models are weaker than Fugu's pool (fact)
- Our techniques (code, RAG, self-consistency) are proven on OTHER benchmarks but UNTESTED on HLE
- We might beat 53.3%. We might get 50%. We won't know until we build and test.

But here's what I know for certain: **we will be the first system to try all of these techniques together on HLE.** Nobody has combined dynamic orchestration + code execution + deep web research + self-consistency + skills + GEPA on HLE. Fugu only does orchestration. We do everything.

If even ONE of our additional techniques works on HLE — code execution, or RAG, or self-consistency — we match or beat Fable 5. If multiple work, we exceed it.

That's not a guarantee. That's a hypothesis we need to test. And testing is exactly what we'll do.