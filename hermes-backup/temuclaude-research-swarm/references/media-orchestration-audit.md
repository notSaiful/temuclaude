# Media Orchestration Audit Methodology

## When to Use

After building or modifying any media orchestration component (image, video, TTS, music),
run this audit to verify completeness before declaring the build done.

## Audit Script Template

```python
import sys, ast, re, os
from pathlib import Path

media_dir = Path("src/media")

# 1. FILE EXISTENCE — check all expected files exist
# 2. STUB/TODO CHECK — parse AST, find empty functions, TODOs, NotImplementedErrors
# 3. IMPORT CHECK — verify all modules import without errors
# 4. PIPELINE STAGES — grep for each of the 10 stages in the orchestrator
# 5. PROVIDER API CALLS — check for aiohttp/session.post/session.get/endpoint URLs
# 6. JUDGE SCORING — check all scoring dimensions exist, weighted consensus, JSON+regex parsing
# 7. MODEL POOLS — check pool sizes, routing functions work
# 8. INTENT CLASSIFICATION — test all task type classifications
# 9. PACKAGE EXPORTS — check __init__.py exports all components
# 10. FUNCTIONAL TEST — run the orchestrator with mock LLM, test all tiers + cache
```

## Key Checks

### Empty Function Detection (false positive avoidance)
AST-based empty function detection will flag one-liner getters like `return MUSIC_JUDGE_POOL`
as "empty" because they only contain a Return statement. These are NOT stubs. To avoid
false positives, only flag functions that have ZERO non-docstring, non-pass, non-return
statements AND have a body size of 0 after removing docstrings.

### Pipeline Stage Verification
The 10-stage pipeline should have these grep-able patterns in the orchestrator file:
1. Cache: `get_generation_result` + `set_generation_result`
2. Intent: `classify_*_task`
3. Tier: `determine_*_tier`
4. Prompt enhancement: `enhanced_prompt` or `call_llm_func` with prompt rewriting
5. Parallel generation: `asyncio.gather`
6. Judge consensus: `judge_all` or `judge_output`
7. Quality gate: `evaluate_and_refine` or `quality_gate`
8. Post-processing: `post_processor` (may be placeholder — same as TTS)
9. Memory bank: `record_generation`
10. Return: `return result` with full metadata dict

### Component Parity Check
Compare the new orchestrator against the reference implementation (TTS for music).
Both should have: Generator class, Judge class, QualityGate class, Orchestrator class,
judge prompt builder, score calculator, score parser, judge_all method, quality gate
run method, get_threshold, get_stats.

### Provider API Call Verification
Check for real HTTP calls (not just data definitions):
- `aiohttp` or `httpx` import
- `session.post` (submit pattern)
- `session.get` (poll pattern for async APIs)
- API endpoint URL defined as a constant
- `generation_id` handling for async submit→poll APIs

### Cache Key Consistency
The cache `get` and `set` calls must use the SAME parameters for the hash key. If `get`
is called before intent classification (task_type unknown) but `set` is called after
(task_type known), the keys won't match and cache will never hit. Solution: classify
intent BEFORE checking cache, so both get and set use the classified task_type.

## Music Orchestration Build (2026-07-06)

Built `music_orchestrator.py` (687 lines), `music_provider.py` (269 lines) to complete
the 4th media orchestration. Pattern: same as TTS orchestrator but with async submit→poll
for the AIML API music endpoint (`POST /v2/generate/audio` → `GET /v2/generate/audio/{id}`).

Music models: minimax/music-2.0 ($0.0315/gen, cheapest), minimax/music-1.5 ($0.15),
minimax/music-2.6 ($0.20, frontier), minimax/music-cover ($0.195, remix), elevenlabs/eleven_music
($0.20). 3 tiers: draft (1 model), standard (2 models), premium (3 models). 6 unique task
pools: song_cover, ethnic_instruments, longest_duration, highest_quality,
custom_lyrics_structure, eleven_quality.

Judge dimensions: musicality (0.30), prompt_adherence (0.25), vocal_quality (0.15),
audio_quality (0.20), structure (0.10). 3-judge consensus with weighted scoring.

All 4 media orchestrations now complete: Image (generator.py + models.py), Video (same
pipeline via models.py), TTS (tts_orchestrator.py), Music (music_orchestrator.py).
Total media module: 6,595 + 1,380 = ~8,000 lines.