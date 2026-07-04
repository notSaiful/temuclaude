# Phase 3 Plan — Self-Improvement Layer

## What We're Building

Phase 3 adds the self-improvement layer: Self-QA gate (model scores its own work), skill auto-loading (inject domain expertise), query log analysis (learn from past performance), and adaptive routing (adjust model weights based on results).

This is what makes Temuclaude get better over time — without retraining.

## Components

### 1. Self-QA Gate (src/self_qa.py)
After generating a response, a verifier model scores it 0-10. If below threshold (8), retry with feedback. Max 3 retries.

**Implementation:**
```
async def self_qa_gate(question, answer, verifier_model, call_model_func):
    # Build QA prompt: "Score this answer 0-10. Is it correct? Complete? Professional?"
    # If score >= 8: return answer (accepted)
    # If score < 8: return feedback for retry
    # Max 3 retries before accepting best attempt
```

**Integration in orchestrator:**
- After Fusion produces an answer, Self-QA gate checks it
- If score < 8, retry the entire Fusion with feedback
- Max 3 retries

### 2. Skill Auto-Loading (src/skills_loader.py)
Before answering, check task type and inject relevant skill principles into the system prompt.

**Skill mapping:**
- coding → test-driven-development, systematic-debugging
- reasoning → systematic-debugging
- creative → humanizer
- agentic → hermes-agent
- math → (no skill needed, code verification handles this)
- knowledge → (no skill needed)

**Implementation:**
```
def load_skill_principles(task_type):
    # Map task type to skill files
    # Read SKILL.md for each skill
    # Extract key principles (first 500 chars)
    # Return as string to inject into system prompt
```

**Integration in orchestrator:**
- Before calling models, inject skill principles into system prompt
- "You are Temuclaude. Domain expertise: {skill_principles}"

### 3. Query Log Analysis (src/analyzer.py)
Analyze past query logs to find patterns: which task types have lowest success, which models perform best per task.

**Implementation:**
```
def analyze_logs(log_file):
    # Read all queries from log
    # Group by task_type
    # Calculate success rate per task type
    # Calculate success rate per model per task type
    # Return report: "Math: 85% success. DeepSeek best for math at 90%."
```

**This is NOT real-time.** It's a analysis tool run periodically (or before GEPA evolution).

### 4. Adaptive Routing (src/adaptive.py)
Based on log analysis, adjust which model is used for each task type.

**Implementation:**
```
def get_adaptive_routing(analyzer_report):
    # For each task type, check which model has highest success rate
    # If a different model performs better than the default, switch
    # Return updated TASK_MODEL_MAP
```

**Integration in orchestrator:**
- On startup, load adaptive routing from last analysis
- Periodically (cron) re-analyze and update routing
- For Phase 3: manual trigger (run analyzer, then restart with updated routing)

### 5. GEPA Prompt Evolution (src/gepa.py) — SIMPLIFIED
Simplified version: analyze logs, generate prompt variations, test on sample, select best.

**Implementation:**
```
async def evolve_prompts(log_file, call_model_func):
    # 1. Analyze logs: find weakest task type
    # 2. Generate 3 prompt variations targeting that weakness
    # 3. Test each on 5 sample queries from logs
    # 4. Score each variation (Self-QA gate)
    # 5. Select best variation
    # 6. Save to config/evolved_prompts.json
```

**This is a WEEKLY cron job.** Not real-time. For Phase 3: manual trigger.

## Strategy Selection Matrix (Updated)

| Tier | Task Type | Phase 1-2 Strategy | Phase 3 Addition |
|------|-----------|-------------------|-----------------|
| trivial | any | direct cheap model | + skill principles in prompt |
| medium | any | direct specialist | + skill principles in prompt |
| hard | math | Fusion + code + self-consistency | + Self-QA gate + skill principles |
| hard | coding | Fusion + code | + Self-QA gate + TDD/debugging skills |
| hard | knowledge | Fusion | + Self-QA gate |
| hard | reasoning | Fusion + self-consistency | + Self-QA gate + debugging skills |
| hard | creative | Fusion | + Self-QA gate + humanizer skill |
| hard | agentic | Fusion | + Self-QA gate + hermes-agent skill |

## File Changes

1. NEW: src/self_qa.py — Self-QA gate
2. NEW: src/skills_loader.py — Skill auto-loading
3. NEW: src/analyzer.py — Query log analysis
4. NEW: src/adaptive.py — Adaptive routing
5. NEW: src/gepa.py — Simplified GEPA prompt evolution
6. MODIFY: src/orchestrator.py — Wire all new modules into complete()
7. NEW: tests/test_phase3.py — Phase 3 test suite
8. MODIFY: README.md — Update Phase 3 status

## What's NOT in Phase 3
- Postgres database (Phase 5 — production)
- LiteLLM Adaptive Router (needs Postgres — Phase 5)
- Real-time GEPA (Phase 5 — needs cron + production infra)
- Session search integration (Phase 5 — needs Hermes session DB)
- LiteLLM proxy database config (Phase 5 — needs Postgres)