# External Modification Race Condition — Lessons from 27-Task Build

## Problem
During the 27-task autonomous system build (2026-07-06), multiple files were modified
externally between read and patch operations, causing:

1. **Patch failures** — `patch` tool fails with "Could not find a match" because the
   file content changed after `read_file` but before `patch`.
2. **API mismatches** — daemons built with one API (e.g., `shared_memory.publish()`)
   fail to import because the existing module uses a different API
   (e.g., `shared_memory.add_knowledge()`).
3. **Method name drift** — daemons built with method names like `_run_audit()`,
   `_benchmark_competitors()`, `_determine_throttle()` fail because the externally
   modified version uses different names (`_scan_code()`, `_publish_scoreboard()`,
   `_determine_level()`).

## Root Cause
The Temuclaude project runs autonomous daemons and cron jobs that modify files in
`/Users/saiful/temuclaude/research/`. When building new daemons in the same directory,
the build process races with these autonomous modifications.

## Mitigation Strategy

### 1. Re-read before patch
Always call `read_file` immediately before `patch` on files that might be autonomously
modified. The `_warning` field in patch output tells you if the file was modified since
last read.

### 2. Check actual API before using it
Before importing from an existing module, check its actual exports:
```python
import sys
sys.path.insert(0, 'research')
import shared_memory
print(dir(shared_memory))
# Shows: ['add_knowledge', 'log_event', 'get_knowledge', ...] — NOT 'publish'
```

### 3. Check method names before calling
Before calling methods on a daemon you didn't build:
```python
from some_daemon import SomeDaemon
d = SomeDaemon()
print([m for m in dir(d) if not m.startswith('__')])
```

### 4. Handle Pyright type warnings
Pyright `reportArgumentType` and `reportAttributeAccessIssue` errors on dynamically
typed Python are cosmetic — they don't affect runtime. Only fix if the code actually
fails at import or execution.

### 5. Duplicate file detection
If you create a file and it already exists in a different directory (e.g.,
`research/halal_checker.py` vs `research/scripts/halal_checker.py`), the one earlier
in `sys.path` wins. Check both locations:
```bash
find /Users/saiful/temuclaude -name "*your_module*" -not -path "*/__pycache__/*"
```

## Files Known to Be Autonomously Modified
- `research/integrator_daemon.py` — auto-integrator cron job modifies it
- `research/coordinator_daemon.py` — coordinator daemon may update its own config
- `research/shared_memory.py` — multiple daemons read/write
- `research/meta_auditor_daemon.py` — meta-auditor may self-modify
- `research/cost_efficiency_daemon.py` — cost daemon may self-modify

## Safe Files (not autonomously modified)
- `research/daemon_base.py` — stable base class
- `research/scripts/benchmark_guard.py` — standalone script
- `research/scripts/code_scanner.py` — standalone script
- All new daemon files you create (until they start running)

## Recovery Pattern
When a patch fails due to external modification:
1. Re-read the file with `read_file`
2. Check what changed (diff the content in your context)
3. Adapt your patch to the new content
4. If the external version is better, keep it and adjust your code to match its API