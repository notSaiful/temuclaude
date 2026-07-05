# TEMUCLAUDE EFFICIENCY BREAKTHROUGH — DETAILED IMPLEMENTATION PLAN
**Created:** 2026-07-05 | **Status:** PLANNING
**Goal:** 50-95% token reduction + 4-5.5x model speedup | **Quality:** ZERO LOSS
**Target:** Temuclaude (8-model orchestration) + Hermes Agent (core agent)

---

## ARCHITECTURE UNDERSTANDING (Verified from Codebase)

### Hermes Agent Core Files
| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `run_agent.py` | Main agent loop | `AIAgent`, `_dispatch_delegate_task`, `_compress_context` |
| `agent/context_compressor.py` | Context compression | `ContextCompressor` (4-layer: prune → protect head → protect tail → summarize → iterate) |
| `tools/delegate_tool.py` | Subagent spawning | `delegate_task`, `DELEGATE_BLOCKED_TOOLS`, ThreadPoolExecutor |
| `model_tools.py` | Tool registry & dispatch | `get_tool_definitions`, `handle_function_call`, async bridging |
| `agent/prompt_builder.py` | System prompt construction | Tiered prompt: stable → context → volatile |
| `agent/conversation_compression.py` | High-level compression API | `compress_context()` |
| `cli.py` | CLI entry, session management | Compression triggers, session rotation |

### Existing Compression (Already Implemented)
- **SNIP**: Tool output pruning (`_prune_old_tool_results`) — deduplicates, summarizes, truncates args
- **COLLAPSE**: Token-budget tail protection + head protection
- **AUTOCOMPACT**: LLM summarization with iterative updates (`_generate_summary`)
- **Missing**: MICROCOMPACT (deduplication across turns), speculative tool execution, fork cache sharing

### Existing Delegation (Already Implemented)
- `delegate_task` spawns isolated subagents with restricted toolsets
- Background execution via ThreadPoolExecutor
- **Missing**: Byte-identical prefix sharing for cache hits

---

## PHASE 1: HERMES AGENT EFFICIENCY (Week 1 — No Infra Change)
**Target: 50-95% token reduction, immediate quality gains**

### 1.1 Four-Layer Progressive Context Compression → UPGRADE EXISTING
**Files:** `agent/context_compressor.py`, `agent/conversation_compression.py`

| Layer | Current State | Enhancement Needed |
|-------|---------------|-------------------|
| **SNIP** | ✅ Tool output pruning, deduplication, arg truncation | Add per-toolset `max_output_tokens` config |
| **MICROCOMPACT** | ❌ Not implemented | Cross-turn deduplication via content hashing |
| **COLLAPSE** | ✅ Token-budget tail + head protection | Add reversible folding with metadata |
| **AUTOCOMPACT** | ✅ LLM summarization, iterative updates | Auto-restore 5 recent files post-compression |

**Implementation Steps:**
1. Add `MICROCOMPACT` pass in `_prune_old_tool_results` — hash all message content, replace duplicates with references
2. Add `folded_sections` tracking in `ContextCompressor` for reversible collapse
3. Add `auto_restore_recent_files()` call after compression in `conversation_compression.py`
4. Add config: `compression.max_output_tokens_per_toolset`, `compression.enable_microcompact`

### 1.2 Fork Agents for Cache Sharing (95% Input Token Savings)
**Files:** `tools/delegate_tool.py`, `run_agent.py` (`_dispatch_delegate_task`)

**Mechanism:** Ensure parallel subagents receive byte-identical prompt prefixes
- Same system prompt + context + task prefix (only task-specific suffix differs)
- vLLM/SGLang prefix caching handles the rest automatically

**Implementation Steps:**
1. In `delegate_task`, build a **shared prefix** = system prompt + context + shared instructions
2. Pass shared prefix to all subagents in batch; append task-specific goal
3. Verify identical prefix via hash logging
4. Add config: `delegation.enable_prefix_sharing` (default: true)

### 1.3 Speculative Tool Execution
**Files:** `model_tools.py` (tool dispatch), `run_agent.py` (agent loop)

**Mechanism:** Start read-only tools during model streaming
- Detect read-only tools via toolset metadata (`READONLY_TOOLSETS = {"search", "file_read", "web"}`)
- Dispatch async during generation, collect before response completes
- Hides ~1s latency per tool call

**Implementation Steps:**
1. Add `is_readonly` property to tool definitions in `tools/registry.py`
2. In `handle_function_call`, detect streaming + read-only → launch async, await before yield
3. Add streaming callback hook in `AIAgent.run_conversation()`
4. Add config: `tools.speculative_execution` (default: true)

### 1.4 MIPROv2 Prompt Optimization (DSPy)
**Files:** New skill `prompt-optimization`, integrate with DSPy

**Action:** Replace manual prompts with MIPROv2-optimized versions
- Joint optimization of instructions + few-shot examples
- Bayesian optimization over prompt space
- Eval on MMLU-Pro, GPQA, MATH, HumanEval

**Implementation Steps:**
1. Create skill `prompt-optimization` with DSPy integration
2. Add `optimize_prompt()` function using `dspy.MIPROv2`
3. Create eval datasets from Temuclaude session history
4. Add auto-optimization trigger: when prompt used >100 times with <80% success
5. Add config: `prompt_optimization.enabled`, `prompt_optimization.eval_benchmarks`

### 1.5 Seven Error Recovery "Continue Sites"
**Files:** `run_agent.py` (agent loop), `agent/error_classifier.py`

**Recovery Paths:**
1. Context overflow → auto-compress + retry
2. Token limit hit → auto-escalate output cap 4K→64K
3. Tool timeout → retry with longer timeout
4. Model error → fallback to next model in cascade
5. Parse error → re-prompt with format correction
6. Rate limit → exponential backoff + retry
7. Unknown error → log, compress, retry once

**Implementation Steps:**
1. Extend `FailoverReason` enum with new recovery types
2. Add `_recover_and_retry()` method in `AIAgent`
3. Wire into main loop exception handling
4. Add metrics tracking per recovery type

---

## PHASE 2: HERMES SELF-EVOLUTION PIPELINE (Week 2)
**Target: Continuous auto-improvement, $2-10/run, no GPU**

### 2.1 Deploy NousResearch/hermes-agent-self-evolution
**Repo:** github.com/NousResearch/hermes-agent-self-evolution

**Phases (from blueprint):**
1. Skills (done) → 2. Tool descriptions → 3. System prompts → 4. Tool code → 5. Continuous loop

### 2.2 DSPy + GEPA Integration
**Components:**
- Execution trace reader (parses tool calls, outcomes, errors)
- Failure analyzer (understands WHY things fail)
- Mutation generator (targeted prompt/skill/tool changes)
- Constraint gates: tests pass, size limits (≤15KB skills), semantic preservation

### 2.3 Teacher-Student Distillation (BetterTogether)
**Pattern:** Strongest model (GLM-5.2) optimizes prompts for weaker models
- 50x cost reduction claimed
- Strategy: "p → w" (optimize prompts first, then fine-tune weights)

### 2.4 Skill Curator Background Job
**Cron job:** Daily maintenance
- Usage tracking per skill
- Staleness detection (last used > 30 days)
- Archival of unused skills
- LLM-driven review for quality

---

## PHASE 3: SELF-HOSTED INFERENCE MIGRATION (Month 2 — Separate Session)
**Target: 4-5.5x decode speedup, lossless quality**
**Requires:** GPU infra (H100/A100), vLLM/SGLang deployment

---

## QUALITY VERIFICATION PROTOCOL (MANDATORY AT EACH PHASE)

```python
def verify_no_quality_loss(baseline, optimized):
    benchmarks = ["MMLU-Pro", "GPQA-Diamond", "MATH", "HumanEval", "SWE-bench", "Arena-Hard"]
    for bm in benchmarks:
        base = evaluate(baseline, bm)
        opt = evaluate(optimized, bm)
        delta = opt - base
        assert delta >= -0.005, f"REGRESSION on {bm}: {delta:.3f}"
    
    token_savings = measure_token_reduction(optimized)
    assert token_savings >= 0.20
    
    speedup = measure_latency_speedup(optimized)
    assert speedup >= 1.5
    
    return "PASS"
```

---

## EXECUTION ORDER (This Session — Phase 1 Only)

| # | Task | Files | Est. Time | Verification |
|---|------|-------|-----------|--------------|
| 1 | Add MICROCOMPACT pass to context compressor | `context_compressor.py` | 1 | 45 min | Token reduction test |
| 2 | Add reversible collapse tracking | `context_compressor.py` | 30 min | Fold/unfold test |
| 3 | Add auto-restore recent files | `conversation_compression.py` | 20 min | File restore test |
| 4 | Add prefix sharing to delegate_task | `delegate_tool.py` | 45 min | Cache hit rate test |
| 5 | Add speculative tool execution | `model_tools.py`, `run_agent.py` | 60 min | Latency hide test |
| 6 | Create prompt-optimization skill | New skill + DSPy | 60 min | MIPROv2 eval |
| 7 | Add 7 continue sites | `run_agent.py`, `error_classifier.py` | 45 min | Recovery simulation |
| 8 | Run full verification suite | All Phase 1 changes | 30 min | Benchmark delta < 0.5% |

**Total Phase 1 Estimate: ~4.5 hours**

---

## ROLLBACK TRIGGERS (Per Task)
- Any benchmark regression > 0.5% → immediate revert
- Token savings < 20% after task 1-3 → investigate
- Cache hit rate < 90% after task 4 → debug prefix sharing
- Speculative tool adds latency → disable per toolset

---

## SUCCESS CRITERIA (Phase 1 Complete)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Context token usage | ≤30% of baseline | `measure_token_reduction()` |
| Parallel task input tokens | ≤5% of baseline | Fork agent cache hit rate |
| Tool latency visibility | ≤100ms perceived | Speculative tool execution |
| Prompt quality (MMLU-Pro) | +10-50% | MIPROv2 eval |
| Quality regression | <0.5% on any benchmark | Verification protocol |

---

## READY TO EXECUTE?

**Order:** 1→2→3→4→5→6→7→8 (sequential, each verified before next)

**Start with:** Task 1 - MICROCOMPACT pass in `context_compressor.py`

**User approval required before each task.**