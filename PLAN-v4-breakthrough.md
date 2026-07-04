# Temuclaude — PLAN v4 (The Breakthrough)

## How Sakana Fugu Actually Beats Frontier Models

### The Secret: Fugu is NOT orchestration. It's a TRAINED ORCHESTRATOR MODEL.

Fugu doesn't do simple routing or MoA. Fugu is itself a language model that has been **trained** (fine-tuned + evolutionary strategies + reinforcement learning) to:

1. Understand user queries
2. **Dynamically devise agentic scaffolds** to solve them
3. Coordinate a pool of frontier worker models through those scaffolds

This is the key insight I was missing. Fugu is not a script that routes queries. It's a MODEL that learned how to orchestrate other models.

### The Three Training Stages:

**Stage 1: Supervised Fine-Tuning (SFT)**
- Train the orchestrator model on single-step tasks: "given this query, which model should handle it?"
- This gives the orchestrator basic routing ability

**Stage 2: Evolutionary Strategies**
- Apply evolutionary optimization on end-to-end tasks
- The orchestrator learns to plan multi-step workflows: "first try model A, then if that fails, try model B with modified prompt"
- Uses evolutionary search to find optimal coordination strategies
- Based on TRINITY paper (ICLR 2026): a compact coordinator model optimized with evolutionary strategy, delegates three roles — Thinker, Worker, Verifier — to a pool of LLMs turn by turn

**Stage 3: Reinforcement Learning (Conductor)**
- Train the orchestrator with GRPO (reinforcement learning)
- The orchestrator learns to output full "agentic workflows" as natural language
- Each workflow = sequence of steps, each step has: subtask description, assigned worker model, access list (what previous outputs to include)
- Reward: 0 if workflow can't be parsed, 0.5 if executed but wrong answer, 1.0 if correct answer
- Based on Conductor paper (ICLR 2026): RL-trained model that discovers coordination strategies that outperform any individual model

### What Fugu Discovered (Section 4.4 — Optimal Strategies):

The trained orchestrator discovered three main coordination patterns:

1. **Debate and aggregation** — multiple models generate independently, then debate/refine
2. **Build and debug** — one model generates, another reviews and debugs iteratively
3. **Bringing in a specialist** — general model starts, then a specialist model is called for the hard part

The orchestrator learned WHEN to use each pattern based on the query type. This is not hand-coded routing — it's learned coordination.

### Fugu's Benchmark Results (from their paper):

Fugu-Ultra matches or beats Fable 5 and Mythos Preview on:
- SWE-Bench Pro (software engineering)
- Terminal Bench (agentic coding)
- LiveCodeBench (competitive coding)
- GPQA-Diamond (scientific reasoning)
- Humanity's Last Exam (reasoning & knowledge)
- CharXiv Reasoning

**And Fugu does NOT have Fable 5 or Mythos in its agent pool.** It orchestrates publicly accessible models and MATCHES the closed frontier.

---

## THE BREAKTHROUGH FOR TEMUCLAUDE

### What I Got Wrong Before:

I was thinking about orchestration as SCRIPTS (if-else routing, Best-of-N, verifier). Fugu proved that orchestration should be a TRAINED MODEL that learns to coordinate.

### What We Can Actually Do:

We can't train a model from scratch like Sakana did (they have GPU clusters and months of RL). But we CAN do something they didn't:

**Use Hermes as the orchestrator.**

Hermes IS already an orchestrator model. It:
- Understands queries
- Has tool-calling ability
- Can delegate to subagents
- Has skills that inject domain expertise
- Learns from every session (memory)
- Can call multiple models via Ollama Cloud

The key realization: **Hermes + Ollama Cloud models = a poor man's Fugu.**

### The Temuclaude Architecture (Final):

```
                        ┌─────────────────────┐
     User Query ──────► │   HERMES (Orchestrator)    │
                        │   with Temuclaude skill     │
                        └──────────┬──────────┘
                                   │
                    Hermes analyzes query and dynamically
                    devises an agentic scaffold:
                    - Which model(s) to call
                    - What prompt to send each
                    - What order to call them
                    - Whether to debate, build-and-debug, or specialist
                    - Whether to use tools (code execution, web search)
                    - Whether to load skills
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
              ┌─────────┐  ┌─────────┐  ┌─────────┐
              │  GLM-5.2 │  │DeepSeek │  │ Kimi K2.6│
              │  (Thinker)│ │(Worker) │  │(Worker) │
              └─────────┘  └─────────┘  └─────────┘
              ┌─────────┐  ┌─────────┐
              │ MiniMax  │  │Nemotron │
              │ (Worker) │  │(Verifier)│
              └─────────┘  └─────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │  Hermes synthesizes output   │
                    │  Verifier checks quality     │
                    │  If wrong → retry with diff  │
                    │  If right → return to user   │
                    └─────────────────────────────┘
```

### Why This Can Beat Frontier:

1. **Hermes is a capable orchestrator.** It can think, plan, and adapt — not just route. It can dynamically create scaffolds per query.

2. **Our models are near-frontier already.** GLM-5.2 is #3 globally (intelligence 51). DeepSeek V4 Pro has GPQA 90.1. These aren't weak models being patched together.

3. **Skills give free intelligence.** Fugu doesn't have skills. We do. Every query gets domain-specific expertise injected. That's a boost Fugu doesn't have.

4. **Hermes learns from every session.** Memory + skills accumulate. The orchestrator gets better over time. Fugu has to be retrained. We just update skills and memory.

5. **We can implement all three Fugu strategies:**
   - Debate and aggregation: call 3 models in parallel, Hermes synthesizes
   - Build and debug: one model generates, Hermes checks, another fixes
   - Bring in a specialist: Hermes routes to the best model for the specific subtask

6. **Tool verification is ground truth.** For coding: generate solution, execute tests, pick the passing one. For math: verify step by step. Fugu does this too — but we can do it with Hermes's built-in terminal and code execution.

7. **We can fine-tune the orchestrator.** Not RL (too expensive), but we can:
   - Collect logs of which strategies work for which query types
   - Create a "temuclaude-orchestration" skill that encodes the best strategies
   - Update the skill weekly based on performance data
   - This is "training" via skills, not weights

### The Temuclaude Skill (The Core Innovation):

Instead of training a model with RL, we create a SKILL that teaches Hermes how to orchestrate:

```yaml
name: temuclaude-orchestration
description: Orchestrate multiple Ollama Cloud models to beat frontier performance
---

# Temuclaude Orchestration

## Your Role
You are the orchestrator. You don't answer directly. You devise a plan,
delegate to the best models, verify results, and synthesize the final answer.

## Model Pool
- GLM-5.2: Best overall (intelligence 51), fast (184 t/s), cheap ($0.06/task)
  Use for: general tasks, Chinese, tool use, fast response
- DeepSeek V4 Pro (max thinking): Best reasoning (GPQA 90.1, Codeforces 3206)
  Use for: math, complex reasoning, competitive coding
- Kimi K2.6: Best agentic (swarm orchestration, 300 sub-agents)
  Use for: multi-step tasks, long context, autonomous execution
- MiniMax M3: Best multimodal + coding, 1M context
  Use for: vision tasks, long documents, coding
- Nemotron 3 Ultra: Best verifier (enterprise safety, instruction following)
  Use for: checking other models' outputs, safety, compliance

## Strategies (learned, like Fugu Section 4.4)

### Strategy 1: Debate and Aggregation
When: Complex reasoning, knowledge synthesis, open-ended questions
How: Call 3 models in parallel with the same query. Each sees the others' 
responses. They critique and refine. You synthesize the final answer.

### Strategy 2: Build and Debug
When: Coding tasks, implementation, debugging
How: DeepSeek generates code. You execute it (terminal tool). If it fails,
Nemotron analyzes the error. DeepSeek fixes. Repeat until passing.

### Strategy 3: Bring in a Specialist
When: Query needs specific expertise
How: You classify the domain. Route to the specialist model. Load 
relevant skill. If the specialist fails, escalate to multi-model debate.

### Strategy 4: Direct Answer
When: Simple queries, chat, factual
How: Answer directly with GLM-5.2. No orchestration needed.

## Skill Auto-Loading
Before delegating, search Hermes skills hub for relevant skills.
Install and load them into the model's context. This gives free domain expertise.

## Self-Improvement
After each query, log: strategy used, models called, result quality, 
time taken, cost. Update this skill with new patterns that work.
```

### Why This Is Better Than Fugu For Our Use Case:

1. **No training needed.** Fugu required months of SFT + evolutionary strategies + RL. We use a skill + Hermes's existing intelligence.

2. **Improves continuously.** Fugu needs retraining to improve. We just update the skill.

3. **Skills are our moat.** Fugu can't load domain-specific skills. We can. Every domain gets a free quality boost.

4. **Cheaper.** Fugu charges per API call (they're a company). We use Ollama Cloud ($20/mo Pro or $100/mo Max) with no per-query cost.

5. **Hermes has tools.** Code execution, web search, file I/O — Fugu is just a model API. Hermes is a full agent platform.

---

## BUILD STEPS (Revised — Fast)

### Step 1: Foundation
- Python project with asyncio
- All 5 models on Ollama Cloud verified
- Logging infrastructure

### Step 2: The Temuclaude Skill
- Write the orchestration skill (the core innovation)
- Implement all 4 strategies
- Auto-skill-loading for domain expertise

### Step 3: Benchmark
- Test on MMLU-Pro, HumanEval, GSM8K, Terminal-Bench, GPQA
- Compare: single model vs orchestrated vs frontier
- This is our proof

### Step 4: Self-Improvement Loop
- Log every query
- Hermes analyzes which strategies work per task type
- Update skill with new patterns
- Auto-benchmark new models when released on Ollama Cloud

### Step 5: Production API
- OpenAI-compatible wrapper
- Users point at Temuclaude instead of GPT-4
- Cost: $20-100/mo Ollama Cloud (no per-query cost)
- Quality: target 55-60+ intelligence index

---

## THE HONEST PREDICTION

Can we beat Claude Fable 5 (intelligence 60)?

**With Hermes as orchestrator + 5 near-frontier models + skills + tool verification:**

- **Intelligence 52-55:** Very likely (GLM-5.2 alone is 51, orchestration adds 1-4 points)
- **Intelligence 55-58:** Likely with good strategies + skills + verification on right tasks
- **Intelligence 58-60:** Possible on specific benchmarks (coding with test execution, math with PRM)
- **Intelligence 60+ (beating Fable 5):** Possible on specific tasks where tool verification gives ground truth. Unlikely on general intelligence.

**But here's what makes it sellable:**

1. **Cost:** $20-100/mo flat vs Fugus per-query pricing vs Claude's $2.75/task
2. **Privacy:** Ollama Cloud models don't train on your data
3. **Transparency:** Open models, open orchestration logic, open skills
4. **Improving:** Gets better every week as skills accumulate
5. **Skills:** Free domain expertise that Fugu/Claude/GPT don't have

**People will use Temuclaude because it's 90-95% as good as frontier at 1/50th the cost, with skills that make it BETTER than frontier on specific domains.**

That's the value proposition. That's how we win.