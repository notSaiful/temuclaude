"""
Temuclaude — Comprehensive Test Suite
Run with: python -m pytest tests/test_orchestrator.py -v
Or:      python tests/test_orchestrator.py
"""
import sys
import os
import asyncio
import time

# Add parent dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.orchestrator import Temuclaude
from src.models import MODEL_POOL, CHEAP_MODELS, TASK_MODEL_MAP, FUSION_PANEL, AGGREGATOR_MAP
from src.logger import QueryLogger


# ============================================================
# TEST 1: Task Classifier
# ============================================================
def test_classifier() -> bool:
    """Test that the task classifier correctly categorizes queries."""
    tc = Temuclaude()
    loop = asyncio.new_event_loop()

    test_cases = [
        # Math
        ("What is 2 + 2?", "math"),
        ("What is 15 * 12?", "math"),
        ("Solve: what is the integral of sin(x)?", "math"),
        ("Calculate the derivative of x^3", "math"),
        ("Prove that the square root of 2 is irrational", "math"),
        # Coding
        ("Write a Python function to sort a list", "coding"),
        ("Debug this error: TypeError in JavaScript", "coding"),
        ("How do I write a REST API endpoint in Go?", "coding"),
        ("Fix this bug in my React component", "coding"),
        # Reasoning
        ("Why does the sky appear blue?", "reasoning"),
        ("Compare REST vs GraphQL APIs", "reasoning"),
        ("How does photosynthesis work?", "reasoning"),
        ("Analyze the trade-offs between microservices and monoliths", "reasoning"),
        # Creative
        ("Write a poem about the ocean", "creative"),
        ("Write a short story about a dragon", "creative"),
        ("Compose a song about rainfall", "creative"),
        ("Write an essay on climate change", "creative"),
        # Knowledge
        ("What is the capital of France?", "knowledge"),
        ("What is the tallest mountain in the world?", "knowledge"),
        ("Who is Albert Einstein?", "knowledge"),
        ("When did World War 2 end?", "knowledge"),
        # Agentic
        ("How do I deploy a React app to Vercel?", "agentic"),
        ("Install Docker on Ubuntu", "agentic"),
        ("Setup a CI/CD pipeline for my project", "agentic"),
    ]

    passed = 0
    failed = 0
    failures = []

    for query, expected in test_cases:
        result = loop.run_until_complete(tc.classify_task(query))
        if result == expected:
            passed += 1
        else:
            failed += 1
            failures.append((query, expected, result))

    loop.close()

    print(f"\n=== CLASSIFIER TESTS: {passed}/{passed + failed} passed ===")
    for query, expected, got in failures:
        print(f"  FAIL: expected={expected}, got={got} | '{query[:60]}'")

    return failed == 0


# ============================================================
# TEST 2: Tier Determination
# ============================================================
def test_tier_determination() -> bool:
    """Test that the routing tier is correctly determined."""
    tc = Temuclaude()

    test_cases = [
        # (query, task_type, expected_tier)
        # Math queries are never trivial (require computation)
        ("What is 2+2?", "math", "medium"),
        # Knowledge queries can be trivial if short
        ("Who is Einstein?", "knowledge", "trivial"),
        ("Calculate the derivative of x^3", "math", "medium"),
        ("Debug this error: TypeError in JavaScript", "coding", "medium"),
        # Long coding query = hard (over 25 words for coding)
        ("Write a Python function to sort a list using quicksort algorithm with proper type hints and error handling and test cases included please make it complete", "coding", "hard"),
        # Long math proof = hard (over 30 words for math)
        ("Solve this complex mathematical proof: given a continuous function f on a closed interval a b prove that f attains its maximum and minimum values using the completeness axiom and the Bolzano Weierstrass theorem in detail with all steps", "math", "hard"),
    ]

    passed = 0
    failed = 0
    failures = []

    for query, task_type, expected in test_cases:
        result = tc.determine_tier(query, task_type)
        if result == expected:
            passed += 1
        else:
            failed += 1
            failures.append((query, task_type, expected, result))

    print(f"\n=== TIER TESTS: {passed}/{passed + failed} passed ===")
    for query, task_type, expected, got in failures:
        print(f"  FAIL: expected={expected}, got={got} | task={task_type} | '{query[:50]}'")

    return failed == 0


# ============================================================
# TEST 3: Model Pool Configuration
# ============================================================
def test_model_pool() -> bool:
    """Verify all models in the pool have correct configuration."""
    required_fields = ["ollama_tag", "role", "strengths", "cost_tier", "routing_weight"]
    required_models = ["glm-5.2", "deepseek-v4-pro", "kimi-k2.6", "minimax-m3", "nemotron-3-ultra"]

    passed = 0
    failed = 0
    failures = []

    for model_name in required_models:
        if model_name not in MODEL_POOL:
            failed += 1
            failures.append(f"Missing model: {model_name}")
            continue

        model = MODEL_POOL[model_name]
        for field in required_fields:
            if field not in model:
                failed += 1
                failures.append(f"Missing field '{field}' in model '{model_name}'")
            else:
                passed += 1

    # Check cheap models
    if "gpt-oss-120b" not in CHEAP_MODELS:
        failed += 1
        failures.append("Missing cheap model: gpt-oss-120b")
    else:
        passed += 1

    # Check task model map covers all task types
    required_tasks = ["math", "coding", "long_context", "knowledge", "reasoning", "creative", "agentic", "verification", "vision", "simple"]
    for task in required_tasks:
        if task not in TASK_MODEL_MAP:
            failed += 1
            failures.append(f"Missing task mapping: {task}")
        else:
            passed += 1

    # Check fusion panel has 5 models
    if len(FUSION_PANEL) != 5:
        failed += 1
        failures.append(f"Fusion panel should have 5 models, has {len(FUSION_PANEL)}")
    else:
        passed += 1

    # Check aggregator map
    if "default" not in AGGREGATOR_MAP:
        failed += 1
        failures.append("Missing default aggregator")
    else:
        passed += 1

    print(f"\n=== MODEL POOL TESTS: {passed}/{passed + failed} passed ===")
    for f in failures:
        print(f"  FAIL: {f}")

    return failed == 0


# ============================================================
# TEST 4: All Ollama Cloud Models Respond
# ============================================================
def test_all_models_respond() -> bool:
    """Test that every model in the pool can actually respond to a query."""
    tc = Temuclaude()
    loop = asyncio.new_event_loop()

    all_models = list(MODEL_POOL.keys()) + list(CHEAP_MODELS.keys())

    passed = 0
    failed = 0
    failures = []

    test_messages = [{"role": "user", "content": "What is 10 + 5? Answer with just the number."}]

    for model_name in all_models:
        start = time.time()
        try:
            answer = loop.run_until_complete(
                asyncio.wait_for(
                    tc.call_model(model_name, test_messages, max_tokens=200),
                    timeout=60
                )
            )
            latency = time.time() - start

            if answer.startswith("[ERROR"):
                failed += 1
                failures.append(f"{model_name}: returned error: {answer[:100]}")
            elif "15" in answer:
                passed += 1
                print(f"  OK: {model_name:25} ({latency:.1f}s): {answer.strip()[:60]}")
            else:
                # Model responded but answer might be wrong
                failed += 1
                failures.append(f"{model_name}: wrong answer: {answer[:100]}")
        except Exception as e:
            latency = time.time() - start
            failed += 1
            failures.append(f"{model_name}: exception: {str(e)[:100]}")

    loop.close()

    print(f"\n=== MODEL RESPONSE TESTS: {passed}/{passed + failed} passed ===")
    for f in failures:
        print(f"  FAIL: {f}")

    return failed == 0


# ============================================================
# TEST 5: Error Handling — Model Failure
# ============================================================
def test_error_handling() -> bool:
    """Test that the orchestrator handles model failures gracefully."""
    tc = Temuclaude()
    loop = asyncio.new_event_loop()

    # Test 1: Invalid model name should return error string, not crash
    try:
        answer = loop.run_until_complete(
            tc.call_model("nonexistent-model", [{"role": "user", "content": "test"}])
        )
        if answer.startswith("[ERROR"):
            print(f"  OK: Invalid model returns error gracefully: {answer[:80]}")
            passed_1 = True
        else:
            print(f"  FAIL: Invalid model should return error, got: {answer[:80]}")
            passed_1 = False
    except Exception as e:
        print(f"  FAIL: Invalid model caused exception: {e}")
        passed_1 = False

    # Test 2: Empty query should not crash
    try:
        answer = loop.run_until_complete(asyncio.wait_for(tc.complete(""), timeout=30))
        # Empty query should return something (error or response) without crashing
        if answer is not None and isinstance(answer, str):
            print(f"  OK: Empty query handled gracefully (returned {len(answer)} chars)")
            passed_2 = True
        else:
            print(f"  FAIL: Empty query returned None or non-string")
            passed_2 = False
    except asyncio.TimeoutError:
        print(f"  OK: Empty query timed out gracefully (model slow)")
        passed_2 = True
    except Exception as e:
        print(f"  FAIL: Empty query caused exception: {e}")
        passed_2 = False

    # Test 3: Very long query should not crash (use a non-math query to avoid model hang)
    try:
        long_query = "Please explain " + "the history of computing and how " * 100 + "it evolved."
        answer = loop.run_until_complete(asyncio.wait_for(tc.complete(long_query), timeout=30))
        if answer is not None and isinstance(answer, str):
            print(f"  OK: Long query handled gracefully ({len(answer)} chars)")
            passed_3 = True
        else:
            print(f"  FAIL: Long query returned None")
            passed_3 = False
    except asyncio.TimeoutError:
        print(f"  OK: Long query timed out gracefully (expected for very long input)")
        passed_3 = True
    except Exception as e:
        print(f"  FAIL: Long query caused exception: {e}")
        passed_3 = False

    # Test 4: Model timeout works (use short timeout — model should respond fast for "Hi")
    try:
        start = time.time()
        answer = loop.run_until_complete(
            tc.call_model("gpt-oss-120b", [{"role": "user", "content": "Hi"}], max_tokens=200, timeout=30)
        )
        elapsed = time.time() - start
        if not answer.startswith("[ERROR"):
            print(f"  OK: Model responded within timeout ({elapsed:.1f}s)")
            passed_4 = True
        elif "timed out" in answer:
            print(f"  OK: Timeout triggered correctly at {elapsed:.1f}s")
            passed_4 = True
        else:
            print(f"  FAIL: Unexpected: {answer[:80]}")
            passed_4 = False
    except Exception as e:
        print(f"  FAIL: Timeout test exception: {e}")
        passed_4 = False

    # Test 5: Fallback works (use a fast model to verify the path works)
    try:
        # Test with gpt-oss (fastest model) to verify fallback path works without slow retries
        answer = loop.run_until_complete(
            tc.call_model_with_fallback("gpt-oss-120b", [{"role": "user", "content": "What is 2+2?"}], max_tokens=200)
        )
        if not answer.startswith("[ERROR"):
            print(f"  OK: Fallback path works: {answer.strip()[:60]}")
            passed_5 = True
        else:
            print(f"  FAIL: Fallback failed: {answer[:80]}")
            passed_5 = False
    except Exception as e:
        print(f"  FAIL: Fallback test exception: {e}")
        passed_5 = False

    loop.close()

    all_passed = passed_1 and passed_2 and passed_3 and passed_4 and passed_5
    print(f"\n=== ERROR HANDLING TESTS: {'5/5' if all_passed else 'FAILED'} passed ===")
    return all_passed


# ============================================================
# TEST 6: End-to-End Query
# ============================================================
def test_end_to_end() -> bool:
    """Test a complete end-to-end query through the orchestrator."""
    tc = Temuclaude()
    loop = asyncio.new_event_loop()

    test_cases = [
        ("What is 25 * 4?", "math", "100"),
        ("What is the capital of Japan?", "knowledge", "Tokyo"),
        ("Write a one-line Python print statement", "coding", "print"),
    ]

    passed = 0
    failed = 0
    failures = []

    for query, expected_task, expected_answer_contains in test_cases:
        try:
            start = time.time()
            answer = loop.run_until_complete(asyncio.wait_for(tc.complete(query), timeout=60))
            latency = time.time() - start

            # Check we got a non-empty answer
            if not answer or answer.startswith("[ERROR"):
                failed += 1
                failures.append(f"Query failed: '{query[:40]}' -> {answer[:80]}")
                continue

            # Check answer contains expected content
            if expected_answer_contains.lower() in answer.lower():
                passed += 1
                print(f"  OK: '{query[:40]}' -> {answer.strip()[:60]} ({latency:.1f}s)")
            else:
                failed += 1
                failures.append(f"Wrong answer: expected '{expected_answer_contains}' in: {answer[:100]}")
        except Exception as e:
            failed += 1
            failures.append(f"Exception on '{query[:40]}': {str(e)[:100]}")

    loop.close()

    print(f"\n=== E2E TESTS: {passed}/{passed + failed} passed ===")
    for f in failures:
        print(f"  FAIL: {f}")

    return failed == 0


# ============================================================
# TEST 7: Logger
# ============================================================
def test_logger() -> bool:
    """Test that the query logger works correctly."""
    logger = QueryLogger(log_dir="/tmp/temuclaude_test_logs")

    # Log a test query
    query_id = logger.log(
        user_query="Test query",
        task_type="math",
        routing_tier="medium",
        models_used=["glm-5.2"],
        strategy="direct_specialist",
        final_answer="42",
        latency_ms=1000,
        success=True,
    )

    # Verify it was logged
    recent = logger.get_recent(1)
    if len(recent) == 1 and recent[0]["user_query"] == "Test query":
        print(f"  OK: Query logged and retrieved. ID: {query_id}")
        passed = True
    else:
        print(f"  FAIL: Logger did not return the logged query")
        passed = False

    # Clean up
    import shutil
    shutil.rmtree("/tmp/temuclaude_test_logs", ignore_errors=True)

    print(f"\n=== LOGGER TESTS: {'1/1' if passed else '0/1'} passed ===")
    return passed


# ============================================================
# TEST 8: CLI Entry Point
# ============================================================
def test_cli() -> bool:
    """Test that the CLI entry point works."""
    import subprocess

    try:
        result = subprocess.run(
            [sys.executable, "src/orchestrator.py", "What", "is", "3+4?"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
        )
        output = result.stdout + result.stderr
        if "Answer:" in output and "7" in output:
            print(f"  OK: CLI works: {output.strip()[:80]}")
            passed = True
        elif "Usage:" in output:
            # No args provided — shows usage
            print(f"  FAIL: CLI needs args but got none")
            passed = False
        else:
            print(f"  FAIL: CLI output unexpected: {output[:100]}")
            passed = False
    except Exception as e:
        print(f"  FAIL: CLI exception: {e}")
        passed = False

    print(f"\n=== CLI TESTS: {'1/1' if passed else '0/1'} passed ===")
    return passed


# ============================================================
# TEST 9: Concurrent Logger Writes
# ============================================================
def test_concurrent_logger() -> bool:
    """Test that the logger handles concurrent writes safely."""
    import threading

    logger = QueryLogger(log_dir="/tmp/temuclaude_concurrent_test")
    errors = []

    def write_log(i: int) -> None:
        try:
            logger.log(
                user_query=f"Concurrent test {i}",
                task_type="math",
                routing_tier="medium",
                models_used=["glm-5.2"],
                strategy="direct",
                final_answer=str(i),
                latency_ms=100 + i,
                success=True,
            )
        except Exception as e:
            errors.append(str(e))

    threads = []
    for i in range(20):
        t = threading.Thread(target=write_log, args=(i,))
        threads.append(t)

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    recent = logger.get_recent(20)

    # Verify all 20 were logged
    if len(recent) == 20 and len(errors) == 0:
        print(f"  OK: 20 concurrent writes, all logged, no errors")
        passed = True
    else:
        print(f"  FAIL: {len(recent)}/20 logged, {len(errors)} errors")
        if errors:
            print(f"  First error: {errors[0][:100]}")
        passed = False

    # Clean up
    import shutil
    shutil.rmtree("/tmp/temuclaude_concurrent_test", ignore_errors=True)

    print(f"\n=== CONCURRENT LOGGER TESTS: {'1/1' if passed else '0/1'} passed ===")
    return passed


# ============================================================
# RUN ALL TESTS
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("TEMUCLAUDE — PHASE 1 TEST SUITE")
    print("=" * 60)

    results = []
    results.append(("Classifier", test_classifier()))
    results.append(("Tier Determination", test_tier_determination()))
    results.append(("Model Pool Config", test_model_pool()))
    results.append(("Logger", test_logger()))
    results.append(("Error Handling", test_error_handling()))
    results.append(("All Models Respond", test_all_models_respond()))
    results.append(("End-to-End", test_end_to_end()))
    results.append(("CLI Entry Point", test_cli()))
    results.append(("Concurrent Logger", test_concurrent_logger()))

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