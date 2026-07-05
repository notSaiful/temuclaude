# TEMUCLAUDE EFFICIENCY BREAKTHROUGH — IMPLEMENTATION PLAN
**Created:** 2026-07-05 | **Status:** IN_PROGRESS
**Goal:** 50-95% token reduction + 4-5.5x model speedup | **Quality:** ZERO LOSS

---

## PHASE 1: HERMES AGENT EFFICIENCY (Week 1 — No Infra Change)
*Target: 50-95% token reduction, immediate quality gains*

### 1.1 Four-Layer Progressive Context Compression
**Files to modify:** `~/.hermes/profiles/default/skills/`, Hermes agent core
**Pattern from:** Claude Code reverse-engineering (500K lines TS)

| Layer | Action | Implementation |
|-------|--------|----------------|
| SNIP | Truncate large tool outputs in history | Add `max_output_tokens` per toolset, truncate with "…[truncated]" |
| MICROCOMPACT | Near-zero-cost deduplication | Hash tool outputs, replace duplicates with reference |
| COLLAPSE | Fold inactive conversation sections | Fold turns older than N with summary, reversible on demand |
| AUTOCOMPACT | Sub-agent summarizes entire conversation | Spawn subagent when context > 80% limit, replace with summary |

**Post-compression:** Auto-restore 5 most recently edited files

### 1.2 Fork Agents for Cache Sharing (95% Input Token Savings)
**Files:** `delegate_task` tool, subagent spawning logic
**Mechanism:** Ensure parallel subagents receive byte-identical prompt prefixes
- Same system prompt + context + task prefix
- Only task-specific suffix differs
- vLLM/SGLang prefix caching handles the rest

### 1.3 Speculative Tool Execution
**Files:** Tool dispatch loop in `model_tools.py` / `run_agent.py`
**Mechanism:** Start read-only tools (search, read, grep) during model streaming
- Detect read-only tools via toolset metadata
- Dispatch async during generation, collect before response completes
- Hides ~1s latency per tool call

### 1.4 MIPROv2 Prompt Optimization (DSPy)
**Files:** New skill `prompt-optimization`, DSPy integration
**Action:** Replace manual prompts with MIPROv2-optimized versions
- Joint optimization of instructions + few-shot examples
- Bayesian optimization over prompt space
- Eval on MMLU-Pro, GPQA, MATH, HumanEval

### 1.5 Seven Error Recovery "Continue Sites"
**Files:** Agent loop error handling
**Recovery paths:**
1. Context overflow → auto-compress + retry
2. Token limit hit → auto-escalate output cap 4K→64K
3. Tool timeout → retry with longer timeout
4. Model error → fallback to next model in cascade
5. Parse error → re-prompt with format correction
6. Rate limit → exponential backoff + retry
7. Unknown error → log, compress, retry once

---

## PHASE 2: HERMES SELF-EVOLUTION PIPELINE (Week 2)
*Target: Continuous auto-improvement, $2-10/run, no GPU*

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

## PHASE 3: SELF-HOSTED INFERENCE MIGRATION (Month 2)
*Target: 4-5.5x decode speedup, lossless quality*

### 3.1 Infrastructure: vLLM + SGLang Cluster
**Hardware:** H100/A100 (FP8 KV cache requires Hopper+)
**Models to deploy:** Top 3 from pool (GLM-5.2, DeepSeek V4, Kimi K2.6)
**Quantization:** AWQ 4-bit weights + FP8 KV cache

### 3.2 Speculative Decoding Stack
**Priority order (all lossless):**
1. **EAGLE-3** (vLLM native) — feature-level speculation, 3.5x
2. **DDD** (Dynamic Depth Decoding) — +44% over EAGLE-2, 3.16x avg
3. **SpecVocab** — dynamic vocab subset, +8% over EAGLE-3
4. **Hydra++** — sequentially-dependent heads, drop-in for Medusa
5. **Mamba Drafters** — cross-model, less memory

**Combined target:** EAGLE-3 + DDD + SpecVocab = **4-5.5x**

### 3.3 RadixAttention (SGLang) for Prefix Sharing
- Automatic prefix caching across requests
- 2-10x prefill speedup on shared contexts
- Critical for Hermes fork agents (95% shared prefixes)

### 3.4 Continuous Batching + Chunked Prefill
- vLLM: `enable_chunked_prefill=True`, `max_num_batched_tokens`
- SGLang: native continuous batching
- Chunked prefill for long contexts (disaggregated prefill)

### 3.5 Migration Strategy
| Stage | Action | Validation |
|-------|--------|------------|
| 1 | Deploy vLLM/SGLang with FP8 KV + AWQ 4-bit | Benchmark: MMLU-Pro, GPQA, MATH, HumanEval |
| 2 | Enable EAGLE-3 speculative decoding | Verify lossless: delta < 0.5% on all benchmarks |
| 3 | Add DDD + SpecVocab | Measure combined speedup |
| 4 | Switch Temuclaude routing to self-hosted endpoints | A/B test: cloud vs self-hosted |
| 5 | Full cutover | Monitor 24h, rollback if any regression |

---

## QUALITY VERIFICATION PROTOCOL (MANDATORY AT EACH PHASE)

```python
# Run after EVERY implementation
def verify_no_quality_loss(baseline, optimized):
    benchmarks = ["MMLU-Pro", "GPQA-Diamond", "MATH", "HumanEval", "SWE-bench", "Arena-Hard"]
    for bm in benchmarks:
        base = evaluate(baseline, bm)
        opt = evaluate(optimized, bm)
        delta = opt - base
        assert delta >= -0.005, f"REGRESSION on {bm}: {delta:.3f}"
    
    # Efficiency checks
    token_savings = measure_token_reduction(optimized)
    assert token_savings >= 0.20
    
    speedup = measure_latency_speedup(optimized)
    assert speedup >= 1.5
    
    return "PASS"
```

---

## EXECUTION ORDER (This Session)

### IMMEDIATE (Phase 1.1 - 1.5)
1. [ ] Implement 4-layer compression in Hermes agent
2. [ ] Add fork agent cache sharing to delegate_task
3. [ ] Add speculative tool execution to tool dispatcher
4. [ ] Create prompt-optimization skill with MIPROv2
5. [ ] Add 7 continue sites to agent error handling

### Phase 2.1 - 2.4
6. [ ] Clone & deploy hermes-agent-self-evolution
7. [ ] Integrate DSPy + GEPA trace reader
8. [ ] Set up teacher-student distillation pipeline
8. [ ] Create skill curator cron job

### Phase 3 (Separate session - requires GPU infra)
9. [ ] Provision vLLM/SGLang cluster
10. [ ] Deploy quantized models
11. [ ] Enable speculative decoding stack
12. [ ] Migrate Temuclaude routing

---

## SUCCESS CRITERIA

| Metric | Target | Measurement |
|--------|--------|-------------|
| Context token usage | ≤30% of baseline | `measure_token_reduction()` |
| Parallel task input tokens | ≤5% of baseline | Fork agent cache hit rate |
| Tool latency visibility | ≤100ms perceived | Speculative tool execution |
| Prompt quality (MMLU-Pro) | +10-50% | MIPROv2 eval |
| Self-evolution cycle cost | $2-10/run | Track OpenRouter spend |
| Model decode speedup | 4-5.5x | vLLM benchmarks |
| Quality regression | <0.5% on any benchmark | Verification protocol |

---

## ROLLBACK TRIGGERS
- Any benchmark regression > 0.5%
- Token savings < 20% after Phase 1
- Speedup < 1.5x after Phase 3
- Self-evolution produces failing tests

**On trigger:** Immediate rollback, root cause analysis, fix, re-verify.