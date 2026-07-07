# Critical Bug Fixes — Discovered 2026-07-06

Three root-cause bugs were killing the daemon swarm. All must be fixed before the system can run 24/7.

## Bug 1: Scout Heartbeat Death Loop

**Root cause:** `daemon_base.py` `run()` method writes heartbeat ONCE at cycle start (line 129), then calls `run_once()` which blocks for 15+ min (scout runs 61 arXiv queries × 15s sleep). Coordinator checks every 60s, declares heartbeat stale after 120s, kills the scout, restarts it. Scout never completes a full cycle. Infinite restart loop.

**Evidence:** Coordinator log showed 15+ restart attempts of scout_daemon in 20 min. Scout heartbeat age = 5h (stale). All daemons showed "sleeping" with 5h heartbeat age — frozen.

**Fix:** Add a background heartbeat thread to `daemon_base.py` that writes heartbeat every 30 seconds, independent of `run_once()` duration. Use `threading.Thread(target=self._heartbeat_loop, daemon=True)` before the main while loop. The thread writes heartbeat every 30s with current status ("running" or "sleeping"). This allows long-running `run_once()` calls (scout 15+ min, integrator 20+ min) without coordinator false-kills.

**Key code change in daemon_base.py:**
```python
import threading  # ADD THIS IMPORT

# In run() method, before while loop:
def _heartbeat_loop(self):
    while self.running:
        self.write_heartbeat("running" if not self._idle else "sleeping",
                           self._heartbeat_extra or {})
        time.sleep(30)

# Start thread before main loop
hb_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
hb_thread.start()
```

## Bug 2: Integrator LLM Timeout

**Root cause:** `integrator_daemon.py` line 95 uses `timeout=300` (5 min) for the LLM auto-integrator script, and line 117 uses `timeout=180` (3 min) for pytest. LLM code generation needs 10-20 min. All 3 items in `implementation_failed` queue timed out.

**Evidence:** Integrator log showed "Implementation timed out" for cognitive_firewall and routellm_cascade. 3 items stuck in `implementation_failed` queue.

**Fix:**
- Increase auto-integrator timeout from 300s to 1200s (20 min)
- Increase pytest timeout from 180s to 600s (10 min)
- Add 2-attempt retry logic with 30s sleep between attempts
- Log stderr on failure (was silently swallowed)
- Use `pytest -x` to stop on first failure (faster)

## Bug 3: Coordinator Blanket 120s Stale Threshold

**Root cause:** `coordinator_daemon.py` line 77 uses a blanket 120s stale threshold for ALL daemons. But daemons have vastly different cycle durations: scout = 15+ min, research = 5-10 min, integrator = 20+ min, distiller = 30s, coordinator = 2 min. One threshold doesn't work.

**Fix:** Add `DAEMON_STALE_THRESHOLD` dict with per-daemon timeouts:
```python
DAEMON_STALE_THRESHOLD = {
    "scout_daemon": 1800,        # 30 min
    "distiller_daemon": 300,    # 5 min
    "research_daemon_1": 900,   # 15 min
    "research_daemon_2": 900,
    "research_daemon_3": 900,
    "integrator_daemon": 2400,  # 40 min
    "cyber_daemon": 900,
    "efficiency_daemon": 900,
    "media_daemon": 900,
    "marketing_daemon": 7200,
    "feedback_daemon": 3600,
    "meta_auditor_daemon": 3600,
    "swot_daemon": 7200,
    "website_daemon": 3600,
    "industry_radar_daemon": 3600,
    "model_optimizer_daemon": 7200,
    "cost_efficiency_daemon": 3600,
}
```

Update `_check_health()` to use `threshold = DAEMON_STALE_THRESHOLD.get(name, 300)` instead of hardcoded `120`.

## Bug 4: Marketing Posts Never Go Out

**Root cause:** Cron job `2a1a40a0efd7` references `scripts/temuclaude_auto_post.sh` but file is at `marketing/auto_post.sh`. All content files are 497 chars but X free account limit is 280 chars. Daily poster skips all content as "TOO LONG."

**Evidence:** Only 2 posts in `posted_log.json`. Morning cron job showed `last_status: error`.

**Fix:**
- Update cron job script path to `marketing/auto_post.sh`
- Create `marketing/content/short_form/` directory with 14 tweets under 280 chars each
- Update `daily_poster.py` SLOT_CONTENT to prioritize short_form entries

## Bug 5: Hardcoded Paths Prevent Cloud Deployment

**Root cause:** All daemon scripts hardcode `/Users/saiful/temuclaude` and `/tmp/temuclaude_daemons`. Can't run on cloud VM where path is `/opt/temuclaude`.

**Fix:** Replace all hardcoded paths with environment variables:
```python
TEMUCLAUDE_DIR = os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude")
RESEARCH_DIR = os.environ.get("RESEARCH_DIR", f"{TEMUCLAUDE_DIR}/research")
DAEMON_STATE_DIR = os.environ.get("DAEMON_STATE_DIR", "/tmp/temuclaude_daemons")
```

This allows the same code to run on Mac (local dev) and Oracle Cloud (production) without changes.

## Bug 6: SWOT/Radar Push JSON Strings to Queue (research_daemon expects file paths)

**Root cause:** `swot_daemon.py` and `industry_radar_daemon.py` push JSON-serialized strings into the `new_findings` queue via `qm.push("new_findings", [json.dumps(task)])`. But `research_daemon.py` line 96 does `with open(finding_file) as f: finding = json.load(f)` — it expects the queue item to be a FILE PATH, not a JSON string. Result: `FileNotFoundError` when research_daemon tries to open a JSON string as if it were a file path.

**Evidence:** research_daemon_1 log showed `FileNotFoundError: [Errno 2] No such file or directory: '{"id": "swot_20260706T..."}'`

**Fix:** SWOT and radar daemons must write findings to JSON files first, then push the file PATH to the queue:
```python
# WRONG (old):
task = json.dumps({...})
qm.push("new_findings", [task])  # Pushes JSON string

# CORRECT (new):
task_data = {...}
finding_file = findings_dir / f"swot_{ts}_{area}.json"
with open(finding_file, 'w') as f:
    json.dump(task_data, f, indent=2)
qm.push("new_findings", [str(finding_file)])  # Pushes file path
```

**Cleanup:** If the queue already contains JSON strings, clean them:
```python
q = qm._read_queue()
nf = q.get("new_findings", [])
cleaned = [item for item in nf if not (isinstance(item, str) and item.startswith("{"))]
q["new_findings"] = cleaned
qm._write_queue(q)
```

## Bug 7: super_intelligence_daemon Missing recall_one Import

**Root cause:** `super_intelligence_daemon.py` calls `recall_one()` but only imports `remember, recall` from `unlimited_memory`. Missing `recall_one`.

**Fix:** `from unlimited_memory import remember, recall, recall_one`

## Bug 8: model_benchmarker.py None.lower() Crash

**Root cause:** `model_benchmarker.py` line 48 does `r["response"].lower()` but `call_model()` can return `None` for the response field when the API call fails. `None.lower()` crashes with `AttributeError`.

**Fix:** Use `r.get("response") or ""` to handle None:
```python
passed = bp["expected_contains"].lower() in (r.get("response") or "").lower()
```

## Bug 9: PID File Race Condition on Restart

**Root cause:** When `stop_swarm.sh` kills processes and `start_swarm.sh` removes PID files, killed processes' `atexit` handlers also try to remove PID files. If a process is killed but hasn't fully exited, `os.kill(pid, 0)` in `is_already_running()` might still return True, causing new daemon instances to exit with "already running" error. Meanwhile the old process's heartbeat daemon thread keeps it alive as an orphan.

**Fix:** In `start_swarm.sh`, add `sleep 3` after killing all processes, then force-remove all PID and heartbeat files, then verify no PID files remain before starting new daemons. Also kill ALL orphaned processes with `pkill -9 -f "research/.*_daemon.py"` before restart.

**Manual PID recovery:** If daemons are running but don't have PID files (orphaned from a race), manually write PID files for them:
```python
import os
pid_map = {77407: "cyber_daemon", ...}  # from ps aux
for pid, name in pid_map.items():
    os.kill(pid, 0)  # verify alive
    with open(f"/tmp/temuclaude_daemons/{name}.pid", "w") as f:
        f.write(str(pid))
```