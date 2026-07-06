"""
Temuclaude Phase 2 Test Suite
Tests: Fusion, Self-Consistency, Code Verification, Dynamic Aggregator, Hard Tier
"""
import sys
import os
import asyncio
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.orchestrator import Temuclaude
from src.fusion import fuse, get_panel, get_aggregator, build_fusion_prompt
from src.consistency import self_consistency, extract_answer, majority_vote
from src.verifier import verify_with_code, extract_code
from src.models import FUSION_PANEL, AGGREGATOR_MAP

_SKIP_API = os.environ.get("SKIP_API_TESTS", "1") == "1"
skip_no_api = pytest.mark.skipif(_SKIP_API, reason="SKIP_API_TESTS=1")


# ============================================================
# TEST 1: Panel Selection
# ============================================================
def test_panel_selection() -> bool:
    """Test that get_panel returns the right models for each task type."""
    print("\n=== PANEL SELECTION TESTS ===")
    
    # Test that math prioritizes DeepSeek
    panel = get_panel("math", 3)
    assert "deepseek-v4-pro" in panel, f"Math panel should include deepseek-v4-pro: {panel}"
    assert panel[0] == "deepseek-v4-pro", f"Math panel should start with deepseek-v4-pro: {panel}"
    print(f"  OK: math panel = {panel}")
    
    # Test that knowledge prioritizes GLM-5.2
    panel = get_panel("knowledge", 3)
    assert "glm-5.2" in panel, f"Knowledge panel should include glm-5.2: {panel}"
    assert panel[0] == "glm-5.2", f"Knowledge panel should start with glm-5.2: {panel}"
    print(f"  OK: knowledge panel = {panel}")
    
    # Test that creative prioritizes MiniMax
    panel = get_panel("creative", 3)
    assert "minimax-m3" in panel, f"Creative panel should include minimax-m3: {panel}"
    assert panel[0] == "minimax-m3", f"Creative panel should start with minimax-m3: {panel}"
    print(f"  OK: creative panel = {panel}")
    
    # Test panel size limit
    panel = get_panel("math", 2)
    assert len(panel) == 2, f"Panel size should be 2: {len(panel)}"
    print(f"  OK: panel size 2 = {panel}")
    
    # Test default (unknown task type)
    panel = get_panel("unknown_type", 3)
    assert len(panel) == 3, f"Default panel should have 3 models: {len(panel)}"
    print(f"  OK: default panel = {panel}")
    
    print(f"  5/5 passed")
    return True


# ============================================================
# TEST 2: Dynamic Aggregator Selection
# ============================================================
def test_aggregator_selection() -> bool:
    """Test that get_aggregator returns the right model per task type (Fugu pattern)."""
    print("\n=== AGGREGATOR SELECTION TESTS ===")
    
    test_cases = [
        ("math", "deepseek-v4-pro"),
        ("coding", "deepseek-v4-pro"),
        ("knowledge", "glm-5.2"),
        ("reasoning", "deepseek-v4-pro"),
        ("creative", "minimax-m3"),
        ("agentic", "glm-5.2"),
        ("unknown_type", "glm-5.2"),  # default
    ]
    
    passed = 0
    for task_type, expected in test_cases:
        result = get_aggregator(task_type)
        if result == expected:
            passed += 1
            print(f"  OK: {task_type:15} → {result}")
        else:
            print(f"  FAIL: {task_type:15} → expected {expected}, got {result}")
    
    print(f"  {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


# ============================================================
# TEST 3: Answer Extraction (for self-consistency)
# ============================================================
def test_answer_extraction() -> bool:
    """Test that extract_answer correctly parses model responses."""
    print("\n=== ANSWER EXTRACTION TESTS ===")
    
    test_cases = [
        ("The answer is 42.\nAnswer: 42", "42"),
        ("Some reasoning.\nAnswer: Paris", "Paris"),
        ("Calculation done.\nThe answer is 100", "100"),
        ("25 multiplied by 4 equals 100", "100"),
        ("Just a plain response with no answer marker", "Just a plain response with no answer marker"),
    ]
    
    passed = 0
    for response, expected in test_cases:
        result = extract_answer(response)
        if result == expected:
            passed += 1
            print(f"  OK: '{response[:40]}...' → '{result}'")
        else:
            print(f"  FAIL: '{response[:40]}...' → expected '{expected}', got '{result}'")
    
    print(f"  {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


# ============================================================
# TEST 4: Majority Vote
# ============================================================
def test_majority_vote() -> bool:
    """Test that majority_vote correctly picks the most common answer."""
    print("\n=== MAJORITY VOTE TESTS ===")
    
    test_cases = [
        (["42", "42", "42", "100", "42"], "42"),  # clear majority
        (["Paris", "London", "Paris", "Berlin", "Paris"], "Paris"),  # clear majority
        (["100", "200", "300"], "100"),  # no clear majority → first
        (["42", "42", "100", "100"], "42"),  # tie → first of the tied
    ]
    
    passed = 0
    for answers, expected in test_cases:
        result = majority_vote(answers)
        if result == expected:
            passed += 1
            print(f"  OK: {answers} → '{result}'")
        else:
            print(f"  FAIL: {answers} → expected '{expected}', got '{result}'")
    
    print(f"  {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


# ============================================================
# TEST 5: Code Extraction
# ============================================================
def test_code_extraction() -> bool:
    """Test that extract_code correctly parses model responses."""
    print("\n=== CODE EXTRACTION TESTS ===")
    
    test_cases = [
        ("```python\nprint(42)\n```", "print(42)"),
        ("```\nprint('hello')\n```", "print('hello')"),
        ("Here is the code:\n```python\nx = 10\nprint(x)\n```", "x = 10\nprint(x)"),
        ("print('raw code')", "print('raw code')"),
    ]
    
    passed = 0
    for response, expected in test_cases:
        result = extract_code(response)
        if result.strip() == expected.strip():
            passed += 1
            print(f"  OK: extracted from '{response[:30]}...'")
        else:
            print(f"  FAIL: expected '{expected}', got '{result}'")
    
    print(f"  {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


# ============================================================
# TEST 6: Fusion Prompt Builder
# ============================================================
def test_fusion_prompt() -> bool:
    """Test that build_fusion_prompt creates a valid prompt."""
    print("\n=== FUSION PROMPT TESTS ===")
    
    question = "What is 15 * 12?"
    responses = {
        "glm-5.2": "180",
        "deepseek-v4-pro": "180",
    }
    panel = ["glm-5.2", "deepseek-v4-pro"]
    
    messages = build_fusion_prompt(question, responses, panel)
    
    # Check structure
    assert len(messages) == 2, f"Should have 2 messages: {len(messages)}"
    assert messages[0]["role"] == "system", f"First message should be system: {messages[0]['role']}"
    assert messages[1]["role"] == "user", f"Second message should be user: {messages[1]['role']}"
    
    # Check content includes the question and responses
    user_content = messages[1]["content"]
    assert "15 * 12" in user_content, "Prompt should contain the question"
    assert "180" in user_content, "Prompt should contain model responses"
    assert "Model A" in user_content or "Model B" in user_content, "Prompt should label models"
    
    print(f"  OK: Prompt built correctly with question and {len(panel)} responses")
    print(f"  1/1 passed")
    return True


# ============================================================
# TEST 7: Code Verification (live)
# ============================================================
@skip_no_api
def test_code_verification():
    """Test that verify_with_code generates and executes code."""
    print("\n=== CODE VERIFICATION TESTS ===")
    
    tc = Temuclaude()
    loop = asyncio.new_event_loop()
    
    try:
        result = loop.run_until_complete(
            asyncio.wait_for(
                verify_with_code("What is 15 * 12?", "gpt-oss-120b", tc.call_model_with_fallback, max_tokens=2000),
                timeout=60
            )
        )
        
        if result["verified"] and result["answer"]:
            if "180" in result["answer"]:
                print(f"  OK: Code verified — answer = {result['answer'][:50]}")
                passed = True
            else:
                print(f"  FAIL: Code ran but wrong answer: {result['answer'][:50]}")
                passed = False
        else:
            print(f"  FAIL: Code execution failed: {result.get('stderr', 'unknown')[:100]}")
            # Code verification failing is acceptable if Ollama is slow
            # But let's report it honestly
            passed = False
    except asyncio.TimeoutError:
        print(f"  FAIL: Code verification timed out")
        passed = False
    except Exception as e:
        print(f"  FAIL: Exception: {str(e)[:100]}")
        passed = False
    
    loop.close()
    print(f"  {'1/1' if passed else '0/1'} passed")
    return passed


# ============================================================
# TEST 8: Fusion (live)
# ============================================================
@skip_no_api
def test_fusion_live():
    """Test that Fusion actually calls multiple models and synthesizes."""
    print("\n=== FUSION LIVE TESTS ===")
    
    tc = Temuclaude()
    loop = asyncio.new_event_loop()
    
    try:
        result = loop.run_until_complete(
            asyncio.wait_for(
                fuse("What is 25 * 4?", "math", tc.call_model_with_fallback, panel_size=3, max_tokens=2000),
                timeout=120
            )
        )
        
        # Check we got a response
        if result["answer"] and not result["answer"].startswith("[ERROR"):
            if "100" in result["answer"]:
                print(f"  OK: Fusion answer = {result['answer'][:60]}")
                print(f"  OK: Aggregator = {result['aggregator']}")
                print(f"  OK: Panel = {result['panel']}")
                passed = True
            else:
                print(f"  FAIL: Wrong answer: {result['answer'][:60]}")
                passed = False
        else:
            print(f"  FAIL: No valid answer: {str(result['answer'])[:100]}")
            passed = False
    except asyncio.TimeoutError:
        print(f"  FAIL: Fusion timed out (models slow)")
        passed = False
    except Exception as e:
        print(f"  FAIL: Exception: {str(e)[:100]}")
        passed = False
    
    loop.close()
    print(f"  {'1/1' if passed else '0/1'} passed")
    return passed


# ============================================================
# TEST 9: Hard Tier Integration (live)
# ============================================================
@skip_no_api
def test_hard_tier():
    """Test that the hard tier uses Fusion for complex queries."""
    print("\n=== HARD TIER TESTS ===")
    
    tc = Temuclaude()
    loop = asyncio.new_event_loop()
    
    # Use a hard math question (over 30 words for math = hard tier)
    question = (
        "Calculate the derivative of f(x) = 3x^4 - 2x^3 + 5x^2 - 7x + 1 "
        "and evaluate it at x = 2. Show your work and give the final numerical answer."
    )
    
    try:
        result = loop.run_until_complete(
            asyncio.wait_for(tc.complete(question), timeout=180)
        )
        
        if result and not result.startswith("[ERROR"):
            print(f"  OK: Hard tier returned answer ({len(result)} chars)")
            print(f"  Answer preview: {result[:80]}...")
            passed = True
        else:
            print(f"  FAIL: Error response: {str(result)[:100]}")
            passed = False
    except asyncio.TimeoutError:
        print(f"  FAIL: Hard tier timed out (models slow — acceptable)")
        # Timeout is acceptable for hard tier with Fusion (many model calls)
        # But we should report it honestly
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
    print("TEMUCLAUDE — PHASE 2 TEST SUITE")
    print("=" * 60)

    results = []
    # Non-live tests (fast, no model calls)
    results.append(("Panel Selection", test_panel_selection()))
    results.append(("Aggregator Selection", test_aggregator_selection()))
    results.append(("Answer Extraction", test_answer_extraction()))
    results.append(("Majority Vote", test_majority_vote()))
    results.append(("Code Extraction", test_code_extraction()))
    results.append(("Fusion Prompt", test_fusion_prompt()))
    
    # Live tests (slow, call real models)
    results.append(("Code Verification", test_code_verification()))
    results.append(("Fusion Live", test_fusion_live()))
    results.append(("Hard Tier", test_hard_tier()))

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