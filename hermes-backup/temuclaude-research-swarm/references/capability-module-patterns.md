# Capability Module Development Patterns

Patterns learned while adding 16 Hermes capabilities to Temuclaude (2026-07-07).

## Module Architecture

Each capability module follows this structure:
- Lives in `src/<module_name>.py`
- Uses Ollama Cloud models (free, via `openai.AsyncOpenAI` pointing at `OLLAMA_API_BASE`)
- Has a companion test in `tests/test_<module_name>.py`
- All functions have async + sync variants where LLM calls are involved
- Fallback behavior when no `model_fn` is provided (template/placeholder response)
- No external dependencies beyond `aiohttp` and `openai` (already in project)

## Pattern: Bidirectional Regex for Safety Filters

When writing regex patterns to detect harmful content, the action verb can appear
BEFORE or AFTER the dangerous noun.

**Bad (only catches one direction):**
```python
r"\b(?:bomb|explosive)\b.*\b(?:make|build|construct)\b"
# Misses: "How to build a bomb" — 'build' comes before 'bomb'
```

**Good (catches both directions):**
```python
r"\b(?:bomb|explosive)\b.*\b(?:make|build|construct)\b"
r"\b(?:make|build|construct)\b.*\b(?:bomb|explosive)\b"
```

This was discovered when `check_weapons("How to build a pipe bomb at home")` passed
when it should have been flagged. The pattern only matched `bomb...build` but the
text had `build...bomb`. Fix: add both directions for each pattern pair.

## Pattern: Dynamic Env Var Reading for Testability

**Bad (breaks tests — env var read at import time):**
```python
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

def get_headers():
    if GITHUB_TOKEN:  # Stale value from import time
        ...
```

Setting `os.environ["GITHUB_TOKEN"]` in a test has no effect because the module
already captured the value at import.

**Good (reads at call time):**
```python
def _get_token() -> str:
    return os.environ.get("GITHUB_TOKEN", "")

def get_headers():
    token = _get_token()  # Fresh read every call
    if token:
        ...
```

## Pattern: urlparse Return Type Gotcha

`urlparse(url).netloc` returns a string, not a bool. In Python, non-empty strings
are truthy, but the function return type annotation said `-> bool`. Without an
explicit `bool()` cast, the function returns a string, and `assert result == True`
fails because `"example.com" != True`.

**Fix:** Always wrap in `bool()`:
```python
return bool(parsed.scheme in ("http", "https") and parsed.netloc)
```

## Pattern: Case Sensitivity in Word Replacement Tests

When testing `simplify_wordy()` which replaces "In order to" → "to", the result
may capitalize differently ("To run" vs "to run"). Use `.lower()` in assertions:
```python
assert "run" in result.lower()  # Not: assert "to run" in result
```

## Pattern: Test File Structure

Each test file follows:
```python
import sys
sys.path.insert(0, "/Users/saiful/temuclaude")
from src.<module> import <functions>

def test_<thing>():
    ...
```

The `sys.path.insert` is needed because tests run from the project root but
modules use relative imports (`from .models import ...`).

## Verification Command

To run all 16 new module tests at once:
```bash
cd /Users/saiful/temuclaude && python3 -m pytest \
  tests/test_sequential_thinking.py tests/test_vision.py \
  tests/test_web_search.py tests/test_citation.py \
  tests/test_safety.py tests/test_evenhandedness.py \
  tests/test_copyright_check.py tests/test_memory.py \
  tests/test_code_executor.py tests/test_tone.py \
  tests/test_time_utils.py tests/test_deep_research.py \
  tests/test_team_reasoning.py tests/test_prompt_engine.py \
  tests/test_browser.py tests/test_github_integration.py \
  tests/test_hermes_capabilities.py -v --tb=short
```

Expected: 167 passed, 0 failed (~3.5s execution time).

## Full Module List (as of 2026-07-07)

Original modules: orchestrator, models, fusion, consistency, verifier, self_qa,
adaptive, gepa, tot, debate, cache, logger, guard, honeypot, counter_attack,
security_pipeline, output_firewall, taint_tracker, pareto_tracker, preference_router,
context_compression, self_moa, shepherding, skill_curator, skills_loader,
unified_routing, analyzer, ui_ux/*, media/*

New capability modules (16):
1. sequential_thinking — step-by-step reasoning with revision/backtracking
2. vision — multimodal image analysis via Kimi K2.6
3. web_search — DuckDuckGo search, search-first policy
4. citation — inline/footnote citation system
5. safety — 5-layer safety filters (child, mental health, weapons, code, people)
6. evenhandedness — controversial topic detection and steel-manning
7. copyright_check — quote limits, lyric/poem detection
8. memory — SQLite persistent cross-query memory
9. code_executor — sandboxed Python execution
10. tone — filler removal, prose-first, conciseness
11. time_utils — IANA timezone conversion
12. deep_research — 10k+ word multi-pass research reports
13. team_reasoning — multi-agent team (Leader/Researcher/Analyst/Critic)
14. prompt_engine — prompt optimization, few-shot, CoT, A/B testing
15. browser — web page fetch and HTML parsing
16. github_integration — GitHub REST API (repos, code, issues)