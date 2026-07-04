# Phase 2 Plan — Core Orchestration

## What We're Building

Phase 2 adds the real power: Fusion (multiple models in parallel), self-consistency (voting), code execution verification, and dynamic aggregator selection. This is where Temuclaude goes from "smart router" to "Fable 5 killer."

## Components

### 1. Fusion Module (src/fusion.py)
- Calls N models in parallel using asyncio.gather
- Collects all responses
- Sends to a dynamic aggregator model for synthesis
- Aggregator chosen based on task type (Fugu pattern)

**Implementation:**
```
async def fuse(question, task_type, panel_models):
    # Call all models in parallel
    responses = await asyncio.gather(*[
        call_model(model, messages) for model in panel_models
    ])
    # Pick aggregator based on task type
    aggregator = AGGREGATOR_MAP[task_type]
    # Build synthesis prompt with all responses
    synthesis_prompt = build_fusion_prompt(question, responses, panel_models)
    # Aggregator synthesizes
    final = await call_model(aggregator, synthesis_prompt)
    return final
```

### 2. Self-Consistency Module (src/consistency.py)
- Runs the same model N times at temperature 0.7
- Extracts the final answer from each response
- Majority vote on extracted answers
- If no clear majority, falls back to first response

**Implementation:**
```
async def self_consistency(question, model, n=20):
    responses = await asyncio.gather(*[
        call_model(model, messages, temperature=0.7) for _ in range(n)
    ])
    answers = [extract_answer(r) for r in responses]
    voted = majority_vote(answers)
    if voted:
        return voted
    return responses[0]  # fallback

def extract_answer(response):
    # Parse "Answer: X" from the end of the response
    match = re.search(r'Answer:\s*(.+?)(?:\n|$)', response)
    if match:
        return match.group(1).strip()
    return response  # no clear answer format
```

### 3. Code Execution Verification (src/verifier.py)
- For math/coding questions, generate Python code
- Execute in sandboxed subprocess
- Capture output as verified answer
- If code fails, fall back to model's direct answer

**Implementation:**
```
async def verify_with_code(question, model):
    # Ask model to write Python code that solves the question
    code_prompt = f"Write Python code to solve this. Only output code, no explanation.\nQuestion: {question}"
    code = await call_model(model, code_prompt)
    # Extract code from markdown blocks if present
    code = extract_code(code)
    # Execute in sandbox
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, timeout=10,
        env={"PATH": os.environ.get("PATH", "")},
        cwd=temp_dir
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None  # code failed, fall back
```

### 4. Dynamic Aggregator (in src/fusion.py)
- Chooses the best model to synthesize based on task type
- Already defined in models.py AGGREGATOR_MAP
- Math → DeepSeek, Knowledge → GLM-5.2, Creative → MiniMax, etc.

### 5. Updated Orchestrator (src/orchestrator.py)
- Hard tier now uses Fusion instead of single model
- Math hard: Fusion + code verification + self-consistency
- Coding hard: Fusion + code verification
- Knowledge hard: Fusion only
- Reasoning hard: Fusion + self-consistency
- Creative hard: Fusion only

## Strategy Selection Matrix

| Tier | Task Type | Strategy |
|------|-----------|----------|
| trivial | any | direct cheap model |
| medium | any | direct specialist |
| hard | math | Fusion + code verify + self-consistency |
| hard | coding | Fusion + code verify |
| hard | knowledge | Fusion only |
| hard | reasoning | Fusion + self-consistency |
| hard | creative | Fusion only |
| hard | agentic | Fusion only |

## Test Plan

1. test_fusion: verify parallel model calls work, aggregator produces synthesis
2. test_consistency: verify N samples, voting, answer extraction
3. test_verifier: verify code generation, execution, fallback
4. test_aggregator: verify dynamic selection per task type
5. test_hard_tier: verify hard tier uses correct strategy per task type
6. test_integration: full end-to-end with hard queries

## Concurrency Note

- Ollama Pro ($20/mo): 3 concurrent models
- Ollama Max ($100/mo): 10 concurrent models
- For 5-model fusion: need Max tier
- For self-consistency with N=20: model calls are sequential per model (same model, same Ollama connection)
- But: fusion calls 5 different models in parallel (needs 5 slots)
- Solution: configurable panel size. Default to 3 on Pro, 5 on Max.

## File Changes

1. NEW: src/fusion.py — Fusion + dynamic aggregator
2. NEW: src/consistency.py — Self-consistency voting
3. NEW: src/verifier.py — Code execution verification
4. MODIFY: src/orchestrator.py — Wire hard tier to use new modules
5. MODIFY: src/models.py — Add configurable panel size
6. NEW: tests/test_fusion.py — Fusion tests
7. MODIFY: tests/test_orchestrator.py — Add hard tier tests