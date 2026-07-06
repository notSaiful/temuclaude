#!/usr/bin/env python3
"""
Benchmark Guard — runs benchmark tests and returns pass/fail.
Called by integrator_daemon before committing.
Returns True if no regression, False if any benchmark score dropped.
"""

import subprocess, sys, json
from pathlib import Path

TEMUCLAUDE = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude")) if "os" in dir() else Path("/Users/saiful/temuclaude")
import os
TEMUCLAUDE = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude"))
BASELINE_FILE = TEMUCLAUDE / "research" / "benchmark_baseline.json"


def run_benchmarks() -> dict:
    """Run benchmark tests, return scores."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest",
             "tests/test_beat_fable.py", "tests/test_cost_reductions.py",
             "-q", "--tb=no", "--json-report", "--json-report-file=/tmp/bench_results.json"],
            capture_output=True, text=True, timeout=300, cwd=TEMUCLAUDE
        )
    except Exception:
        pass

    scores = {}
    # Parse pytest output for pass counts
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest",
             "tests/test_beat_fable.py", "tests/test_cost_reductions.py",
             "-q", "--tb=no"],
            capture_output=True, text=True, timeout=300, cwd=TEMUCLAUDE
        )
        output = result.stdout + result.stderr
        import re
        passed = re.findall(r'(\d+) passed', output)
        failed = re.findall(r'(\d+) failed', output)
        scores["total_passed"] = int(passed[0]) if passed else 0
        scores["total_failed"] = int(failed[0]) if failed else 0
    except Exception:
        scores["total_passed"] = 0
        scores["total_failed"] = 0

    return scores


def check_regression() -> bool:
    """Compare current scores to baseline. Return True if no regression."""
    current = run_benchmarks()

    if not BASELINE_FILE.exists():
        # First run — save baseline
        with open(BASELINE_FILE, 'w') as f:
            json.dump(current, f, indent=2)
        return True

    try:
        with open(BASELINE_FILE) as f:
            baseline = json.load(f)
    except Exception:
        return True

    # Check if passed count dropped
    if current.get("total_passed", 0) < baseline.get("total_passed", 0):
        print(f"REGRESSION: passed {current['total_passed']} < baseline {baseline['total_passed']}")
        return False

    # Update baseline if improved
    if current.get("total_passed", 0) > baseline.get("total_passed", 0):
        with open(BASELINE_FILE, 'w') as f:
            json.dump(current, f, indent=2)
        print(f"IMPROVED: passed {current['total_passed']} > baseline {baseline['total_passed']}")

    return True


if __name__ == "__main__":
    sys.exit(0 if check_regression() else 1)
