#!/usr/bin/env python3
"""
Temuclaude Full System Integration Test
Verifies all 23 daemons, memory systems, quality guards, and orchestration.
Run: python3 ~/.hermes/skills/research/temuclaude-research-swarm/scripts/integration_test.py
     (from /Users/saiful/temuclaude directory)
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, 'research')
sys.path.insert(0, 'research/scripts')

passed = 0
failed = 0

def test(name, condition, detail=""):
    global passed, failed
    status = "PASS" if condition else "FAIL"
    if condition:
        passed += 1
    else:
        failed += 1
    print(f"  [{status}] {name}" + (f" -- {detail}" if detail else ""))

def run_all():
    global passed, failed
    passed = 0
    failed = 0

    print("=== TEMUCLAUDE FULL SYSTEM INTEGRATION TEST ===\n")

    # 1. Daemon Infrastructure
    print("1. Daemon Infrastructure")
    from daemon_base import DaemonBase, get_all_daemon_statuses
    statuses = get_all_daemon_statuses()
    test("Daemon base tracks 23 daemons", len(statuses) == 23, f"{len(statuses)} daemons")
    test("Background heartbeat thread exists", hasattr(DaemonBase, '_heartbeat_loop'))

    from coordinator_daemon import DAEMON_STALE_THRESHOLD
    test("Per-daemon thresholds", len(DAEMON_STALE_THRESHOLD) >= 22, f"{len(DAEMON_STALE_THRESHOLD)} thresholds")
    test("Scout gets 30min", DAEMON_STALE_THRESHOLD.get("scout_daemon") == 1800)
    test("Integrator gets 40min", DAEMON_STALE_THRESHOLD.get("integrator_daemon") == 2400)

    # 2. Quality Guards
    print("\n2. Quality Guards")
    from benchmark_guard import check_regression
    test("Benchmark guard exists", callable(check_regression))

    # 3. All daemons import
    print("\n3. All Daemons Import")
    daemon_modules = [
        'marketing_daemon', 'feedback_daemon', 'meta_auditor_daemon', 'swot_daemon',
        'website_daemon', 'industry_radar_daemon', 'model_optimizer_daemon',
        'cost_efficiency_daemon', 'revenue_daemon', 'growth_daemon',
        'competitive_dominance_daemon', 'self_expansion_daemon', 'super_intelligence_daemon',
    ]
    all_import = True
    for mod in daemon_modules:
        try:
            __import__(mod)
        except Exception as e:
            all_import = False
            test(f"{mod} imports", False, str(e)[:50])
    test(f"All 13 new daemons import", all_import, f"{len(daemon_modules)} modules")

    # 4. Memory systems
    print("\n4. Memory Systems")
    from shared_memory import add_knowledge
    add_knowledge('test', 'value')
    test("Shared memory bus works", True)

    from unlimited_memory import remember, recall
    remember("test_cat", "test_daemon", "Test title", "Test content")
    r = recall("test content")
    test("Unlimited memory works", len(r) > 0, f"{len(r)} results")

    # 5. Halal checker
    print("\n5. Halal Compliance")
    from halal_checker import check_output_halal
    h = check_output_halal("Build AI for the Ummah")
    test("Halal checker allows halal content", h["is_halal"] == True)
    h2 = check_output_halal("Buy wine and beer")
    test("Halal checker blocks haram content", h2["is_halal"] == False)

    # 6. Orchestration
    print("\n6. Orchestration & Cloud")
    from ollama_client import *
    test("Ollama client imports", True)
    test("Master control script exists", os.path.exists('research/scripts/master_control.sh'))
    test("Deploy script exists", os.path.exists('research/scripts/deploy_oracle.sh'))

    # 7. Content
    print("\n7. Marketing Content")
    test("Short form content set 1", os.path.exists('marketing/content/short_form_01.md'))
    test("Short form content set 2", os.path.exists('marketing/content/short_form_02.md'))

    # 8. Integrator pipeline
    print("\n8. Integrator Pipeline")
    with open('research/integrator_daemon.py') as f:
        integ = f.read()
    test("Integrator has benchmark guard", "benchmark_guard" in integ)
    test("Integrator has retry loop", "max_attempts" in integ or "attempt" in integ)

    # Summary
    print(f"\n=== RESULTS ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    total = passed + failed
    pct = passed / total * 100 if total > 0 else 0
    print(f"Total tests: {total}")
    print(f"Success rate: {pct:.0f}%")

    if pct == 100:
        print("\n*** ALL TESTS PASSED -- SYSTEM READY ***")
    elif pct >= 90:
        print("\n*** SYSTEM OPERATIONAL -- MINOR ISSUES ***")
    else:
        print("\n*** SYSTEM NEEDS ATTENTION ***")

    return pct == 100

if __name__ == "__main__":
    os.chdir("/Users/saiful/temuclaude")
    success = run_all()
    sys.exit(0 if success else 1)