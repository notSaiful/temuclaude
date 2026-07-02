# Timuclaude — Hermes Agent Full Power Analysis

## How to Exploit Every Hermes Capability for Timuclaude

---

## 1. HERMES AGENT STATE (July 2026)

From the ecosystem research:

- **188,000 GitHub stars** (from 40K in April — 24K stars/week at peak)
- **90,000+ community skills** in the Skills Hub
- **22 releases** in 6 weeks (v0.11 → v0.15.1)
- **17+ LLM providers** supported
- **NVIDIA selected Hermes** as reference runtime for Nemotron 3 Ultra (550B params)
- **40,000+ desktop app beta users**
- **276 documented use cases**

This is the most popular open-source AI agent platform in the world. We're building on the right foundation.

---

## 2. HERMES CAPABILITIES FOR TIMUCLAUDE

### A. Subagent Delegation (delegate_task) — OUR FUSION PANEL

Hermes can spawn up to 3 concurrent subagents (configurable, no hard ceiling). Each gets:
- Isolated context (fresh conversation)
- Restricted toolsets (we can give each subagent a different model)
- Own terminal session
- Only final summary enters parent context

**For Timuclaude:** This IS our Fusion panel. Instead of calling 3 models through an API, we delegate to 3 subagents — each using a different Ollama Cloud model. Each generates independently. Hermes (parent) receives all 3 summaries and synthesizes.

```python
delegate_task(tasks=[
    {"goal": "Answer this query", "context": "Use GLM-5.2. Query: ...", "toolsets": ["terminal"]},
    {"goal": "Answer this query", "context": "Use DeepSeek V4 Pro. Query: ...", "toolsets": ["terminal"]},
    {"goal": "Answer this query", "context": "Use Kimi K2.6. Query: ...", "toolsets": ["terminal"]},
])
```

**Advantage over Fusion Router:** Fusion charges per-query for each panel model. We use Ollama Cloud flat rate. Plus our subagents can use tools (terminal, file, web) — Fusion panel models only get web_search.

### B. Kanban Multi-Agent Board — OUR ORCHESTRATION BACKBONE

Durable task board in SQLite. Multiple named agents collaborate:
- Tasks with status: triage → todo → ready → running → blocked → done → archived
- Task links (parent → child dependencies)
- Comments (inter-agent protocol)
- Workspaces (scratch, repo, persistent)
- Dispatcher (auto-spawns workers, reclaims stale claims)
- Failure limit (auto-block after N consecutive failures)

**For Timuclaude:** This is our production orchestration system. Instead of ad-hoc delegation, we use Kanban for complex multi-step tasks:
1. Create task: "Solve this benchmark problem"
2. Dispatcher assigns to best model profile (GLM-5.2 profile, DeepSeek profile, etc.)
3. Worker solves, marks done
4. Verifier profile reviews, comments
5. If rejected → re-assign to different model
6. All durable, survives restarts, auditable

**Advantage over Fugu:** Fugu's coordination is in-memory (lost on restart). Kanban is durable SQLite — survives crashes, auditable, human-in-the-loop capable.

### C. Self-Evolution (DSPy + GEPA) — OUR OPRO LAYER (ALREADY BUILT)

Hermes Agent Self-Evolution repository (NousResearch/hermes-agent-self-evolution):
- Uses DSPy (Stanford) + GEPA (Genetic-Pareto Prompt Evolution, ICLR 2026 Oral)
- Reads execution traces to understand WHY things fail
- Proposes targeted mutations (not random rewrites)
- Evaluates candidates against test suite + size limits + semantic drift
- Selects best variant, opens PR
- **No GPU needed** — operates via API calls, $2-10 per optimization run
- MIT licensed

**For Timuclaude:** This IS the OPRO layer I planned — but already built and tested by Nous Research. We use it to:
1. Evolve our timuclaude-orchestration skill — optimize the prompts that tell Hermes how to orchestrate
2. Evolve model-specific prompts — find the best prompt for each model per task type
3. Evolve verifier prompts — optimize how Nemotron judges responses
4. Evolve synthesis prompts — optimize how GLM-5.2 combines panel outputs

**How to run it:**
```bash
git clone https://github.com/NousResearch/hermes-agent-self-evolution.git
export HERMES_AGENT_REPO=~/.hermes/hermes-agent
python -m evolution.skills.evolve_skill \
    --skill timuclaude-orchestration \
    --iterations 10 \
    --eval-source sessiondb  # uses real session history
```

**Advantage over Fugu:** Fugu requires RL retraining (GPU-intensive, expensive, months). We evolve prompts via API calls — $2-10 per run, no GPU, hours not months. And it's already built.

### D. Skills System — OUR DOMAIN EXPERTISE LAYER

- 90,000+ community skills in Hermes Hub
- Auto-creation from experience (built-in since v0.2)
- Curator (autonomous skill maintenance, since v0.12)
- Self-evolution (genetic optimization of skills, since June 2026)
- Skills are just SKILL.md files — instruction sets, not compiled plugins
- Auto-loaded per task type
- Searchable via /skills

**For Timuclaude:** Before each query, Hermes searches for relevant skills:
- Coding → loads test-driven-development, systematic-debugging, codebase-inspection
- Research → loads arxiv, blogwatcher, web-search
- Math → loads reasoning-focused skills
- Writing → loads humanizer, frontend-design

**The 3-layer skill lifecycle for Timuclaude:**
1. **Create** — Hermes creates new skills from successful orchestration patterns
2. **Maintain** — Curator prunes unused/bad skills
3. **Evolve** — GEPA optimizes skill prompts against benchmarks

This is the Voyager pattern (skill library that compounds) — but already built into Hermes.

### E. Memory System — OUR SELF-IMPROVEMENT DATA

4 layers:
- SQLite session store (every conversation, searchable via FTS5)
- MEMORY.md (durable facts, ~2,200 chars)
- USER.md (user profile, ~1,375 chars)
- Skills (reusable procedures)

**For Timuclaude:** Memory stores:
- Which models work best for which task types (from real usage data)
- Which orchestration strategies produce the best results
- Which skills improve benchmark scores
- User preferences and patterns

### F. Session Search (FTS5) — OUR TRAINING DATA

Full-text search over past conversations. No LLM calls needed — pure SQLite FTS5.

**For Timuclaude:** When facing a new query, search past sessions for similar queries:
- "What strategy worked last time we had a coding problem like this?"
- "Which model combination produced the best result on a similar math problem?"
- "What skills were loaded when we got the best score?"

This is ground-truth data from real usage — not synthetic training data.

### G. Cron Jobs — OUR CONTINUOUS IMPROVEMENT

Scheduled tasks that run automatically:
- Daily: benchmark new models on Ollama Cloud, update routing
- Weekly: run GEPA evolution on timuclaude-orchestration skill
- Weekly: analyze session logs, update memory with best patterns
- Monthly: full benchmark suite, compare against frontier scores

### H. Profiles — OUR MODEL-SPECIFIC CONFIGURATIONS

Each model gets its own Hermes profile:
- `timuclaude-glm` — GLM-5.2 config + skills + memory
- `timuclaude-deepseek` — DeepSeek V4 Pro config + skills + memory
- `timuclaude-kimi` — Kimi K2.6 config + skills + memory
- `timuclaude-minimax` — MiniMax M3 config + skills + memory
- `timuclaude-nemotron` — Nemotron 3 Ultra config + skills + memory
- `timuclaude-orchestrator` — Hermes config that delegates to the above

Profiles are shareable as Git repos (since v0.14). We can distribute Timuclaude as a set of profiles.

### I. MCP Client — OUR TOOL EXPANSION

Native MCP client support. We already installed 12+ MCP servers. For Timuclaude:
- filesystem — file access
- puppeteer / chrome-devtools — browser automation for web verification
- context7 — documentation lookup
- firecrawl — web scraping for RAG
- sequential-thinking — structured reasoning
- memory MCP — knowledge graph

### J. OpenAI-Compatible Proxy — OUR PRODUCTION API

Since v0.14, Hermes has an OpenAI-compatible proxy server. Any tool that talks to OpenAI can talk to Hermes. This IS our production API — users point their app at Timuclaude instead of OpenAI.

### K. Persistent Goals (/goal) — OUR BENCHMARK OPTIMIZATION

Standing goals that Hermes works on across turns:
- "Optimize Timuclaude to beat Fable 5 on Terminal-Bench"
- "Find the best model combination for GPQA Diamond"
- "Evolve the orchestration skill to improve SWE-Bench scores"

Hermes works on these autonomously, across sessions.

### L. Context Files (.hermes.md / AGENTS.md) — PROJECT-SPECIFIC INSTRUCTIONS

For Timuclaude, we create a `.hermes.md` in the project directory:
- Project conventions
- Model configurations
- Benchmark targets
- Skill loading rules
- Orchestration strategy preferences

---

## 3. THE COMPLETE TIMUCLAUDE STACK (HERMES-POWERED)

```
User Query
    ↓
┌──────────────────────────────────────────────────────┐
│  HERMES AGENT (Orchestrator Profile)                 │
│                                                      │
│  1. Analyze query (task type, difficulty)            │
│  2. Auto-load skills from Hub (90K+ available)       │
│  3. Search past sessions for similar queries (FTS5)  │
│  4. Decide strategy:                                 │
│     - Direct: 1 model + skills (60%)                 │
│     - Fusion: delegate_task to N subagents (35%)     │
│     - MCTS: tree search with PRM (5%)                │
│                                                      │
│  IF FUSION:                                          │
│  5. delegate_task to 3-5 subagents (parallel)        │
│     - Each uses different Ollama Cloud model         │
│     - Each has relevant skills loaded                │
│     - Each can use tools (terminal, web, file)       │
│  6. Hermes receives all summaries                    │
│  7. Structured analysis (consensus/contradictions/   │
│     insights/blind_spots) — Fusion pattern           │
│  8. Synthesize final answer                          │
│                                                      │
│  IF VERIFIABLE:                                      │
│  9. Tool verification (execute code, verify math)    │
│  10. If fails → OPRO retry with optimized prompt     │
│  11. Self-consistency (N runs, majority vote)        │
│                                                      │
│  ALWAYS:                                             │
│  12. Log to session store (FTS5 searchable)          │
│  13. Extract skill if new pattern discovered          │
│  14. Update memory with results                      │
│                                                      │
│  LITELLM (underneath):                               │
│  - Adaptive Router learns best model per task type   │
│  - Fallbacks if model fails                          │
│  - Cost tracking                                     │
│  - Unified API to all Ollama Cloud models            │
│                                                      │
│  SELF-EVOLUTION (weekly cron):                       │
│  - GEPA evolves orchestration skill prompts          │
│  - DSPy optimizes model-specific prompts             │
│  - $2-10 per run, no GPU needed                      │
│                                                      │
│  KANBAN (for complex tasks):                         │
│  - Durable task board across model profiles          │
│  - Survives restarts                                 │
│  - Human-in-the-loop capable                         │
│  - Auditable                                         │
└──────────────────────────────────────────────────────┘
    ↓
  OUTPUT + cost report + strategy used + models called
```

---

## 4. WHAT HERMES GIVES US THAT NOBODY ELSE HAS

| Capability | Fugu | Maestro | Fusion | Model Council | Hermes (us) |
|-----------|------|---------|--------|---------------|-------------|
| Subagent delegation | ❌ | ❌ | ❌ | ❌ | ✅ delegate_task |
| Durable multi-agent board | ❌ | ❌ | ❌ | ❌ | ✅ Kanban |
| Self-evolution (GEPA) | ❌ | ❌ | ❌ | ❌ | ✅ DSPy+GEPA |
| Skill library (90K+) | ❌ | ❌ | ❌ | ❌ | ✅ |
| Session search (FTS5) | ❌ | ❌ | ❌ | ❌ | ✅ |
| Persistent goals | ❌ | ❌ | ❌ | ❌ | ✅ /goal |
| Cron automation | ❌ | ❌ | ❌ | ❌ | ✅ |
| Profiles (shareable) | ❌ | ❌ | ❌ | ❌ | ✅ |
| MCP client | ❌ | ❌ | ❌ | ❌ | ✅ |
| OpenAI-compatible proxy | ✅ | ✅ | ✅ | ❌ | ✅ |
| Memory (4 layers) | ❌ | ❌ | ❌ | ❌ | ✅ |
| Context files | ❌ | ❌ | ❌ | ❌ | ✅ |
| Terminal/file/web tools | ❌ | ❌ | web only | ❌ | ✅ full |

**Hermes is not just our orchestrator. Hermes is our entire platform.** Fugu is a model API. Maestro is a routing proxy. Fusion is a deliberation tool. Model Council is a feature. Hermes is a complete agent runtime with 188K stars, 90K skills, and NVIDIA backing.

---

## 5. THE SELF-IMPROVEMENT LOOP (COMPLETE)

Three layers, all built into Hermes:

1. **Create** (built-in since v0.2): Agent creates skills from successful patterns
2. **Maintain** (Curator, since v0.12): Prunes unused skills, grades quality
3. **Evolve** (Self-Evolution, June 2026): GEPA genetically optimizes skill prompts

Plus:
4. **Adaptive Router** (LiteLLM): Learns which model is best per task type
5. **Session Search** (FTS5): Retrieves past successful strategies
6. **Memory**: Stores durable facts about what works
7. **Cron**: Runs weekly evolution, daily benchmarks, continuous improvement

**This is the most complete self-improvement stack of any AI system.** Fugu needs months of RL retraining. We evolve prompts for $2-10 per run, weekly, automatically.

---

## 6. KEY INSIGHT

**Timuclaude is not just "models + routing." Timuclaude is "Hermes Agent + 5 Ollama Cloud models + LiteLLM + 8 orchestration strategies + 90K skills + self-evolution + Kanban + session search + cron automation."**

No competitor has this stack. Not Fugu. Not Maestro. Not Fusion. Not Model Council. Not OpenRouter.

This is how we beat frontier: not with a bigger model, but with a smarter SYSTEM that learns, evolves, and compounds over time.