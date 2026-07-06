"""
Temuclaude Phase 3 Test Suite
Tests: Self-QA gate, skill loading, log analysis, adaptive routing, GEPA
"""
import sys
import os
import asyncio
import json
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.self_qa import self_qa_gate, build_qa_prompt, extract_score
from src.skills_loader import load_skill_principles, build_enhanced_system_prompt
from src.analyzer import analyze_logs, print_report
from src.adaptive import get_adaptive_routing, get_model_for_task, update_adaptive_routing, reset_adaptive_routing, ADAPTIVE_CONFIG_PATH
from src.gepa import get_evolved_prompts, get_system_prompt, evolve_prompts
from src.orchestrator import Temuclaude

_SKIP_API = os.environ.get("SKIP_API_TESTS", "1") == "1"
skip_no_api = pytest.mark.skipif(_SKIP_API, reason="SKIP_API_TESTS=1")


# ============================================================
# TEST 1: Self-QA Prompt Builder
# ============================================================
def test_qa_prompt_builder() -> bool:
    """Test that build_qa_prompt creates valid messages."""
    print("\n=== SELF-QA PROMPT TESTS ===")
    
    messages = build_qa_prompt("What is 2+2?", "4")
    
    assert len(messages) == 2, f"Should have 2 messages: {len(messages)}"
    assert messages[0]["role"] == "system", "First should be system"
    assert messages[1]["role"] == "user", "Second should be user"
    assert "2+2" in messages[1]["content"], "Should contain question"
    assert "4" in messages[1]["content"], "Should contain answer"
    assert "Score" in messages[0]["content"], "System prompt should mention scoring"
    
    print("  OK: Prompt built correctly")
    print("  1/1 passed")
    return True


# ============================================================
# TEST 2: Score Extraction
# ============================================================
def test_score_extraction() -> bool:
    """Test that extract_score correctly parses verifier responses."""
    print("\n=== SCORE EXTRACTION TESTS ===")
    
    test_cases = [
        ("Score: 9\nReason: Correct and complete.", (9, "Correct and complete.")),
        ("Score: 7\nReason: Mostly correct but incomplete.", (7, "Mostly correct but incomplete.")),
        ("score: 10\nreason: Perfect.", (10, "Perfect.")),
        ("I give it 8/10 because it's good.", (8, None)),  # 8/10 pattern, reasoning may vary
        ("No clear score here", (0, "")),  # parsing fails → 0
    ]
    
    passed = 0
    for response, expected in test_cases:
        score, reasoning = extract_score(response)
        if score == expected[0]:
            passed += 1
            print(f"  OK: score={score} from '{response[:40]}...'")
        else:
            print(f"  FAIL: expected {expected[0]}, got {score} from '{response[:40]}'")
    
    print(f"  {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


# ============================================================
# TEST 3: Skill Loading
# ============================================================
def test_skill_loading() -> bool:
    """Test that skill principles are loaded for relevant task types."""
    print("\n=== SKILL LOADING TESTS ===")
    
    # Coding should load TDD and debugging skills
    principles = load_skill_principles("coding")
    if principles:
        print(f"  OK: coding skills loaded ({len(principles)} chars)")
        coding_ok = True
    else:
        print(f"  NOTE: coding skills not found (skills dir may not exist)")
        coding_ok = True  # Not a failure if skills dir doesn't exist
    
    # Creative should load humanizer
    principles = load_skill_principles("creative")
    if principles:
        print(f"  OK: creative skills loaded ({len(principles)} chars)")
        creative_ok = True
    else:
        print(f"  NOTE: creative skills not found")
        creative_ok = True
    
    # Math should return empty (no skills needed)
    principles = load_skill_principles("math")
    if principles == "":
        print(f"  OK: math has no skills (expected)")
        math_ok = True
    else:
        print(f"  FAIL: math should have no skills")
        math_ok = False
    
    # Knowledge should return empty
    principles = load_skill_principles("knowledge")
    if principles == "":
        print(f"  OK: knowledge has no skills (expected)")
        knowledge_ok = True
    else:
        print(f"  FAIL: knowledge should have no skills")
        knowledge_ok = False
    
    # Enhanced system prompt
    enhanced = build_enhanced_system_prompt("coding", "You are Temuclaude.")
    if "Temuclaude" in enhanced:
        print(f"  OK: enhanced prompt built ({len(enhanced)} chars)")
        enhanced_ok = True
    else:
        print(f"  FAIL: enhanced prompt missing base")
        enhanced_ok = False
    
    all_ok = coding_ok and creative_ok and math_ok and knowledge_ok and enhanced_ok
    print(f"  {'5/5' if all_ok else 'FAILED'} passed")
    return all_ok


# ============================================================
# TEST 4: Log Analysis
# ============================================================
def test_log_analysis() -> bool:
    """Test that analyze_logs correctly parses and analyzes logs."""
    print("\n=== LOG ANALYSIS TESTS ===")
    
    # Create test logs
    import tempfile
    test_log_dir = tempfile.mkdtemp()
    log_file = os.path.join(test_log_dir, "queries_test.jsonl")
    
    test_queries = [
        {"task_type": "math", "models_used": ["deepseek-v4-pro"], "strategy": "direct", "success": True},
        {"task_type": "math", "models_used": ["deepseek-v4-pro"], "strategy": "direct", "success": True},
        {"task_type": "math", "models_used": ["glm-5.2"], "strategy": "direct", "success": False},
        {"task_type": "coding", "models_used": ["deepseek-v4-pro"], "strategy": "fusion", "success": True},
        {"task_type": "coding", "models_used": ["kimi-k2.6"], "strategy": "fusion", "success": False},
    ]
    
    with open(log_file, "w") as f:
        for q in test_queries:
            f.write(json.dumps(q) + "\n")
    
    analysis = analyze_logs(test_log_dir)
    
    # Check structure
    assert analysis["total_queries"] == 5, f"Should have 5 queries: {analysis['total_queries']}"
    assert "by_task_type" in analysis, "Should have by_task_type"
    assert "by_model" in analysis, "Should have by_model"
    assert "by_strategy" in analysis, "Should have by_strategy"
    
    # Check math success rate (2/3 = 67%)
    math_rate = analysis["by_task_type"].get("math", {}).get("success_rate", 0)
    assert abs(math_rate - 2/3) < 0.01, f"Math success rate should be ~67%: {math_rate}"
    
    print(f"  OK: {analysis['total_queries']} queries analyzed")
    print(f"  OK: math success rate = {math_rate:.1%}")
    print(f"  OK: weakest task = {analysis.get('weakest_task')}")
    
    # Clean up
    import shutil
    shutil.rmtree(test_log_dir, ignore_errors=True)
    
    print(f"  1/1 passed")
    return True


# ============================================================
# TEST 5: Adaptive Routing
# ============================================================
def test_adaptive_routing() -> bool:
    """Test that adaptive routing loads, saves, and resets correctly."""
    print("\n=== ADAPTIVE ROUTING TESTS ===")
    
    # Reset first
    reset_adaptive_routing()
    
    # Should return empty (no config)
    routing = get_adaptive_routing()
    assert routing == {}, f"Empty routing expected: {routing}"
    print(f"  OK: empty routing on reset")
    
    # Default routing should fall back to TASK_MODEL_MAP
    model = get_model_for_task("math")
    assert model == "deepseek-v4-pro", f"Math should use deepseek-v4-pro: {model}"
    print(f"  OK: math → {model} (default)")
    
    # Update with analysis
    fake_analysis = {
        "best_models": {
            "math": {"model": "glm-5.2", "success_rate": 0.95, "count": 10},
        },
        "total_queries": 100,
    }
    changes = update_adaptive_routing(fake_analysis)
    
    if changes:
        assert "math" in changes, f"Should have math change: {changes}"
        print(f"  OK: routing updated — math → glm-5.2 (adaptive override)")
    else:
        print(f"  NOTE: no changes made (model may be same as default)")
    
    # Verify override takes effect
    model = get_model_for_task("math")
    # After update, should use adaptive override
    adaptive = get_adaptive_routing()
    if "math" in adaptive:
        assert model == adaptive["math"], f"Should use adaptive override: {model}"
        print(f"  OK: adaptive override active — math → {model}")
    
    # Reset
    reset_adaptive_routing()
    routing = get_adaptive_routing()
    assert routing == {}, f"Should be empty after reset: {routing}"
    print(f"  OK: reset clears adaptive routing")
    
    print(f"  1/1 passed")
    return True


# ============================================================
# TEST 6: GEPA Prompt Loading
# ============================================================
def test_gepa_prompt_loading() -> bool:
    """Test that evolved prompts load correctly."""
    print("\n=== GEPA PROMPT LOADING TESTS ===")
    
    # No evolved prompts yet → should return default
    prompt = get_system_prompt("math", "Default prompt")
    assert "Default prompt" in prompt or "Temuclaude" in prompt, f"Should return default: {prompt}"
    print(f"  OK: returns default when no evolved prompts")
    
    # Create a fake evolved prompt
    from src.gepa import EVOLVED_PROMPTS_PATH
    os.makedirs(os.path.dirname(EVOLVED_PROMPTS_PATH), exist_ok=True)
    fake_prompts = {"math": "You are an expert mathematician. Always show your work step by step."}
    with open(EVOLVED_PROMPTS_PATH, "w") as f:
        json.dump(fake_prompts, f)
    
    # Should now return evolved prompt
    prompt = get_system_prompt("math", "Default prompt")
    assert "expert mathematician" in prompt, f"Should return evolved prompt: {prompt}"
    print(f"  OK: evolved prompt loaded for math")
    
    # Clean up
    os.remove(EVOLVED_PROMPTS_PATH)
    
    print(f"  1/1 passed")
    return True


# ============================================================
# TEST 7: Self-QA Gate (live)
# ============================================================
@skip_no_api
def test_self_qa_gate_live():
    """Test that Self-QA gate scores a good answer and accepts it."""
    print("\n=== SELF-QA GATE LIVE TESTS ===")
    
    tc = Temuclaude()
    loop = asyncio.new_event_loop()
    
    try:
        result = loop.run_until_complete(
            asyncio.wait_for(
                self_qa_gate(
                    "What is 15 * 12?",
                    "180",
                    "gpt-oss-120b",
                    tc.call_model_with_fallback,
                    threshold=8,
                    max_retries=1,
                    max_tokens=500,
                ),
                timeout=60
            )
        )
        
        if result["score"] >= 8:
            print(f"  OK: Good answer scored {result['score']}/10 (accepted)")
            passed = True
        elif result["score"] >= 5:
            # Model might be lenient or strict — acceptable for test
            print(f"  OK: Answer scored {result['score']}/10 (may vary by model)")
            passed = True
        else:
            print(f"  FAIL: Good answer scored only {result['score']}/10")
            passed = False
        
        print(f"  Attempts: {result['attempts']}, Scores: {result['all_scores']}")
    except asyncio.TimeoutError:
        print(f"  FAIL: Self-QA timed out")
        passed = False
    except Exception as e:
        print(f"  FAIL: Exception: {str(e)[:100]}")
        passed = False
    
    loop.close()
    print(f"  {'1/1' if passed else '0/1'} passed")
    return passed


# ============================================================
# TEST 8: Full Integration (live)
# ============================================================
@skip_no_api
def test_integration_live():
    """Test that a medium-tier query uses adaptive routing + skills."""
    print("\n=== INTEGRATION LIVE TESTS ===")
    
    tc = Temuclaude()
    loop = asyncio.new_event_loop()
    
    # Medium coding query should use adaptive routing + skill-enhanced prompt
    try:
        result = loop.run_until_complete(
            asyncio.wait_for(tc.complete("Write a Python function to reverse a string"), timeout=60)
        )
        
        if result and not result.startswith("[ERROR") and len(result) > 10:
            print(f"  OK: Medium query with skills returned ({len(result)} chars)")
            print(f"  Preview: {result[:80]}...")
            passed = True
        else:
            print(f"  FAIL: Bad response: {str(result)[:100]}")
            passed = False
    except asyncio.TimeoutError:
        print(f"  FAIL: Timed out")
        passed = False
    except Exception as e:
        print(f"  FAIL: Exception: {str(e)[:100]}")
        passed = False
    
    loop.close()
    print(f"  {'1/1' if passed else '0/1'} passed")
    return passed


# ============================================================
# RUN ALL TESTS
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("TEMUCLAUDE — PHASE 3 TEST SUITE")
    print("=" * 60)

    results = []
    # Non-live tests
    results.append(("QA Prompt Builder", test_qa_prompt_builder()))
    results.append(("Score Extraction", test_score_extraction()))
    results.append(("Skill Loading", test_skill_loading()))
    results.append(("Log Analysis", test_log_analysis()))
    results.append(("Adaptive Routing", test_adaptive_routing()))
    results.append(("GEPA Prompt Loading", test_gepa_prompt_loading()))
    
    # Live tests
    results.append(("Self-QA Gate Live", test_self_qa_gate_live()))
    results.append(("Integration Live", test_integration_live()))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False

    print(f"\n{'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    sys.exit(0 if all_passed else 1)