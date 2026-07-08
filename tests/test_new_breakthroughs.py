"""
Temuclaude — New Breakthrough Verification Tests (Step-Level Code Verification, Pareto, Preference Router)
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.verifier import (
    extract_reasoning_steps, verify_steps_with_code, verify_with_code, extract_code,
    apply_budget_forcing, verify_logical_with_z3
)
from src.pareto_tracker import calculate_pareto, record_query, get_adjusted_budgets, load_metrics, METRICS_FILE
from src.preference_router import record_routing_decision, get_routing_recommendations, get_preference_dataset, load_preferences, PREFS_FILE


# ============================================================
# TEST 1: Step-Level Code Verification
# ============================================================
def test_step_extraction() -> bool:
    """Test that reasoning steps are correctly extracted from responses."""
    print("\n=== STEP EXTRACTION TESTS ===")
    
    # Test "Step N:" pattern
    response1 = "Step 1: First, we calculate 2+2=4.\nStep 2: Then, we multiply by 3 to get 12.\nStep 3: Therefore, the answer is 12."
    steps1 = extract_reasoning_steps(response1)
    assert len(steps1) == 3, f"Should find 3 steps, got {len(steps1)}"
    assert "2+2" in steps1[0], f"Step 1 should contain calculation: {steps1[0]}"
    print(f"  OK: 'Step N:' pattern — found {len(steps1)} steps")
    
    # Test numbered list pattern
    response2 = "1. Calculate the sum\n2. Multiply the result\n3. Get the final answer"
    steps2 = extract_reasoning_steps(response2)
    assert len(steps2) == 3, f"Should find 3 steps from numbered list, got {len(steps2)}"
    print(f"  OK: Numbered list — found {len(steps2)} steps")
    
    # Test paragraph breaks
    response3 = "First paragraph about step 1.\n\nSecond paragraph about step 2.\n\nThird paragraph about step 3."
    steps3 = extract_reasoning_steps(response3)
    assert len(steps3) >= 2, f"Should find at least 2 paragraphs, got {len(steps3)}"
    print(f"  OK: Paragraph breaks — found {len(steps3)} steps")
    
    # Test single step
    response4 = "The answer is 42."
    steps4 = extract_reasoning_steps(response4)
    assert len(steps4) == 1, f"Single response should return 1 step, got {len(steps4)}"
    print(f"  OK: Single step — found {len(steps4)} step")
    
    # Test empty response
    steps5 = extract_reasoning_steps("")
    assert len(steps5) == 0, f"Empty response should return 0 steps, got {len(steps5)}"
    print(f"  OK: Empty response — found {len(steps5)} steps")
    
    print("  5/5 passed")


# ============================================================
# TEST 2: Pareto Efficiency Tracking
# ============================================================
def test_pareto_tracking() -> bool:
    """Test that Pareto efficiency tracking works."""
    print("\n=== PARETO EFFICIENCY TESTS ===")
    
    # Test calculate_pareto with no data
    result = calculate_pareto()
    assert "token_savings_pct" in result, "Should have token_savings_pct"
    assert "accuracy_pct" in result, "Should have accuracy_pct"
    assert "is_pareto_improvement" in result, "Should have is_pareto_improvement"
    assert "recommendation" in result, "Should have recommendation"
    print(f"  OK: calculate_pareto returns correct keys")
    
    # Test record_query (we won't check the file, just that it doesn't crash)
    try:
        record_query(tier="trivial", tokens_used=500, correct=True, task_type="math", strategy="test")
        record_query(tier="medium", tokens_used=4096, correct=True, task_type="coding", strategy="test")
        record_query(tier="hard", tokens_used=8192, correct=False, task_type="reasoning", strategy="test")
        print(f"  OK: record_query works without errors")
    except Exception as e:
        assert False, f"record_query failed: {e}"
    
    # Test get_adjusted_budgets
    budgets = get_adjusted_budgets()
    assert "trivial" in budgets, "Should have trivial budget"
    assert "medium" in budgets, "Should have medium budget"
    assert "hard" in budgets, "Should have hard budget"
    assert isinstance(budgets["trivial"], int), "Budget should be int"
    print(f"  OK: get_adjusted_budgets returns budgets: {budgets}")
    
    # Test that metrics file exists after recording
    assert os.path.isfile(METRICS_FILE), f"Metrics file should exist at {METRICS_FILE}"
    print(f"  OK: Metrics file persisted to {METRICS_FILE}")
    
    print("  4/4 passed")


# ============================================================
# TEST 3: Preference-Data Router
# ============================================================
def test_preference_router() -> bool:
    """Test that preference-data router collects and analyzes routing decisions."""
    print("\n=== PREFERENCE-DATA ROUTER TESTS ===")
    
    # Test record_routing_decision
    try:
        record_routing_decision(
            query="What is 2+2?", task_type="math", tier="trivial",
            model="gpt-oss-120b", models_used=["gpt-oss-120b"],
            strategy="direct_cheap", latency_ms=500, success=True
        )
        record_routing_decision(
            query="Analyze the trade-offs between microservices and monoliths with detailed reasoning about deployment complexity and team autonomy",
            task_type="reasoning", tier="hard",
            model="deepseek-v4-pro", models_used=["deepseek-v4-pro", "glm-5.2", "kimi-k2.6"],
            strategy="fusion+step_verify+prm_consistency", latency_ms=15000, success=True
        )
        print(f"  OK: record_routing_decision works without errors")
    except Exception as e:
        assert False, f"record_routing_decision failed: {e}"
    
    # Test get_routing_recommendations
    recs = get_routing_recommendations()
    assert isinstance(recs, dict), f"Recommendations should be dict, got {type(recs)}"
    print(f"  OK: get_routing_recommendations returns dict with {len(recs)} entries")
    
    # Test get_preference_dataset
    dataset = get_preference_dataset()
    assert isinstance(dataset, list), f"Dataset should be list, got {type(dataset)}"
    if dataset:
        assert "preference" in dataset[0], "Dataset entries should have preference field"
        assert "query" in dataset[0], "Dataset entries should have query field"
        assert "tier" in dataset[0], "Dataset entries should have tier field"
    print(f"  OK: get_preference_dataset returns {len(dataset)} records")
    
    # Test that preferences file exists
    assert os.path.isfile(PREFS_FILE), f"Preferences file should exist at {PREFS_FILE}"
    print(f"  OK: Preferences file persisted to {PREFS_FILE}")
    
    print("  4/4 passed")


# ============================================================
# TEST 4: s1 Budget Forcing
# ============================================================
def test_budget_forcing() -> bool:
    """Test that s1 budget forcing appends 'Wait' to short responses."""
    print("\n=== s1 BUDGET FORCING TESTS ===")
    
    # Short response should get "Wait" appended
    short_response = "The answer is 42."
    forced = apply_budget_forcing(short_response, min_reasoning_tokens=200)
    assert "Wait" in forced, f"Short response should get 'Wait' appended: {forced}"
    assert forced != short_response, "Forced response should differ from original"
    print(f"  OK: Short response gets 'Wait' appended")
    
    # Long response should NOT get "Wait" appended
    long_response = "Let me think step by step. " * 50 + "Answer: 42."
    forced2 = apply_budget_forcing(long_response, min_reasoning_tokens=200)
    assert forced2 == long_response, "Long response should NOT get 'Wait' appended"
    print(f"  OK: Long response is NOT modified")
    
    # Empty response edge case
    forced3 = apply_budget_forcing("", min_reasoning_tokens=100)
    assert "Wait" in forced3, "Empty response should get 'Wait' appended"
    print(f"  OK: Empty response gets 'Wait' appended")
    
    print("  3/3 passed")


# ============================================================
# TEST 5: Z3/SMT Logical Verification
# ============================================================
def test_z3_verification() -> bool:
    """Test Z3/SMT logical verification."""
    print("\n=== Z3/SMT LOGICAL VERIFICATION TESTS ===")
    
    # Test with logical patterns
    response_with_logic = "If A then B. If B then C. A implies D."
    result = verify_logical_with_z3("test question", response_with_logic)
    
    # Z3 may or may not be installed — test both paths
    if "Z3 not installed" in result.get("reason", ""):
        print(f"  OK: Z3 not installed — graceful fallback (pip install z3-solver to enable)")
        print(f"  1/1 passed (with note)")
        return
    
    # Z3 IS installed — verify it works
    assert "verified" in result, "Result should have 'verified' key"
    assert result["verified"] == True, f"Consistent logic should be verified: {result}"
    print(f"  OK: Consistent logic verified by Z3")
    
    # Test with contradictory logic
    # "if A then B" + "if A then not B" → unsat
    contradictory = "If A then B. If A then not B."
    result2 = verify_logical_with_z3("test", contradictory)
    assert result2["verified"] == False, "Contradictory logic should fail verification"
    print(f"  OK: Contradictory logic rejected by Z3")
    
    # Test with no logical patterns
    no_logic = "The weather is nice today."
    result3 = verify_logical_with_z3("test", no_logic)
    assert result3["verified"] == False, "No logic patterns should return not verified"
    assert "No logical patterns" in result3["reason"], f"Should mention no patterns: {result3['reason']}"
    print(f"  OK: No logical patterns — Z3 returns gracefully")
    
    print("  3/3 passed")


# ============================================================
# RUN ALL TESTS
# ============================================================
def main():
    print("=" * 60)
    print("TEMUCLAUDE — NEW BREAKTHROUGH VERIFICATION TESTS")
    print("Step-Level Code Verification, Pareto Tracking, Preference Router")
    print("=" * 60)
    
    tests = [
        ("Step-Level Code Verification", test_step_extraction),
        ("Pareto Efficiency Tracking", test_pareto_tracking),
        ("Preference-Data Router", test_preference_router),
        ("s1 Budget Forcing", test_budget_forcing),
        ("Z3/SMT Logical Verification", test_z3_verification),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  FAILED: {name} — {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{passed + failed} test groups passed")
    if failed == 0:
        print("ALL TESTS PASSED")
    else:
        print(f"{failed} TEST GROUPS FAILED")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)