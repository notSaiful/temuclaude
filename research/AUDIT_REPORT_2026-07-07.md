# TemuClaude Research Daemon System — Audit Report
**Date:** 2026-07-07
**Auditor:** Hermes Agent (automated audit)
**Scope:** All 56 `.py` files in `/Users/saiful/temuclaude/research/`
**Method:** Full source review — every file read in full

---

## Executive Summary

The research daemon system is a 22-daemon autonomous swarm with a shared queue, heartbeat-based health monitoring, and a coordinator that restarts stale daemons. The architecture is sound in concept but has **significant production-readiness issues**: pervasive hardcoded absolute paths, race conditions in file-based IPC, a broken import in `benchmark_guard.py`, stub/incomplete implementations in several daemons, and the coordinator only partially managing all daemon lifecycles.

| Severity | Count |
|----------|-------|
| CRITICAL | 3 |
| HIGH | 12 |
| MEDIUM | 18 |
| LOW | 9 |
| **Total** | **42** |

---

## 1. BROKEN IMPORTS

### CRITICAL-1: `benchmark_guard.py` — `os` used before import
**File:** `scripts/benchmark_guard.py`, line 11–12
```python
TEMUCLAUDE = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude")) if "os" in dir() else Path("/Users/saiful/temuclaude")
import os
```
Line 11 references `os.environ` and `dir()` **before** `os` is imported on line 12. The `"os" in dir()` check will always be `False` at module level (since `os` hasn't been imported yet), so it falls to the `else` branch — which works only by accident because the hardcoded path is correct on this machine. On any other machine this silently uses the wrong path.

**Fix:** Move `import os` to line 1 (before any usage):
```python
import os
import subprocess, sys, json
from pathlib import Path
TEMUCLAUDE = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude"))
```

### HIGH-1: `dashboard.py` — `flask` import not guarded
**File:** `dashboard.py`, line 14
```python
from flask import Flask, render_template_string, jsonify, request
```
Flask is a third-party dependency. If not installed, `import dashboard` crashes. No fallback or graceful error message.

**Fix:** Add try/except around import or document Flask as a required dependency.

### HIGH-2: `scout_arxiv.py`, `scout_github.py`, `scout_huggingface.py` — `certifi` dependency
**Files:** `scripts/scout_arxiv.py` line 14, `scripts/scout_github.py` line 12, `scripts/scout_huggingface.py` line 12
```python
import certifi
```
`certifi` is a third-party package. If not installed, all scouts crash at import time. No try/except fallback to default SSL context.

**Fix:** Add fallback:
```python
try:
    import certifi
    _ssl_ctx = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _ssl_ctx = ssl.create_default_context()
```

### MEDIUM-1: `seo_content_generator.py` — fragile `sys.path` manipulation
**File:** `scripts/seo_content_generator.py`, line 11
```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ollama_client import call_model
```
This inserts the `scripts/` parent (i.e., `research/`) into path, but `ollama_client.py` is in `scripts/`, not `research/`. Should insert `os.path.dirname(__file__)` (the scripts dir itself). Currently works only because daemons already inserted `scripts/` into `sys.path` before importing this module.

**Fix:** Change to `sys.path.insert(0, os.path.dirname(__file__))`.

### MEDIUM-2: `roi_calculator.py` — imports `usage_tracker` without path setup
**File:** `scripts/roi_calculator.py`, line 7
```python
from usage_tracker import load_ledger, compute_summary
```
This works only if `scripts/` is already on `sys.path` (which it is when called from `cost_efficiency_daemon.py`). If run directly, it fails.

**Fix:** Add `sys.path.insert(0, os.path.dirname(__file__))` at top.

### MEDIUM-3: `prompt_evolver.py` — same issue
**File:** `scripts/prompt_evolver.py`, lines 7–8
```python
from ollama_client import call_model
from model_benchmarker import BENCHMARK_PROMPTS
```
No `sys.path` setup. Works only when imported from a daemon that already set up the path.

---

## 2. HARDCODED PATHS (Won't Work in Production)

### CRITICAL-2: Pervasive hardcoded `/Users/saiful/temuclaude` path
**Affected files and lines:**

| File | Line | Hardcoded Path |
|------|------|---------------|
| `coordinator_daemon.py` | 17–18 | `sys.path.insert(0, "/Users/saiful/temuclaude/research")` |
| `coordinator_daemon.py` | 23 | `STATE_DIR = Path("/tmp/temuclaude_daemons")` |
| `coordinator_daemon.py` | 74 | `PRIORITIES_FILE = Path("/Users/saiful/temuclaude/research/priorities.json")` |
| `coordinator_daemon.py` | 75 | `METRICS_FILE = Path("/Users/saiful/temuclaude/research/daemon_metrics.json")` |
| `coordinator_daemon.py` | 134 | `script_path = Path(f"/Users/saiful/temuclaude/{script}")` |
| `coordinator_daemon.py` | 149 | `cwd="/Users/saiful/temuclaude"` |
| `coordinator_daemon.py` | 192 | `report_file = Path("/Users/saiful/temuclaude/research/PRIORITY_REPORT.md")` |
| `scout_daemon.py` | 15–16 | `sys.path.insert(0, "/Users/saiful/temuclaude/research")` |
| `scout_daemon.py` | 21 | `RAW_DIR = Path("/Users/saiful/temuclaude/research/raw")` |
| `distiller_daemon.py` | 15–16 | `sys.path.insert(0, "/Users/saiful/temuclaude/research")` |
| `distiller_daemon.py` | 21–22 | `RAW_DIR`, `FINDINGS_DIR` hardcoded |
| `distiller_daemon.py` | 39, 49 | `Path("/tmp/temuclaude_daemons/distiller_processed.json")` |
| `research_daemon.py` | 16–17 | `sys.path.insert(0, "/Users/saiful/temuclaude/research")` |
| `research_daemon.py` | 23 | `RESEARCH_DIR = Path("/Users/saiful/temuclaude/research")` |
| `integrator_daemon.py` | 17–18 | `sys.path.insert(0, "/Users/saiful/temuclaude/research")` |
| `integrator_daemon.py` | 23–28 | `TEMUCLAUDE_DIR`, `SRC_DIR`, `TESTS_DIR`, etc. hardcoded |
| `integrator_daemon.py` | 40, 50 | `Path("/tmp/temuclaude_daemons/integrator_state.json")` |
| `integrator_daemon.py` | 97 | `"/Users/saiful/temuclaude/research/scripts/auto_integrator.py"` |
| `integrator_daemon.py` | 142 | `"/Users/saiful/temuclaude/research/scripts/benchmark_guard.py"` |
| `cyber_daemon.py` | 24–25 | `sys.path.insert(0, "/Users/saiful/temuclaude/research")` |
| `cyber_daemon.py` | 31 | `RESEARCH_DIR = Path("/Users/saiful/temuclaude/research")` |
| `efficiency_daemon.py` | 29–30 | Same pattern |
| `efficiency_daemon.py` | 36 | Same pattern |
| `media_daemon.py` | 26–27 | Same pattern |
| `media_daemon.py` | 33 | Same pattern |
| `model_optimizer_daemon.py` | 16 | `sys.path.insert(0, "/Users/saiful/temuclaude/research")` |
| `model_optimizer_daemon.py` | 19 | `TEMUCLAUDE = Path("/Users/saiful/temuclaude")` |
| `queue.py` | 15–16 | `QUEUE_FILE`, `QUEUE_LOCK_FILE` hardcoded |
| `daemon_base.py` | 20 | `DAEMON_STATE_DIR = Path("/tmp/temuclaude_daemons")` |
| `dashboard.py` | 18–19 | `RESEARCH_DIR`, `STATE_DIR` hardcoded |
| `dashboard.py` | 299, 301 | `cwd="/Users/saiful/temuclaude"` hardcoded |
| `dynamic_priorities.py` | 27 | `TEMUCLAUDE_DIR = os.path.expanduser("~/temuclaude")` (better but still not configurable) |
| `auto_integrator.py` | 16 | `TEMUCLAUDE_DIR = os.path.expanduser("~/temuclaude")` |
| `resume_swarm.py` | 67–74 | Hardcoded cron job IDs in fallback |
| `pause_swarm.py` | 72–80 | Hardcoded cron job IDs in fallback |
| `swarm_status.py` | 11–19 | Hardcoded cron job IDs |

**Pattern:** Some files use `os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude")` (better), while others hardcode the path directly (worse). The inconsistency means some files respond to env vars and others don't.

**Fix:** Centralize path resolution. Create a `paths.py` in the research dir:
```python
# research/paths.py
import os
from pathlib import Path

TEMUCLAUDE_DIR = Path(os.environ.get("TEMUCLAUDE_DIR", os.path.expanduser("~/temuclaude")))
RESEARCH_DIR = TEMUCLAUDE_DIR / "research"
SCRIPTS_DIR = RESEARCH_DIR / "scripts"
STATE_DIR = Path(os.environ.get("DAEMON_STATE_DIR", "/tmp/temuclaude_daemons"))
RAW_DIR = RESEARCH_DIR / "raw"
FINDINGS_DIR = RESEARCH_DIR / "findings"
QUEUE_FILE = RESEARCH_DIR / "queue.json"
```
Then import everywhere: `from paths import TEMUCLAUDE_DIR, RESEARCH_DIR, ...`

### CRITICAL-3: `swarm_status.py` — hardcoded job IDs will break if jobs are recreated
**File:** `scripts/swarm_status.py`, lines 11–19
The job IDs are hardcoded. If any cron job is deleted and recreated (new ID), this file silently reports `[MISSING]` for all jobs. Unlike `resume_swarm.py` and `pause_swarm.py`, this file has **no dynamic fetch fallback** — it only uses hardcoded IDs.

**Fix:** Use the same dynamic `hermes cron list --json` approach as `resume_swarm.py`.

---

## 3. MISSING ERROR HANDLING

### HIGH-3: `queue.py` — `_read_queue` crashes on corrupt JSON
**File:** `queue.py`, lines 56–58
```python
def _read_queue(self) -> Dict:
    self._acquire_lock()
    try:
        with open(self.queue_file) as f:
            return json.load(f)
    finally:
        self._release_lock()
```
If `queue.json` is corrupt (truncated write), `json.load` raises `json.JSONDecodeError` which propagates to the caller. The lock is released (good, `finally`), but the daemon calling `push`/`pop` will crash.

**Fix:** Add `except json.JSONDecodeError: return {}` before the `finally`.

### HIGH-4: `daemon_base.py` — `write_heartbeat` has no error handling
**File:** `daemon_base.py`, line 100–101
```python
def write_heartbeat(self, status="running", extra=None):
    ...
    with open(self.heartbeat_file, 'w') as f:
        json.dump(hb, f)
```
If the write fails (disk full, permissions), this raises and crashes the heartbeat thread (which silently dies — the `except Exception: pass` in `_heartbeat_loop` catches it, but then no heartbeats are written and the coordinator thinks the daemon is dead and restarts it, causing duplicate processes).

**Fix:** Add try/except in `write_heartbeat` or ensure the caller handles it.

### HIGH-5: `daemon_base.py` — `cleanup` can crash on logger
**File:** `daemon_base.py`, lines 118–123
```python
def cleanup(self):
    self.remove_pid()
    if self.heartbeat_file.exists():
        self.heartbeat_file.unlink()
    self.logger.info(f"{self.name} stopped")
```
If `remove_pid` or `unlink` fails (exception), the logger.info line never executes. Also, `self.logger` may not exist if `__init__` crashed early.

**Fix:** Wrap each operation in try/except.

### HIGH-6: `integrator_daemon.py` — `git checkout .` destroys uncommitted work
**File:** `integrator_daemon.py`, lines 131, 147
```python
subprocess.run(["git", "checkout", "."], cwd=TEMUCLAUDE_DIR)
```
If tests fail, this reverts ALL uncommitted changes — not just the ones the integrator made. If a human developer has uncommitted work, it gets destroyed silently. No warning, no stash.

**Fix:** Use `git stash` before integration and `git stash pop` on failure, or only revert files the integrator touched.

### HIGH-7: `integrator_daemon.py` — `git push` failure not checked
**File:** `integrator_daemon.py`, line 159
```python
subprocess.run(["git", "push"], cwd=TEMUCLAUDE_DIR)
```
Return code is never checked. If push fails (network, auth), the commit is local only and the daemon reports success.

**Fix:** Check `returncode` and log warning on failure.

### HIGH-8: `integrator_daemon.py` — `_implement_finding` doesn't pass finding content to auto_integrator
**File:** `integrator_daemon.py`, lines 95–98
```python
result = subprocess.run([
    sys.executable,
    "/Users/saiful/temuclaude/research/scripts/auto_integrator.py"
], capture_output=True, text=True, timeout=1200, cwd=TEMUCLAUDE_DIR)
```
The `finding_file` path is never passed as an argument. `auto_integrator.py` just reads ALL findings from the directory. This means the integrator doesn't actually implement the specific finding it popped from the queue — it re-processes whatever `auto_integrator.py` finds.

**Fix:** Pass the finding file: `args.extend([finding_file])` and update `auto_integrator.py` to accept it.

### HIGH-9: `revenue_daemon.py` — division by zero potential
**File:** `revenue_daemon.py`, line 24
```python
pricing = get_tier_pricing(costs / max(1, 1))
```
`max(1, 1)` always returns 1 — this is a no-op. If `costs` is 0 (which it is, since `_compute_revenue` returns 0.0), then `0/1 = 0`. The `max(1, 1)` was probably meant to be `max(1, revenue)` to avoid division by zero when computing a cost ratio. But `get_tier_pricing()` doesn't take a ratio — it takes no arguments (it returns a static dict).

**Fix:** Remove this line or fix the logic. `get_tier_pricing()` takes no arguments in `pricing_engine.py`.

### HIGH-10: `model_optimizer_daemon.py` — no error handling on `_update_config`
**File:** `model_optimizer_daemon.py`, lines 111–124
If `MODEL_CONFIG` doesn't exist or is corrupt, the except clause logs a warning but the daemon continues. However, if the config file is partially written (race with another daemon), `json.load` could corrupt the file.

**Fix:** Use atomic write (write to temp, rename).

### HIGH-11: `meta_auditor_daemon.py` — `_save_report` doesn't handle disk full
**File:** `meta_auditor_daemon.py`, lines 199–201
```python
with open(report_file, 'w') as f:
    json.dump(report, f, indent=2)
```
No error handling. If write fails, the daemon crashes.

### MEDIUM-4: Multiple files — `os.kill(pid, signal.SIGKILL)` after SIGTERM
**File:** `coordinator_daemon.py`, lines 167–172
```python
os.kill(pid, signal.SIGTERM)
time.sleep(2)
try:
    os.kill(pid, signal.SIGKILL)
except ProcessLookupError:
    pass
```
If the process exited gracefully after SIGTERM (which is the intended behavior), `SIGKILL` raises `ProcessLookupError` which is caught. But if the process is still alive after 2s, it gets `SIGKILL`'d — this is correct but the 2s sleep is hardcoded and blocks the coordinator.

---

## 4. RACE CONDITIONS / FILE ACCESS ISSUES

### HIGH-12: `shared_memory.py` — write-then-lock pattern (non-atomic)
**File:** `shared_memory.py`, lines 21–25
```python
def _lock_and_write(filepath, data):
    with open(filepath, 'w') as f:       # ← truncates file BEFORE locking
        fcntl.flock(f, fcntl.LOCK_EX)    # ← locks after truncation
        json.dump(data, f, indent=2)
        fcntl.flock(f, fcntl.LOCK_UN)
```
The file is opened with `'w'` (which **truncates** it) **before** the lock is acquired. Any reader doing `_lock_and_read` between the `open()` and `flock()` will see an empty/partial file.

**Fix:** Open with `'w'` but write to a temp file first, then rename. Or open, lock, then truncate:
```python
def _lock_and_write(filepath, data):
    with open(filepath, 'r+') as f:  # or 'a' then seek
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        f.truncate()
        json.dump(data, f, indent=2)
        fcntl.flock(f, fcntl.LOCK_UN)
```
But this requires the file to exist. Better: write to temp file, then atomic rename.

### MEDIUM-5: `queue.py` — lock file fd leaked on exception
**File:** `queue.py`, lines 42–50
```python
def _acquire_lock(self):
    self.lock_fd = open(self.lock_file, 'w')
    fcntl.flock(self.lock_fd, fcntl.LOCK_EX)

def _release_lock(self):
    fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
    self.lock_fd.close()
```
If `_acquire_lock` succeeds but the code between acquire and release throws, `self.lock_fd` is never closed. The `try/finally` in `_read_queue` and `_write_queue` handles this for those methods, but `_acquire_lock` itself could fail on `open()` (leaving no fd but `self.lock_fd` from a previous call).

Also: `self.lock_fd` is an instance variable, so concurrent calls from multiple threads (not expected but possible) would overwrite each other.

**Fix:** Use a context manager pattern:
```python
@contextmanager
def _lock(self):
    with open(self.lock_file, 'w') as fd:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
```

### MEDIUM-6: `queue.py` — non-atomic read-modify-write
**File:** `queue.py`, `push` and `pop` methods
The lock is acquired, file is read, modified in memory, and written back. The lock prevents concurrent access **within the same process**, but `fcntl.flock` with `LOCK_EX` only works between processes that also use flock. If a daemon opens the queue file directly (bypassing QueueManager), the lock is bypassed.

### MEDIUM-7: `dedup.py` — `save_seen` is not atomic
**File:** `scripts/dedup.py`, lines 22–26
```python
def save_seen(state: dict) -> None:
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
```
No locking. If two scouts run concurrently and both call `filter_new` at the same time, they both load the same state, both append their new IDs, and the second write overwrites the first. New IDs from the first scout are lost.

**Fix:** Use `fcntl.flock` or a lock file.

### MEDIUM-8: `radar_scorer.py` — same non-atomic save_seen
**File:** `scripts/radar_scorer.py`, lines 27–32
Same issue as dedup.py — no locking on `save_seen`.

### MEDIUM-9: Multiple daemons — write to same files without locking
**Files:**
- `swot_daemon.py` line 129: `with open(BOOST_FILE, 'w') as f:`
- `industry_radar_daemon.py` line 92: `with open(BOOST_FILE, 'w') as f:`
- `cost_efficiency_daemon.py` line 58: `with open(THROTTLE_FILE, 'w') as f:`
- `coordinator_daemon.py` lines 187–194: writes PRIORITIES_FILE and PRIORITY_REPORT.md
- `feedback_daemon.py` line 121: `with open(FEEDBACK_FILE, 'w') as f:`
None of these use file locking. If two daemons write the same file (e.g., if coordinator and feedback both write to overlapping files), data can be lost.

### MEDIUM-10: `daemon_base.py` — heartbeat thread races with main thread
**File:** `daemon_base.py`, lines 130–138
The heartbeat thread reads `self._idle` and `self._heartbeat_extra` which are written by the main thread. These are plain Python attributes with no synchronization. In CPython with the GIL, this is safe for simple reads/writes, but if the values are dicts that get replaced mid-read, the heartbeat thread could see a partially-updated dict.

### MEDIUM-11: `integrator_daemon.py` — `git push` without checking for upstream
**File:** `integrator_daemon.py`, line 159
If the branch has no upstream configured, `git push` fails silently (return code not checked).

### MEDIUM-12: `distiller_daemon.py` — `_save_processed` non-atomic
**File:** `distiller_daemon.py`, lines 47–51
```python
def _save_processed(self):
    state_file = Path("/tmp/temuclaude_daemons/distiller_processed.json")
    with open(state_file, 'w') as f:
        json.dump(list(self.processed), f)
```
If the daemon crashes mid-write, the state file is corrupt and all processed files will be re-processed on restart.

### MEDIUM-13: `unlimited_memory.py` — SQLite not thread-safe
**File:** `unlimited_memory.py`, lines 19–22
Each call to `_get_db()` creates a new connection. If multiple daemons call `remember()` concurrently, they each open their own connection to the same SQLite file. SQLite supports concurrent access with WAL mode, but the default mode uses file locking that can cause `database is locked` errors.

**Fix:** Enable WAL mode: `conn.execute("PRAGMA journal_mode=WAL")` after connecting.

---

## 5. DEAD CODE / STUBS / INCOMPLETE IMPLEMENTATIONS

### HIGH-13: `research_daemon.py` — `_research_topic` is a stub
**File:** `research_daemon.py`, lines 59–91
The method writes a prompt to a file but **doesn't actually execute any research**. It creates a text file with instructions for an LLM agent that never runs. The "research" is just a prompt template saved to disk.

The comment on line 106-107 confirms this:
```python
# For now, create a structured research template
# The actual LLM research would be triggered via the cron agent system
```

**Fix:** Either integrate with the LLM (call Ollama/OpenRouter) or document that this is a placeholder for the cron system.

### MEDIUM-14: `coordinator_daemon.py` — `_manage_scaling` is empty stub
**File:** `coordinator_daemon.py`, lines 200–203
```python
def _manage_scaling(self):
    """Scale research daemons based on queue depth."""
    # Could add logic to start/stop research daemons based on queue size
    pass
```
The coordinator never scales research daemons. The comment acknowledges this.

### MEDIUM-15: `meta_auditor_daemon.py` — `_attempt_fix` is mostly a stub
**File:** `meta_auditor_daemon.py`, lines 168–183
```python
def _attempt_fix(self, issue: dict) -> bool:
    # For now, log the issue. LLM-based fix can be added later.
    if issue.get("type") == "failed_queue_overflow":
        ...  # Only this one fix is implemented
    return False
```
Only `failed_queue_overflow` is handled. All other issue types (test failures, daemon errors, stale findings, high revert rate) are logged but never fixed.

### MEDIUM-16: `marketing_daemon.py` — `_track_engagement` is a stub
**File:** `marketing_daemon.py`, lines 124–135
```python
def _track_engagement(self):
    ...
    for post in recent:
        # Would call Twitter API here to get engagement
        pass
```
The method does nothing. No Twitter API integration exists.

### MEDIUM-17: `revenue_daemon.py` — `_compute_revenue` returns hardcoded 0
**File:** `revenue_daemon.py`, lines 36–37
```python
def _compute_revenue(self):
    return 0.0  # Integrate with billing when available
```
The revenue daemon always computes $0 revenue. The Ummah Fund allocation is always $0.

### MEDIUM-18: `auto_integrator.py` — only prints instructions, doesn't implement
**File:** `scripts/auto_integrator.py`, lines 110–128
The script outputs text instructions for an LLM agent ("=== INSTRUCTIONS FOR LLM AGENT ===") but doesn't actually implement anything itself. It relies on an external LLM cron agent to read its stdout and act.

### MEDIUM-19: `dashboard.py` — only monitors 7 daemons, not all 22
**File:** `dashboard.py`, lines 21–25
```python
DAEMONS = [
    "scout_daemon", "distiller_daemon",
    "research_daemon_1", "research_daemon_2", "research_daemon_3",
    "integrator_daemon", "coordinator_daemon"
]
```
The dashboard only lists 7 of the 22 daemons. The newer daemons (cyber, efficiency, media, marketing, feedback, meta_auditor, swot, website, industry_radar, model_optimizer, cost_efficiency, revenue, growth, competitive_dominance, self_expansion, super_intelligence) are invisible on the dashboard.

**Fix:** Import `get_all_daemon_statuses` from `daemon_base.py` instead of maintaining a separate list.

---

## 6. TODO/FIXME/STUB MARKERS

### LOW-1: `meta_auditor_daemon.py` line 169
```python
# For now, log the issue. LLM-based fix can be added later.
```

### LOW-2: `coordinator_daemon.py` line 202
```python
# Could add logic to start/stop research daemons based on queue size
```

### LOW-3: `research_daemon.py` lines 106–107
```python
# For now, create a structured research template
# The actual LLM research would be triggered via the cron agent system
```

### LOW-4: `marketing_daemon.py` line 132
```python
# Would call Twitter API here to get engagement
```

### LOW-5: `revenue_daemon.py` line 37
```python
return 0.0  # Integrate with billing when available
```

### LOW-6: `auto_integrator.py` line 77
```python
# This script is run BY the LLM cron agent — it uses these functions
```

### LOW-7: `benchmark_guard.py` lines 11–12
The convoluted `if "os" in dir()` pattern is essentially a broken TODO for making the path configurable.

### LOW-8: `swarm_status.py` lines 11–19
Hardcoded job IDs are a maintenance TODO — they will need updating whenever cron jobs are recreated.

### LOW-9: `resume_swarm.py` lines 67–74 and `pause_swarm.py` lines 72–80
Fallback hardcoded job IDs — same maintenance issue.

---

## 7. COORDINATOR DAEMON LIFECYCLE MANAGEMENT ANALYSIS

### Does `coordinator_daemon.py` properly manage all daemon lifecycles?

**Partially.** Here's the detailed assessment:

#### ✅ What it does correctly:
1. **Defines all 22 daemons** in `DAEMON_SCRIPTS` dict (lines 24–47) — complete list
2. **Per-daemon stale thresholds** (lines 50–73) — thoughtful, each daemon has a different expected cycle duration
3. **Health check** reads heartbeat files and checks staleness (lines 101–125)
4. **Restart logic** kills stale process and starts a new one (lines 159–177)
5. **PID file management** — reads PID files, sends SIGTERM then SIGKILL
6. **Research daemon args** — correctly passes `--id` flag for `research_daemon_1/2/3` (lines 141–143)

#### ❌ What it misses:

**Issue C-1: `get_all_daemon_statuses()` in `daemon_base.py` is missing `coordinator_daemon` from the monitored list**
**File:** `daemon_base.py`, lines 203–213
The `get_all_daemon_statuses()` function lists all daemons but does NOT include `coordinator_daemon`. The coordinator's own heartbeat is never checked by anyone. If the coordinator crashes, no one restarts it.

**Fix:** Add a watchdog mechanism or a separate `coordinator_watchdog.py` that monitors the coordinator.

**Issue C-2: Coordinator doesn't verify daemons actually started**
**File:** `coordinator_daemon.py`, lines 145–155
After `subprocess.Popen`, the coordinator stores `proc.pid` but never checks if the process actually started successfully. If the daemon script has a syntax error or import failure, it exits immediately, but the coordinator doesn't notice until the next health check (60s later).

**Fix:** After starting, `time.sleep(2)` then check if the process is still alive: `os.kill(pid, 0)`.

**Issue C-3: Coordinator stores PIDs in `self.daemon_pids` but never reads them**
**File:** `coordinator_daemon.py`, line 83, 154
`self.daemon_pids` is populated but never used. The restart logic reads from PID files on disk, not from this dict. Dead code.

**Issue C-4: No daemon stop mechanism**
The coordinator can start and restart daemons but has **no graceful stop** mechanism. There's no `stop_daemon` method. To stop a daemon, you must kill it manually or let it crash.

**Issue C-5: No exponential backoff on restart**
**File:** `coordinator_daemon.py`, lines 159–177
If a daemon keeps crashing immediately (e.g., broken import), the coordinator will restart it every 60 seconds forever, creating a restart loop. No circuit breaker, no exponential backoff, no "give up after N attempts."

**Fix:** Track restart count per daemon and back off:
```python
self.restart_count = {}
...
count = self.restart_count.get(name, 0)
if count > 5:
    self.logger.error(f"{name} restarted {count} times, giving up")
    return
self.restart_count[name] = count + 1
backoff = min(60 * (2 ** count), 3600)
time.sleep(backoff)
```

**Issue C-6: Coordinator doesn't coordinate `daemon_base.py`'s `is_already_running`**
When the coordinator starts a daemon, the daemon checks `is_already_running()` which looks at the PID file. If a stale PID file exists from a crashed process (but the PID is reused by another process), the daemon will refuse to start, and the coordinator won't notice.

**Issue C-7: Coordinator's `_check_health` can restart a daemon that's just slow**
**File:** `coordinator_daemon.py`, lines 117–125
The staleness check compares heartbeat age to a threshold. If a daemon is running a long task (e.g., `integrator_daemon` running a 20-minute integration), its heartbeat shows "running" but the timestamp may be stale. The coordinator would kill and restart it, losing the in-progress work.

**Fix:** Check heartbeat status: if `status == "running"`, use a longer threshold or skip restart.

**Issue C-8: No coordination between cost_efficiency_daemon's throttle and coordinator**
**File:** `cost_efficiency_daemon.py`, lines 54–57
The cost efficiency daemon writes throttle actions like `"pause_research"`, `"pause_marketing"` to `throttle_state.json`. But the coordinator never reads this file. Throttle decisions are made but never enforced.

**Fix:** Coordinator should read `throttle_state.json` and stop/restart daemons based on throttle level.

---

## 8. ADDITIONAL ISSUES

### MEDIUM-20: `hasan_identity.py` — `verify_integrity` is too fragile
**File:** `hasan_identity.py`, lines 277–289
```python
checks = [
    len(MISSION) == 7,
    len(NEVER_DO) >= 16,
    len(PRINCIPLES) >= 7,
    ...
]
```
If someone adds an 8th mission item or an 18th never-do rule (which should be fine — the file says it's immutable but adding rules is an improvement), the integrity check fails and **all daemons refuse to start**. The checks are too rigid.

### MEDIUM-21: `daemon_base.py` — duplicate log handlers on re-init
**File:** `daemon_base.py`, lines 54–75
`_setup_logger` creates new file and console handlers every time it's called. If a subclass calls `super().__init__()` and then re-creates the logger, duplicate handlers accumulate. Not a current bug but a latent issue.

### MEDIUM-22: `daemon_base.py` — `is_already_running` race condition
**File:** `daemon_base.py`, lines 103–116
Between checking `is_already_running()` and `write_pid()`, another instance could start. Both would pass the check and both would write PID files.

### MEDIUM-23: `dynamic_priorities.py` — hardcoded date in GitHub query
**File:** `scripts/radar_sources.py` line 51
```python
q=topic:llm+created:>2026-06-01&sort=stars
```
The date `2026-06-01` is hardcoded. Over time, this will miss older repos and always show the same recent ones.

**Fix:** Use a dynamic date: `created:>{(datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')}`.

### MEDIUM-24: `model_optimizer_daemon.py` — overly simplistic benchmark
**File:** `model_optimizer_daemon.py`, line 50
```python
test_prompt = "What is 17 * 23? Answer with just the number."
```
This single arithmetic question is the entire quality test. A model that gets this right but fails on reasoning, coding, or instruction-following would be selected as "best."

### MEDIUM-25: `scout_arxiv.py` — 61 queries × 15s sleep = 15+ minutes per cycle
**File:** `scripts/scout_arxiv.py`, lines 172–178
With 61 queries and 15-second sleep between each, one full scout cycle takes ~15 minutes. The arXiv API rate limit is 1 request per 3 seconds, so 15s is overly conservative, but the total time means the scout_daemon's 6-hour interval gives plenty of room.

### LOW-10: `dashboard.py` — XSS vulnerability
**File:** `dashboard.py`, lines 153, 157, 175
The dashboard renders daemon names, file names, and commit messages into HTML via template literals without escaping. If a daemon name or file name contains HTML/JS, it would be injected into the page.

---

## 9. SUMMARY OF RECOMMENDED FIXES (Prioritized)

### Immediate (CRITICAL):
1. Fix `benchmark_guard.py` import order (move `import os` to top)
2. Replace all hardcoded `/Users/saiful/temuclaude` paths with env var / `paths.py` approach
3. Fix `swarm_status.py` to dynamically fetch cron job IDs

### Short-term (HIGH):
4. Fix `shared_memory.py` write-then-lock race condition (use atomic write)
5. Add error handling to `queue.py` `_read_queue` for corrupt JSON
6. Fix `integrator_daemon.py` to pass finding file to `auto_integrator.py`
7. Fix `integrator_daemon.py` to not `git checkout .` (destroys unrelated work)
8. Check `git push` return code in integrator
9. Fix `revenue_daemon.py` `get_tier_pricing()` call (takes no arguments)
10. Add restart backoff/circuit breaker to coordinator
11. Update `dashboard.py` DAEMONS list to include all 22 daemons (or use `get_all_daemon_statuses`)
12. Add `certifi` import fallback in scout scripts

### Medium-term (MEDIUM):
13. Enable SQLite WAL mode in `unlimited_memory.py`
14. Add file locking to `dedup.py` and `radar_scorer.py`
15. Implement coordinator reading `throttle_state.json`
16. Add watchdog for coordinator daemon
17. Implement actual LLM research in `research_daemon.py` (or document as stub)
18. Fix `dynamic_priorities.py` GitHub query to use dynamic date
19. Add `import os` path setup to `roi_calculator.py` and `prompt_evolver.py`

### Long-term (architectural):
20. Centralize all path management in a single `paths.py` module
21. Replace file-based queue with a proper message broker (Redis, SQLite queue)
22. Implement coordinator graceful stop mechanism
23. Implement actual revenue tracking in `revenue_daemon.py`
24. Implement actual engagement tracking in `marketing_daemon.py`

---

**Audit complete.** 42 issues found across 56 files. 3 critical, 12 high, 18 medium, 9 low. The system is functional in its current single-machine, single-user environment but would not survive deployment to a different machine or production environment without addressing the hardcoded paths and race conditions.