# Efficiency Domain Integration Pattern

Complete reference for how the efficiency research domain was added to the Temuclaude swarm on 2026-07-06. Use this as a template for adding future research domains.

## Constraint (Ggs's Rule — LOCKED)

NEVER NEVER NEVER sacrifice quality for cost cutting. Unless the risk to reward is way better (savings >50%, loss <2%). Every efficiency technique must be classified:

- **LOSSLESS** — zero quality loss, mathematically guaranteed (speculative decoding, KV cache, prefix caching, MoE, structured output)
- **QUALITY-PRESERVING** — <1% loss, >20% savings, verified (RouteLLM, semantic cache, AWQ, early exit)
- **PARETO-OPTIMAL** — savings% > loss%, savings >20%, loss <5% (ATTS, BEST-Route)
- **REJECTED** — >5% quality loss, or unverified, or no kill switch. Logged as "track for future," NOT implemented.

## 5-Gate Quality Guardrail

Enforced in `efficiency_daemon.py` via the `REJECTED_TECHNIQUES` set and in the cron job prompt:

1. **LOSSLESS GATE** — mathematically lossless? Accept without further scrutiny.
2. **PARETO GATE** — savings% > loss%, savings >20%, loss <5%? Accept.
3. **VERIFIED GATE** — peer-reviewed or production-verified? Reject marketing claims.
4. **REVERSIBLE GATE** — kill switch exists? All techniques must revert to full compute.
5. **MONITORING GATE** — pareto_tracker.py integration? Must track quality in production.

## Integration Steps (9 files modified/created)

### 1. Scout Queries (3 files)

**scripts/scout_arxiv.py** — added 19 efficiency queries to QUERIES list:
```python
# Lossless speedup
"speculative decoding lossless LLM inference speedup",
"KV cache reuse prefix caching LLM efficiency",
"continuous batching paged attention vLLM throughput",
"MoE mixture experts sparse activation efficient inference",
"structured output constrained generation LLM efficiency",
"chunked prefill LLM inference optimization",
# Quality-preserving cost reduction
"cascade routing LLM cost reduction quality preserving",
"semantic caching LLM duplicate query detection",
"model quantization AWQ lossless quality preserving",
"early exit adaptive computation LLM efficiency",
"teacher student distillation LLM cost reduction",
"prompt caching provider API efficiency",
"context compression lossless token reduction",
"adaptive token budget LLM efficiency Pareto",
# Frontier
"DFlash draft model speculative decoding training",
"model weight merging TIES task arithmetic inference",
"EAGLE Medusa speculative decoding token-level",
"DSPy MIPROv2 prompt optimization efficiency gains",
```

**scripts/scout_github.py** — added 19 efficiency queries (similar pattern).

**scripts/scout_huggingface.py** — added 28 efficiency keywords to paper filter + 6 efficiency model searches:
```python
# Keywords
"speculative decoding", "KV cache", "prefix caching", "vLLM",
"PagedAttention", "continuous batching", "MoE", "mixture of experts",
"semantic cache", "caching", "quantization", "AWQ", "GGUF",
"early exit", "adaptive computation", "cascade routing",
"cost reduction", "efficiency", "throughput", "speedup",
"lossless", "Pareto", "token reduction", "context compression",
"distillation", "model merging", "structured output",

# Model searches
("speculative decoding", 10),
("KV cache", 10),
("semantic cache", 10),
("model quantization AWQ", 10),
("efficient inference", 10),
("model merging", 10),
```

### 2. Dynamic Priorities (1 file, critical pitfall)

**scripts/dynamic_priorities.py** — added 14 techniques to `MISSING_TECHNIQUES` dict, each with a `quality_class` field:

```python
"semantic_caching": {
    "reason": "Semantic cache: 20% hit rate, 100% savings on hit. QUALITY-PRESERVING. NOT implemented.",
    "blocked_by": None,
    "research_needed": "high",
    "impact": 9,
    "quality_class": "quality_preserving",  # <-- THIS FIELD
},
```

**PITFALL (discovered 2026-07-06):** `calculate_dynamic_priorities()` does NOT automatically propagate custom fields from `MISSING_TECHNIQUES` to the returned priority dict. You MUST add the field to the dict construction in `calculate_dynamic_priorities()` (around line 454):

```python
priorities[name] = {
    "priority_score": score,
    "research_needed": info["research_needed"],
    "reason": info["reason"],
    "blocked_by": info["blocked_by"],
    "action": "research_and_implement" if info["blocked_by"] else "implement_now",
    "quality_class": info.get("quality_class", "unknown"),  # <-- MUST ADD THIS
}
```

Without this line, `quality_class` is stored in `MISSING_TECHNIQUES` but never appears in the priority output. The efficiency_daemon will log `quality: unknown` for all techniques even though they have `quality_class` set. Discovered when efficiency_daemon first cycle showed `routellm_cascade (score: 125, quality: unknown)` despite the technique having `quality_class: quality_preserving`.

Also added 6 blocked efficiency techniques to `BLOCKED_TECHNIQUES` dict (speculative_decoding, continuous_batching, awq_quantization, early_exit_adaptive, dflash_speculator_training, model_weight_merging_eff, teacher_student_distillation, efficiency_continuous_improvement).

### 3. Dedicated Daemon (1 new file)

**research/efficiency_daemon.py** — 11.5KB daemon that:
- Runs every 5 minutes (same as research daemons)
- Pulls efficiency findings from queue (identifies by 42 EFFICIENCY_KEYWORDS)
- Researches top efficiency priority from dynamic_priorities.py
- Has REJECTED_TECHNIQUES set — skips techniques that sacrifice quality
- Generates research prompts with quality guardrail notes
- Queues reports for auto-integrator via push_implementation()

Key class: `EfficiencyResearchDaemon(DaemonBase)` with:
- `EFFICIENCY_TOPICS` — 14 technique names to focus on
- `EFFICIENCY_KEYWORDS` — 42 keywords to identify efficiency findings
- `REJECTED_TECHNIQUES` — 4 technique types that sacrifice quality (extreme_quantization, aggressive_pruning, extreme_distillation, unverified_efficiency)
- `_quality_guardrail_note(quality_class)` — generates guardrail text for research prompts

### 4. Coordinator + Daemon Base (2 files)

**coordinator_daemon.py** — added to DAEMON_SCRIPTS:
```python
"efficiency_daemon": "research/efficiency_daemon.py",
```

**daemon_base.py** — added to get_all_daemon_statuses() daemons list:
```python
"efficiency_daemon",  # Added 2026-07-06
```

### 5. Start + Status Scripts (2 files)

**scripts/start_swarm.sh** — added efficiency daemon startup (daemon 7/9), updated all echo statements from /8 to /9.

**scripts/status_swarm.sh** — added "efficiency_daemon" to the hardcoded daemons array on line 21.

### 6. TRACKER.md (1 file)

Updated with full efficiency section: 14 techniques, quality guardrail, key papers, repos, quality rule.

### 7. Cron Job (1 created)

Daily at 3am IST (offset from cyber research at 2am to avoid API overlap). Loads deep-research-mode skill. Enforces quality guardrail in prompt. Rejects >5% quality loss techniques.

## Verification

After integration, verify:
```python
import sys
sys.path.insert(0, "/Users/saiful/temuclaude/research/scripts")
from dynamic_priorities import calculate_dynamic_priorities
p = calculate_dynamic_priorities()
# Check quality_class is propagated
for name in ["semantic_caching", "routellm_cascade", "speculative_decoding"]:
    print(f"{name}: quality_class = {p[name].get('quality_class', 'MISSING')}")
# Should show: quality_preserving, quality_preserving, lossless
```

```bash
# Check daemon is live
cat /tmp/temuclaude_daemons/efficiency_daemon.log
# Should show: "Top efficiency priority: routellm_cascade (score: 125, quality: quality_preserving)"

# Check status dashboard shows 9 daemons
bash /Users/saiful/temuclaude/research/scripts/status_swarm.sh
```

## Key Papers (15 verified)

| Paper | Result | Quality |
|-------|--------|---------|
| Speculative Decoding (arXiv:2401.07851) | 2-3x speedup | LOSSLESS |
| DFlash (Z Lab, Modal Jun 2026) | +5-20% over base | LOSSLESS |
| RouteLLM (arXiv:2406.18665, ICLR 2025) | 85% savings, 95% quality | PRESERVING |
| KV Cache (Raschka Jun 2025) | 90% prefix savings | LOSSLESS |
| PagedAttention/vLLM (arXiv:2309.06180) | 2-3x throughput | LOSSLESS |
| AWQ 4-bit (arXiv:2306.00978) | 4x memory, 10-20% speed | PRESERVING |
| Apple Duo-LLM (NeurIPS 2024) | 30-50% compute savings | PRESERVING |
| ATTS Framework | 28% savings, 2% loss | PARETO |
| BEST-Route (2025) | 60% savings, <1% loss | PARETO |
| Semantic Cache (Portkey) | 20% hit, 100% savings on hit | PRESERVING |
| Prompt Caching (Anthropic/OpenAI) | 90% input savings | LOSSLESS |
| ParallelVLM (CVPR 2026) | 3x video-LLM speedup | LOSSLESS |
| TIES-Merging (arXiv:2511.21437) | +1.62 mean gain | LOSSLESS |
| DSPy/MIPROv2 (ICLR 2026) | 10-50% from prompts | PRESERVING |
| Outlines (structured generation) | 100% valid output | LOSSLESS |

## Key Repos

| Repo | Why |
|------|-----|
| vllm-project/vllm | PagedAttention, continuous batching, spec decoding |
| HuangOwen/Awesome-LLM-Compression | Curated LLM compression papers |
| lm-sys/RouteLLM | Preference-data trained router (85% savings) |
| stanfordnlp/dspy | MIPROv2, GEPA prompt optimization |
| outlines-dev/outlines | Structured output, constrained generation |
| KazKozDev/dspy-optimization-patterns | Teacher-student 50x cost reduction |