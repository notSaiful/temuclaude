# Temuclaude Research Swarm — Scout Scripts Reference

## scout_arxiv.py

**Location:** `/Users/saiful/temuclaude/research/scripts/scout_arxiv.py`

**Purpose:** Searches arXiv for papers on LLM orchestration, reasoning, multi-agent systems.

**Queries (25 diverse topics):**
- Orchestration: "LLM orchestration multi-model fusion ensemble", "model panel judge aggregator routing", "mixture of agents layered aggregation"
- Reasoning: "tree search MCTS LLM reasoning step-by-step", "process reward model PRM verification", "self-consistency chain-of-thought majority vote", "test-time compute scaling reasoning", "Tree of Thoughts Graph of Thoughts reasoning", "LLM reflection self-refine iterative improvement"
- Multi-agent: "multi-agent LLM debate consensus collaboration", "LLM swarm intelligence collective"
- Cost: "cost-efficient LLM inference routing cascade", "speculative decoding early exit LLM"
- Prompt: "automated prompt optimization OPRO evolutionary", "prompt engineering meta-prompting DSPy compiled"
- Model combo: "model merging mixture of experts inference", "ensemble LLM combination technique"
- Verification: "self-verification LLM hallucination reduction code execution", "LLM judge evaluator quality"
- Agent arch: "AI agent architecture tool-use planning ReAct", "LLM skill extraction Voyager library learning", "self-improving LLM automatic improvement meta-learning"
- New models: "open weight LLM model release benchmark evaluation"

**Output:** `research/raw/arxiv_<timestamp>.json`

**Dedup:** In-run (by arxiv_id) + cross-run (via `dedup.filter_new`)

**Rate limit:** 15s sleep between queries

## scout_github.py

**Location:** `/Users/saiful/temuclaude/research/scripts/scout_github.py`

**Purpose:** Searches GitHub for repositories on relevant topics.

**Queries:** Similar diverse coverage for repos

**Output:** `research/raw/github_<timestamp>.json`

## scout_huggingface.py

**Location:** `/Users/saiful/temuclaude/research/scripts/scout_huggingface.py`

**Purpose:** Searches HuggingFace for new models, datasets, spaces.

**Output:** `research/raw/huggingface_<timestamp>.json`

## run_all_scouts.sh

**Location:** `/Users/saiful/temuclaude/research/scripts/run_all_scouts.sh`

**Purpose:** Orchestrates all 3 scouts + distiller in sequence. Called by cron job (no_agent=true).

```bash
#!/bin/bash
cd /Users/saiful/temuclaude/research
echo "=== Running Scout-arXiv ==="
python3 scripts/scout_arxiv.py 2>&1
echo "=== Running Scout-GitHub ==="
python3 scripts/scout_github.py 2>&1
echo "=== Running Scout-HuggingFace ==="
python3 scripts/scout_huggingface.py 2>&1
echo "=== Running Distiller ==="
python3 scripts/distiller.py 2>&1
echo "=== ALL SCOUTS + DISTILLER COMPLETE ==="
```

## distiller.py

**Location:** `/Users/saiful/temuclaude/research/scripts/distiller.py`

**Purpose:** Evaluates raw findings, scores relevance, extracts actionables, writes distilled findings to `research/findings/`.

**Key features:**
- Uses weighted keywords for scoring (multi-agent=9, debate=8, consensus=8, swarm=8, etc.)
- Deduplicates across runs
- Outputs JSON + Markdown findings

## auto_integrator.py

**Location:** `/Users/saiful/temuclaude/research/scripts/auto_integrator.py`

**Purpose:** Implements high-priority findings into Temuclaude codebase. Runs daily at 1am via cron.

## dedup.py

**Location:** `/Users/saiful/temuclaude/research/scripts/dedup.py`

**Purpose:** Cross-run deduplication utility. `filter_new(findings, source, id_field)` returns only unseen items.

## dynamic_priorities.py / priorities.py

**Purpose:** Dynamic priority management for research topics.