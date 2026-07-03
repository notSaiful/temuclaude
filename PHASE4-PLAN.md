# Phase 4 Plan — Benchmark Testing Framework

## What We're Building

A universal benchmark framework that can run Timuclaude against ANY question/answer dataset. This lets us:
- Test on HLE (when HF token available)
- Test on MRCR v2
- Test on custom benchmarks
- Compare baseline (single model) vs full Timuclaude
- Produce reproducible results

## Components

### 1. datasets.py — Dataset Loaders
- Load HLE from HuggingFace (needs HF_TOKEN env var)
- Load MRCR v2 from HuggingFace
- Load custom JSON datasets (format: [{question, answer}, ...])
- Stream large datasets (don't load all into memory)
- Filter: text-only, multimodal, by category

### 2. judges.py — LLM-as-Judge Scoring
- Extract final answer from model response (reuse consistency.extract_answer)
- Compare to ground truth using LLM judge (like HLE's approach)
- Judge prompt: "Is [response] correct based on [correct_answer]? yes/no"
- Also support exact-match scoring for simple answers
- Return: {correct: bool, extracted_answer: str, reasoning: str}

### 3. benchmark_runner.py — Universal Runner
- Takes: dataset, model_func, judge_func, config
- Runs each question through model_func
- Scores each response with judge_func
- Tracks: accuracy, latency, cost, per-category breakdown
- Saves results to JSON
- Supports: sample size, timeout, parallel execution

### 4. results.py — Results Reporter
- Load results JSON
- Print human-readable report
- Compare two runs (baseline vs Timuclaude)
- Per-category breakdown
- Export CSV for external analysis

### 5. run_baseline.py — Baseline Runner
- Run a single model (e.g., GLM-5.2) on a benchmark
- Uses direct model calls (no Fusion)
- Records results

### 6. run_timuclaude.py — Full Timuclaude Runner
- Run full Timuclaude (with Fusion, self-consistency, code verify, Self-QA)
- Uses orchestrator.complete()
- Records results

### 7. tests/test_phase4.py — Framework Tests
- Test dataset loading (custom JSON)
- Test judge (exact match + LLM judge)
- Test benchmark runner (with small sample)
- Test results reporter
- Test comparison

## Dataset Format (Universal)

```json
[
  {"id": "1", "question": "What is 15*12?", "answer": "180", "category": "math"},
  {"id": "2", "question": "Who wrote Hamlet?", "answer": "William Shakespeare", "category": "knowledge"}
]
```

## Usage

```bash
# Run baseline (GLM-5.2 alone) on custom benchmark
python benchmarks/run_baseline.py --model glm-5.2 --dataset benchmarks/data/sample.json --sample 10

# Run full Timuclaude on same benchmark
python benchmarks/run_timuclaude.py --dataset benchmarks/data/sample.json --sample 10

# Compare results
python benchmarks/results.py --compare baseline_results.json timuclaude_results.json
```

## HLE Integration (when HF_TOKEN available)

```bash
export HF_TOKEN=your-token
python benchmarks/run_timuclaude.py --dataset hle --sample 50 --text-only
```

## What's NOT in Phase 4
- Full 2500-question HLE eval (too expensive/time-consuming for development)
- GDPval eval (needs file handling — Phase 5)
- Official submission to ArtificialAnalysis.ai (Phase 6)
- Postgres-backed result storage (Phase 5)