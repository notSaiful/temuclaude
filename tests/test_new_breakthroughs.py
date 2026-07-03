"""
Timuclaude — New Breakthrough Verification Tests (Step-Level Code Verification, Pareto, Preference Router)
"""
import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.verifier import extract_reasoning_steps, verify_steps_with_code, verify_with_code, extract_code
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
    return True


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
    return True


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
    return True


# ============================================================
# RUN ALL TESTS
# ============================================================
def main():
    print("=" * 60)
    print("TIMUCLAUDE — NEW BREAKTHROUGH VERIFICATION TESTS")
    print("Step-Level Code Verification, Pareto Tracking, Preference Router")
    print("=" * 60)
    
    tests = [
        ("Step-Level Code Verification", test_step_extraction),
        ("Pareto Efficiency Tracking", test_pareto_tracking),
        ("Preference-Data Router", test_preference_router),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"  FAILED: {name}")
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