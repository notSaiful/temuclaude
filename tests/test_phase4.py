"""
Temuclaude Phase 4 Test Suite
Tests: Dataset loading, judges, benchmark runner, results reporter
"""
import sys
import os
import asyncio
import json
import tempfile

import pytest

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, project_root)

from benchmarks.datasets import load_custom_json, create_sample_dataset, load_dataset_by_name
from benchmarks.judges import extract_judgment, exact_match_judge, llm_judge, JUDGE_PROMPT
from benchmarks.benchmark_runner import run_benchmark, save_results
from benchmarks.results import load_results, print_report, compare_results, compare_files
from src.orchestrator import Temuclaude

_SKIP_API = os.environ.get("SKIP_API_TESTS", "1") == "1"
skip_no_api = pytest.mark.skipif(_SKIP_API, reason="SKIP_API_TESTS=1")


# ============================================================
# TEST 1: Dataset Loading
# ============================================================
def test_dataset_loading() -> bool:
    """Test that datasets load correctly."""
    print("\n=== DATASET LOADING TESTS ===")
    
    # Sample dataset
    ds = create_sample_dataset()
    assert len(ds) == 10, f"Expected 10, got {len(ds)}"
    assert "question" in ds[0], "Missing question field"
    assert "answer" in ds[0], "Missing answer field"
    assert "category" in ds[0], "Missing category field"
    print(f"  OK: sample dataset ({len(ds)} questions)")
    
    # Custom JSON loading
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump([{"id": "1", "question": "What is 2+2?", "answer": "4", "category": "math"}], f)
        temp_path = f.name
    
    loaded = load_custom_json(temp_path)
    assert len(loaded) == 1, f"Expected 1, got {len(loaded)}"
    assert loaded[0]["answer"] == "4"
    print(f"  OK: custom JSON loaded ({len(loaded)} questions)")
    os.unlink(temp_path)
    
    # load_dataset_by_name with file path
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump([{"id": "1", "question": "Test?", "answer": "Yes", "category": "test"}], f)
        temp_path = f.name
    
    loaded = load_dataset_by_name(temp_path)
    assert len(loaded) == 1
    print(f"  OK: load_dataset_by_name with file path")
    os.unlink(temp_path)
    
    print(f"  3/3 passed")
    return True


# ============================================================
# TEST 2: Judges
# ============================================================
def test_judges() -> bool:
    """Test that judges work correctly."""
    print("\n=== JUDGE TESTS ===")
    
    # Exact match — correct
    result = exact_match_judge("The answer is 180.", "180")
    assert result["correct"] == True, f"Should be correct: {result}"
    print(f"  OK: exact match (correct) — {result['extracted_answer']}")
    
    # Exact match — wrong
    result = exact_match_judge("The answer is 200.", "180")
    assert result["correct"] == False, f"Should be incorrect: {result}"
    print(f"  OK: exact match (wrong)")
    
    # Exact match — case insensitive
    result = exact_match_judge("The answer is Paris.", "paris")
    assert result["correct"] == True, f"Should be correct (case insensitive): {result}"
    print(f"  OK: exact match (case insensitive)")
    
    # Judge prompt structure
    prompt = JUDGE_PROMPT.format(question="What is 2+2?", response="4", correct_answer="4")
    assert "2+2" in prompt, "Should contain question"
    assert "correct_answer" in prompt, "Should contain correct_answer"
    print(f"  OK: judge prompt built correctly")
    
    # Extract judgment from LLM response
    judge_response = """
extracted_final_answer: 180
reasoning: The answer 180 matches the correct answer.
correct: yes
confidence: 100
"""
    judgment = extract_judgment(judge_response)
    assert judgment["correct"] == True, f"Should be correct: {judgment}"
    assert judgment["extracted_answer"] == "180", f"Should extract 180: {judgment}"
    assert judgment["confidence"] == 100, f"Should have confidence 100: {judgment}"
    print(f"  OK: judgment extracted — correct={judgment['correct']}, answer={judgment['extracted_answer']}")
    
    # Extract judgment — incorrect
    judge_response2 = """
extracted_final_answer: 200
reasoning: The answer 200 does not match 180.
correct: no
confidence: 90
"""
    judgment2 = extract_judgment(judge_response2)
    assert judgment2["correct"] == False, f"Should be incorrect: {judgment2}"
    print(f"  OK: judgment extracted — correct={judgment2['correct']}")
    
    print(f"  6/6 passed")
    return True


# ============================================================
# TEST 3: Benchmark Runner (with exact match, small sample, live)
# ============================================================
@skip_no_api
def test_benchmark_runner_live():
    """Test that the benchmark runner works with a live model (small sample)."""
    print("\n=== BENCHMARK RUNNER LIVE TESTS ===")
    
    tc = Temuclaude()
    loop = asyncio.new_event_loop()
    
    # Use 3 sample questions (math, fast models)
    dataset = create_sample_dataset()[:3]
    
    try:
        results = loop.run_until_complete(
            asyncio.wait_for(
                run_benchmark(
                    dataset=dataset,
                    model_func=tc.call_model_with_fallback,
                    model_name="gpt-oss-120b",  # Fast model for testing
                    use_exact_match=True,
                    max_tokens=500,
                    timeout_per_question=30,
                ),
                timeout=120,
            )
        )
        
        assert results["total_questions"] == 3, f"Expected 3 questions: {results['total_questions']}"
        assert "accuracy" in results, "Missing accuracy"
        assert "by_category" in results, "Missing by_category"
        assert len(results["results"]) == 3, "Missing results list"
        
        print(f"  OK: ran {results['total_questions']} questions")
        print(f"  OK: accuracy = {results['accuracy']:.1%}")
        print(f"  OK: avg latency = {results['avg_latency_ms']}ms")
        
        passed = True
    except asyncio.TimeoutError:
        print(f"  FAIL: timed out")
        passed = False
    except Exception as e:
        print(f"  FAIL: {str(e)[:100]}")
        passed = False
    
    loop.close()
    print(f"  {'1/1' if passed else '0/1'} passed")
    return passed


# ============================================================
# TEST 4: Results Reporter
# ============================================================
def test_results_reporter() -> bool:
    """Test that the results reporter works correctly."""
    print("\n=== RESULTS REPORTER TESTS ===")
    
    # Create fake results
    fake_results = {
        "model_name": "test_model",
        "total_questions": 3,
        "correct": 2,
        "accuracy": 2/3,
        "results": [
            {"id": "1", "question": "Q1", "correct_answer": "A", "response": "A", "correct": True, "extracted_answer": "A", "category": "math", "latency_ms": 100},
            {"id": "2", "question": "Q2", "correct_answer": "B", "response": "C", "correct": False, "extracted_answer": "C", "category": "knowledge", "latency_ms": 200},
            {"id": "3", "question": "Q3", "correct_answer": "D", "response": "D", "correct": True, "extracted_answer": "D", "category": "math", "latency_ms": 150},
        ],
        "by_category": {
            "math": {"total": 2, "correct": 2, "accuracy": 1.0},
            "knowledge": {"total": 1, "correct": 0, "accuracy": 0.0},
        },
        "total_latency_ms": 450,
        "avg_latency_ms": 150,
    }
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(fake_results, f)
        temp_path = f.name
    
    # Load and print report
    loaded = load_results(temp_path)
    assert loaded["model_name"] == "test_model"
    assert loaded["accuracy"] == 2/3
    print(f"  OK: results loaded")
    
    # Print report (suppress output)
    import io
    from contextlib import redirect_stdout
    captured = io.StringIO()
    with redirect_stdout(captured):
        print_report(loaded)
    report = captured.getvalue()
    assert "BENCHMARK RESULTS" in report, "Report should have header"
    assert "test_model" in report, "Report should have model name"
    assert "66.7%" in report, "Report should have accuracy"
    print(f"  OK: report generated")
    
    # Compare two results
    fake_baseline = {**fake_results, "model_name": "baseline"}
    fake_temuclaude = {**fake_results, "model_name": "temuclaude", "correct": 3, "accuracy": 1.0}
    
    with redirect_stdout(captured):
        compare_results(fake_baseline, fake_temuclaude)
    comparison = captured.getvalue()
    assert "COMPARISON" in comparison.upper() or "Improvement" in comparison
    print(f"  OK: comparison generated")
    
    # Clean up
    os.unlink(temp_path)
    
    print(f"  3/3 passed")
    return True


# ============================================================
# TEST 5: Save and Load Results
# ============================================================
def test_save_load_results() -> bool:
    """Test that results can be saved and loaded."""
    print("\n=== SAVE/LOAD TESTS ===")
    
    fake_results = {
        "model_name": "test",
        "total_questions": 1,
        "correct": 1,
        "accuracy": 1.0,
        "results": [],
        "by_category": {},
        "total_latency_ms": 100,
        "avg_latency_ms": 100,
    }
    
    # Save
    temp_path = os.path.join(tempfile.gettempdir(), "temuclaude_test_results.json")
    save_results(fake_results, temp_path)
    assert os.path.isfile(temp_path), "File should exist after save"
    print(f"  OK: results saved")
    
    # Load
    loaded = load_results(temp_path)
    assert loaded["model_name"] == "test"
    assert loaded["accuracy"] == 1.0
    print(f"  OK: results loaded correctly")
    
    # Clean up
    os.unlink(temp_path)
    
    print(f"  1/1 passed")
    return True


# ============================================================
# RUN ALL TESTS
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("TEMUCLAUDE — PHASE 4 TEST SUITE")
    print("=" * 60)
    
    results = []
    # Non-live tests
    results.append(("Dataset Loading", test_dataset_loading()))
    results.append(("Judges", test_judges()))
    results.append(("Results Reporter", test_results_reporter()))
    results.append(("Save/Load", test_save_load_results()))
    
    # Live tests
    results.append(("Benchmark Runner Live", test_benchmark_runner_live()))
    
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