# Deep Research Report: Prompt Optimization, Agent Architecture & AI Assistant Design

## Research Date: 2026-07-03
## Source: Research Agent 3 (deleg_0b7d4ce8)
## Status: COMPREHENSIVE

---

## 1. AUTOMATED PROMPT OPTIMIZATION

### DSPy Framework (Stanford NLP)
- Declarative framework — treats prompting as compilation, not handcrafting
- Key Optimizers:
  - MIPROv2: Joint optimization of instructions AND few-shot examples via Bayesian optimization
  - COPRO: Coordinate prompt optimization, simpler than MIPROv2
  - GEPA (ICLR 2026 Oral): Reads execution traces to understand WHY things fail, proposes targeted mutations
  - BootstrapFewShot: Generates few-shot demonstrations from successful runs
  - BetterTogether: Combines GEPA (prompt) + BootstrapFinetune (weights) → "p -> w" strategy
- 10-50% accuracy gains over manual prompts
- INTEGRATION: HIGH PRIORITY — upgrade to MIPROv2 for joint instruction+demo optimization
- Repo: github.com/stanfordnlp/dspy

### PromptAgent (maitrix-org)
- MCTS over the prompt space for expert-level prompt optimization
- INTEGRATION: MCTS-based search could complement GEPA's evolutionary approach

### Hermes Agent Self-Evolution — CRITICAL FINDING
- Nous Research's own evolutionary self-improvement system for Hermes Agent
- Uses DSPy + GEPA to automatically evolve skills, tool descriptions, system prompts, and code
- No GPU training required — all via API calls, ~$2-10 per optimization run
- 5 phases: Skills (done) → Tool descriptions → System prompts → Tool code → Continuous loop
- Guardrails: Full test suite must pass, size limits (Skills ≤15KB), semantic preservation
- Repo: github.com/NousResearch/hermes-agent-self-evolution
- INTEGRATION: THIS IS THE BLUEPRINT for timuclaude's self-improvement

### DSPy Teacher-Student Pattern
- Distill reasoning of expensive models into optimized prompts for cheap models
- Claims 50x cost reduction
- INTEGRATION: HIGHLY RELEVANT — optimize prompts for weaker models using strongest model outputs

---

## 2. AGENT ARCHITECTURE

### Mixture-of-Agents (MoA) — arXiv:2406.04692
- Layered architecture: each layer has multiple LLM agents
- Each agent takes ALL outputs from previous layer as auxiliary info
- Surpasses GPT-4 Omni on AlpacaEval 2.0, MT-Bench, FLASK
- Self-MoA: Sequential version that aggregates outputs over multiple rounds
- INTEGRATION: DIRECTLY RELEVANT — formalize how 5 models combine outputs in layers

### RAP (Reasoning via Planning)
- LLM as both world model AND reasoning agent with MCTS
- 33% relative improvement over CoT on GPT-4
- INTEGRATION: MCTS-based planning for routing decisions and task decomposition

---

## 3. HERMES AGENT ARCHITECTURE (from official docs)

### Core Architecture
- Self-improving AI agent by Nous Research
- Terminal-native autonomous coding/task agent with persistent memory
- Closed learning loop: creates skills from experience, improves them during use

### System Architecture
```
Entry Points (CLI, Gateway, ACP, Batch, API, Python Library)
    ↓
AIAgent (run_agent.py) — core conversation loop
  ├── Prompt Builder (prompt_builder.py)
  ├── Provider Resolution (runtime_provider.py) — 18+ providers
  └── Tool Dispatch (model_tools.py) — 70+ tools, 28 toolsets
    ↓
Session Storage (SQLite + FTS5) | Tool Backends (Terminal×6, Browser×5, Web×4, MCP, etc.)
```

### Key Design Patterns
| Pattern | How It Works |
|---------|-------------|
| Prompt stability | System prompt doesn't change mid-conversation (preserves prefix cache) |
| Tiered system prompt | stable → context → volatile layers |
| Context compression | Lossy summarization when context exceeds thresholds |
| Prompt caching | Anthropic cache breakpoints for prefix caching |
| Interruptible API calls | HTTP call in background thread, monitor interrupt event |
| Observable execution | Every tool call visible via callbacks |
| Platform-agnostic core | One AIAgent serves CLI, gateway, ACP, batch, API |
| Loose coupling | Optional subsystems use registry patterns |
| Profile isolation | Each profile gets own HOME, config, memory, sessions |

### Skills System (3-Level Progressive Disclosure)
- Level 0: skills_list() → [{name, description, category}] (~3k tokens)
- Level 1: skill_view(name) → Full content + metadata
- Level 2: skill_view(name, path) → Specific reference file
- Agent-created skills via /learn command
- Curator: background maintenance — usage tracking, staleness, archival

### Memory System
- MEMORY.md — Agent's personal notes (2,200 chars ~800 tokens)
- USER.md — User profile (1,375 chars ~500 tokens)
- Frozen snapshot: loaded at session start, NEVER changes mid-session
- Character limits prevent bloat — agent must consolidate to make room
- External providers: Honcho (dialectic user modeling), Mem0, etc.

### Delegation & Parallelization
- delegate_task: Spawn isolated subagents for parallel workstreams
- execute_code: Programmatic Python with RPC tool access
- Kanban: Durable SQLite-backed task board
- Persistent Goals: Standing goal → agent keeps working across turns

---

## 4. CLAUDE CODE ARCHITECTURE (reverse-engineered from 500K lines TypeScript)

### The 10 Patterns That Make Claude Code Work
1. AsyncGenerator as agent loop — yields Messages, natural backpressure
2. Speculative tool execution — start read-only tools during model streaming (hides ~1s latency)
3. Concurrent-safe batching — reads in parallel, writes serialized
4. Fork agents for cache sharing — parallel children share byte-identical prompt prefixes (95% input token savings)
5. 4-layer context compression: snip → microcompact → collapse → autocompact
6. File-based memory with LLM recall — side-query selects relevant memories
7. Two-phase skill loading — frontmatter only at startup, full content on invocation
8. Sticky latches for cache stability — beta headers never unset mid-session
9. Slot reservation — 8K default output cap, escalate to 64K on hit
10. Hook config snapshot — freeze at startup to prevent runtime injection

### 4-Level Progressive Compression Pipeline
1. Snip: Truncate large tool outputs in history
2. Microcompact: Near-zero-cost deduplication
3. Collapse: Fold inactive conversation sections (reversible)
4. Autocompact: Last resort — spawn sub-agent to summarize entire conversation
- After compression: auto-restore 5 most recently edited files

### 7 Error Recovery "Continue Sites"
- Context overflow → auto-compress + retry
- Token limit → auto-escalate 4K→64K
- 7 distinct recovery paths — users never see recoverable errors

### Multi-Agent Orchestration (3 modes)
- Sub-Agent: Main agent delegates, waits for results
- Coordinator: Pure dispatcher — can ONLY assign tasks
- Swarm: Named agents communicate peer-to-peer
- Git Worktree gives each agent independent code copy

---

## 5. SKILL EXTRACTION & LEARNING

### Voyager Pattern
- Autonomous exploration → skill library → iterative prompting
- Skills verified by execution before storage
- Enhancement: execution verification, automatic curriculum, skill composition

### Hermes Skills System
- Progressive disclosure (3-level loading)
- Agent-created skills via /learn
- Curator for background maintenance
- Skills ≤15KB size limit

### Meta-Skill (WoJiSama)
- A skill that produces skills — distills any codebase into skills
- INTEGRATION: Timuclaude could have a skill that auto-generates new skills from successful interactions

---

## 6. SELF-IMPROVING SYSTEMS

### Hermes Agent Self-Evolution (THE BLUEPRINT)
- DSPy+GEPA for evolutionary self-improvement
- Reads execution traces → understands WHY things fail → targeted mutations
- Constraint gates: tests pass, size limits, semantic preservation
- $2-10 per optimization run, no GPU

### Hermes Closed Learning Loop
1. Agent-curated memory with periodic nudges
2. Autonomous skill creation
3. Skill self-improvement during use
4. FTS5 cross-session recall with LLM summarization
5. Honcho dialectic user modeling
6. Curator background maintenance
7. Trajectory export for RL training (Atropos)

### DSPy BetterTogether
- GEPA (prompt optimization) + BootstrapFinetune (weight optimization)
- Strategy "p -> w": optimize prompts first (cheap), then fine-tune (expensive)

---

## 7. OPEN-WEIGHT MODEL LANDSCAPE

### Frontier Open-Weight Models (2025-2026)
| Model | Params | Key Strengths | License |
|-------|--------|--------------|--------|
| Llama 4 Scout | 17B (109B MoE) | Multimodal, 10M context | Llama Community |
| Llama 4 Maverick | 17B (400B MoE) | Multimodal, 128 experts | Llama Community |
| DeepSeek V3 | 671B (37B active) | Top-tier reasoning, code, math | DeepSeek License |
| DeepSeek R1 | 671B | Reasoning chains, RL-trained | MIT |
| Qwen 3 | 0.6B-235B | Full range, multilingual | Apache 2.0 |
| Qwen 2.5 Coder | 7B-32B | Code-specialized | Apache 2.0 |
| Mistral Large 2 | 123B | Strong reasoning, function calling | Mistral Research |
| Mixtral 8x22B | 141B (39B active) | MoE, efficient | Apache 2.0 |
| Gemma 3 | 1B-27B | Google open weights, multimodal | Gemma License |
| Phi-4 | 14B | Strong reasoning for size | MIT |
| Kimi K2 | 1T (32B active) | Long context, agentic | Modified MIT |
| Hermes 4 | (Nous Research) | Agent-optimized | Open |

### Best Models for Timuclaude Pool
1. DeepSeek V3/R1 — Top reasoning, MIT license
2. Llama 4 Maverick — Highest quality open MoE
3. Qwen 3 235B — Strong multilingual, Apache 2.0
4. Kimi K2 — Agentic-focused, 1T MoE
5. Mistral Large 2 — Strong function calling
6. Qwen 2.5 Coder 32B — Code-specialized
7. Phi-4 14B — Efficient, strong reasoning per parameter
8. Hermes 4 — Agent-optimized by Nous Research

---

## 8. BENCHMARK LANDSCAPE

### Key Benchmarks for Timuclaude
| Benchmark | Tests | Priority |
|-----------|-------|----------|
| MMLU-Pro | Multi-task language understanding | HIGH |
| HLE | Expert-level reasoning | HIGH |
| GDPval | Real-world task completion | HIGH |
| SciCode | Scientific coding | HIGH |
| MRCR | Long-context retrieval | MEDIUM |
| SWE-bench | GitHub issue resolution | HIGH |
| Arena-Hard | Human preference | MEDIUM |
| GPQA Diamond | Graduate-level QA | HIGH |
| MATH | Mathematical reasoning | HIGH |
| HumanEval/MBPP | Code generation | HIGH |
| BigCodeBench | Complex coding | MEDIUM |
| τ-bench | Tool-agent interaction | MEDIUM |
| AgentBench | Multi-round agent tasks | MEDIUM |
| LiveCodeBench | Live coding competition | MEDIUM |

### Benchmark Strategy
1. Use MMLU-Pro, GPQA, MATH as eval datasets for GEPA/DSPy optimization
2. SWE-bench, AgentBench for end-to-end agent evaluation
3. Track per-model performance to optimize routing decisions
4. Custom eval datasets from session history (Hermes Self-Evolution pattern)
5. DSPy's built-in evaluation framework for automated metric tracking

---

## KEY ACTIONABLE RECOMMENDATIONS FOR TIMUCLAUDE

### Tier 1 — Implement Now
1. Adopt Hermes Self-Evolution architecture (DSPy+GEPA, trace reading, constraint gates, $2-10/run)
2. Implement 4-layer progressive compression (snip → microcompact → collapse → autocompact)
3. Add speculative tool execution (start read-only tools during model streaming)
4. Upgrade to MIPROv2 (Bayesian joint instruction+demo optimization)

### Tier 2 — Implement Next
5. Fork agents for cache sharing (95% input token savings for parallel work)
6. Teacher-Student distillation (optimize prompts for weaker models using strongest model)
7. Mixture-of-Agents layered aggregation (formalize how 5 models combine in layers)
8. Skill curator (background maintenance prevents skill bloat)
9. Memory nudges (agent reminds itself to persist knowledge)

### Tier 3 — Explore
10. MCTS-based planning (RAP framework for task decomposition)
11. Continuous improvement loop (automated pipeline)
12. Trajectory export (ShareGPT format for future fine-tuning)
13. Benchmark integration (MMLU-Pro, SWE-bench, GPQA as eval datasets)
14. Honcho dialectic user modeling (deepening model of user)