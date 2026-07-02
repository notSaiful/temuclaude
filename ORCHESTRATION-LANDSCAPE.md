# LLM Orchestration — Complete Landscape Analysis

## All Known Orchestration Frameworks, Tools, and Breakthroughs (July 2026)

---

## 1. ENTERPRISE GATEWAYS (11 tools)

From AIMultiple benchmark (June 2026):

| Gateway | Key Feature | Ollama? | Relevance |
|---------|------------|---------|-----------|
| **LiteLLM** | Unified API, Adaptive Router, Python SDK | ✅ | **OUR CHOICE** — infrastructure layer |
| OpenRouter | Managed gateway, Auto/Fusion/Pareto routers | ❌ | Reference for patterns |
| Kong AI Gateway | Enterprise API, semantic security | ❌ | Enterprise only |
| Portkey AI Gateway | Multimodal routing, failover, caching | ❌ | Reference |
| TrueFoundry | Enterprise governance | ❌ | Enterprise only |
| Unify.AI | Modular LLMOps | ❌ | Reference |
| Bifrost (Maxim AI) | Ultra-high performance, MCP integration | ❌ | Open source, interesting |
| Helicone | Observability priority | ❌ | Monitoring reference |
| Cloudflare AI Gateway | Edge buffering, multi-provider failover | ❌ | Edge deployment |
| LLM Gateway | Flexible analytics, cost insights | ❌ | Reference |
| Sno.ai (llmix) | Cache, retries, circuit breakers, key rotation | ✅ | Interesting for reliability |

**Gateway benchmark results (AIMultiple):**
- Groq: Fastest FTL (0.14s long prompts)
- SambaNova: Fastest FTL short (0.13s), highest tokens (1,997)
- OpenRouter: FTL 0.40-0.45s, total 25s long
- TogetherAI: FTL 0.43-0.45s, total 11s

---

## 2. DEVELOPER FRAMEWORKS (11 frameworks)

From AIMultiple benchmark:

| Framework | Best For | Benchmark Performance |
|-----------|---------|----------------------|
| **LangGraph** | Fastest execution, efficient state management | **Fastest** in 5-agent benchmark |
| LangChain | Complex AI workflows | Consumes more tokens (heavier memory) |
| **AutoGen** (Microsoft) | Multi-agent conversation | Moderate, consistent coordination |
| **CrewAI** | Role-based agent orchestration | Longest delays (autonomous deliberation) |
| Agency Swarm | AI agent networks | Open source |
| Haystack (Deepset) | Custom NLP pipelines, semantic search | Component-based |
| IBM watsonx | Enterprise use | $500/mo+ |
| LlamaIndex | Data integration, RAG | Free tier available |
| Loft | No-code/low-code AI automation | Enterprise |
| Microchain | Lightweight AI microservices | Open source |
| Orq | Enterprise LLMOps | Free tier available |

**Key benchmark finding:** LangGraph is fastest. CrewAI is slowest (deliberation overhead). AutoGen is moderate but consistent.

---

## 3. NEW OPEN-SOURCE ORCHESTRATION PROJECTS (from GitHub)

### A. MassGen (1.1K stars) — MULTI-AGENT SCALING
**What:** Open-source multi-agent scaling system. Every agent tackles the FULL problem, observes, critiques, and builds on others' work across cycles. When agents believe there's a strong enough answer, they VOTE. Best collectively validated answer wins.

**Key innovation:** "Test-time scaling" through multi-agent consensus voting. Based on "threads of thought" and "iterative refinement" research. Presented at Berkeley Agentic AI Summit 2025.

**How it works:**
1. N agents (different models) all solve the same problem
2. Each agent sees others' work, critiques, refines
3. Multiple cycles of refinement + restarts
4. Agents VOTE when they believe convergence is reached
5. Best collectively-validated answer wins

**Available as a skill:** `npx skills add massgen/skills --all` — works in Claude Code, Cursor, Copilot, and 40+ agents.

**For Timuclaude:** This is the self-consistency + debate pattern COMBINED. Multiple models work the same problem, refine through observation, vote on best answer. We can integrate MassGen's approach into our Fusion panel — instead of just generating independently, agents see each other's work and refine.

**What we take:** The voting/convergence detection mechanism. Instead of a judge picking the best (Fusion pattern), agents VOTE when they agree. This is more democratic and catches errors better.

### B. Ouroboros (4.8K stars) — AGENT OS
**What:** Agent OS for AI coding. Specification-first workflow: interview → crystallize → execute → evaluate → evolve. Turns vague prompts into verified, working codebases.

**Key innovation:** Immutable "seed spec" that locks intent before code execution. 3-stage automated evaluation gate. Replayable, observable, policy-bound execution.

**Works with:** Claude Code, Codex CLI, OpenCode, **Hermes**, Gemini, Kiro, Copilot, Pi.

**For Timuclaude:** The specification-first approach is relevant for benchmark tasks. Instead of just sending a query to models, we:
1. Interview the query (understand what's being asked)
2. Crystallize into immutable spec (lock the task requirements)
3. Execute with models (our Fusion panel)
4. Evaluate (tool verification + verifier model)
5. Evolve (GEPA optimizes the process)

### C. 1flowbase — FUSION-STYLE MULTI-MODEL WORKFLOWS
**What:** Open-source AI gateway that publishes Fusion-style multi-model workflows as OpenAI/Claude-compatible virtual models. Full trace visibility: model calls, tool callbacks, tokens, latency, cost.

**Key innovation:** Mount a vision model as a TOOL for text models. Run Fusion-style panels. All observable with traces.

**How it works:**
```
Agent client → one virtual model endpoint → your workflow → trace/tokens/cost → final answer
```

**For Timuclaude:** This is an alternative to LiteLLM for the gateway layer. It natively supports Fusion-style workflows (panel + synthesis), observability, and mounting models as tools. Could be used alongside LiteLLM.

**What we take:** The "mount model as tool" pattern — e.g., mount a vision model as a tool for text models. Our text models (GLM-5.2, DeepSeek) can "call" a vision model (Kimi K2.6, MiniMax M3) when they need vision capability.

### D. Cliclaw — PARALLEL CODING AGENTS
**What:** Orchestrate AI coding agents (Claude Code, Codex) as parallel subagents over tmux. Loop-engineering runtime with auto-continue, execute-then-review, cross-session memory.

**For Timuclaude:** The "execute-then-review" pattern is our build-and-debug strategy. The cross-session memory is what Hermes already provides.

### E. ainativelang (AINL) — AI-NATIVE PROGRAMMING
**What:** Turns AI from "smart conversation" into "structured worker." Graph-canonical, AI-native programming system for deterministic execution. Multi-step, state, memory, tool use, repeatable execution, validation, control.

**For Timuclaude:** The deterministic execution approach is relevant for benchmarks — we need repeatable, verifiable results, not creative variation.

---

## 4. ORCHESTRATION PATTERNS — COMPLETE TAXONOMY

From all research, here is every known orchestration pattern:

### Generation Patterns:
1. **Direct** — 1 model answers (simplest)
2. **Best-of-N** — N models generate, pick best (proven +12-43%)
3. **Self-consistency** — N samples, majority vote (proven +10-20% on math)
4. **Fusion/Panel+Judge** — N models generate, judge analyzes, synthesizer writes final (OpenRouter Fusion, Perplexity Model Council)
5. **Debate** — models argue, refine, converge (Fugu, debunked as standalone but useful with voting)
6. **MassGen voting** — N agents work same problem, see each other, refine, VOTE when converged
7. **Build-and-debug** — generate, verify, fix, iterate (Fugu, Reflexion: +27% on HumanEval)
8. **Specialist routing** — classify task, route to best model (Fugu, Maestro, LiteLLM Adaptive)
9. **Cheap-first escalate** — try cheap, verify, escalate if fails (Maestro: 92% quality at 97% lower cost)
10. **MCTS + PRM** — tree search over reasoning steps with verifier (rStar-Math: 7B matched frontier)

### Verification Patterns:
11. **Tool verification** — execute code, run tests (ground truth, +10-27%)
12. **PRM step verification** — score each reasoning step (proven +10-20% on math)
13. **Cross-model verification** — model A checks model B's output (Fusion judge pattern)
14. **Web verification** — search to verify factual claims (Fusion web_search)

### Improvement Patterns:
15. **OPRO** — LLM optimizes its own prompts iteratively (Google research)
16. **GEPA** — genetic algorithm evolves prompts (Hermes Self-Evolution, ICLR 2026)
17. **Skill extraction** — save winning strategies as reusable skills (Hermes, Voyager)
18. **Adaptive Router** — bandit algorithm learns best model per task type (LiteLLM)
19. **Session search** — retrieve past successful strategies (Hermes FTS5)
20. **Memory** — store durable facts about what works (Hermes 4-layer memory)

### Architecture Patterns:
21. **Orchestrator model** — trained model coordinates others (Fugu TRINITY/Conductor)
22. **Skill-based orchestration** — Hermes uses skills, not trained weights
23. **Durable task board** — Kanban for multi-agent collaboration (Hermes Kanban)
24. **Specification-first** — interview → spec → execute → evaluate (Ouroboros)
25. **Model-as-tool** — mount vision/audio model as tool for text model (1flowbase)
26. **Parallel subagents** — delegate to isolated contexts (Hermes delegate_task)
27. **Profile-based** — each model gets own profile with config + skills + memory (Hermes)

---

## 5. WHAT TIMUCLAUDE TAKES FROM EACH

| Source | What We Take | How |
|--------|------------|-----|
| **Fugu** | TRINITY roles (Thinker/Worker/Verifier), Conductor (agentic workflows) | Hermes skill, not trained weights |
| **Maestro** | Cheap-first-verify-escalate, cost transparency, model registry JSON | LiteLLM config + cost reporting |
| **OpenRouter Fusion** | Panel + Judge + structured analysis (consensus/contradictions/insights/blind_spots) | delegate_task + Nemotron as judge |
| **Perplexity Model Council** | Convergence/divergence framing for users | Output presentation |
| **MassGen** | Multi-agent voting + convergence detection | Self-consistency with vote mechanism |
| **Ouroboros** | Spec-first (interview → crystallize → execute → evaluate) | Benchmark task preprocessing |
| **1flowbase** | Model-as-tool pattern (vision model as tool for text model) | Mount Kimi/MiniMax as vision tool |
| **LiteLLM** | Adaptive Router, unified API, fallbacks, cost tracking, proxy | Infrastructure layer |
| **LangGraph** | Fastest execution framework | If we need graph-based workflows |
| **AutoGen** | Multi-agent conversation patterns | Reference for delegate_task |
| **Hermes Agent** | Everything: skills, memory, delegation, Kanban, GEPA, cron, profiles, MCP, session search, proxy | Our entire platform |
| **rStar-Math** | MCTS + PRM for hard reasoning | Tree search implementation |
| **Reflexion** | Execute → feedback → fix → retry | Tool verification loop |
| **Voyager** | Skill library that compounds | Hermes skill system (already built) |
| **OPRO** | LLM optimizes prompts iteratively | GEPA (already built in Hermes) |

---

## 6. THE COMPLETE TIMUCLAUDE ORCHESTRATION STACK (27 PATTERNS)

No system in the world combines all 27 patterns. Timuclaude does.

**Generation (10 patterns):** Direct, Best-of-N, Self-consistency, Fusion panel, Debate, MassGen voting, Build-and-debug, Specialist routing, Cheap-first escalate, MCTS+PRM

**Verification (4 patterns):** Tool verification, PRM step verification, Cross-model verification, Web verification

**Improvement (6 patterns):** OPRO, GEPA, Skill extraction, Adaptive Router, Session search, Memory

**Architecture (7 patterns):** Orchestrator (Hermes), Skill-based, Durable Kanban, Spec-first, Model-as-tool, Parallel subagents, Profile-based

---

## 7. BENCHMARK FRAMEWORK FINDINGS

From AIMultiple's orchestration benchmark (100 runs, 5-agent workflow):

- **LangGraph:** Fastest execution, most efficient state management
- **LangChain:** More token consumption (heavier memory/history)
- **AutoGen:** Moderate, consistent coordination
- **CrewAI:** Longest delays (autonomous deliberation before tool calls)

**For Timuclaude:** We use Hermes delegate_task (not LangGraph/CrewAI/AutoGen). Hermes is already optimized for delegation with isolated contexts. We don't need a separate orchestration framework — Hermes IS the framework.

---

## 8. KEY BREAKTHROUGHS FROM THE RESEARCH

1. **MassGen's voting mechanism** is better than Fusion's judge-picks-best. When agents VOTE on convergence, they collectively validate quality. We should use this instead of a single judge.

2. **1flowbase's model-as-tool pattern** is elegant. Instead of routing to a vision model, TEXT models can CALL vision models as tools. This means GLM-5.2 can "use" Kimi K2.6's vision capability mid-generation.

3. **Ouroboros's spec-first approach** prevents architecture drift. For benchmarks, we lock the task requirements before sending to models. This prevents models from misinterpreting the task.

4. **LiteLLM's Adaptive Router** is the only built-in learning router. It tracks quality estimates per model per task type and adjusts routing automatically. This is our self-improvement layer — no need to build it.

5. **Hermes GEPA** is the only built-in prompt evolution system. It genetically optimizes prompts based on execution traces. This is our OPRO layer — no need to build it.

6. **The combination of MassGen voting + Fusion structured analysis + tool verification + GEPA evolution** is unique to Timuclaude. No competitor has all four.