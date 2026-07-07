# Temuclaude Daemon Architecture

The swarm migrated from cron jobs to daemon processes for zero-gap continuous execution. Cron jobs had gaps (between scheduled runs), no state, and couldn't self-heal. Daemons run forever with heartbeat monitoring.

## DaemonBase (daemon_base.py)

All daemons inherit from DaemonBase, which provides:

- **PID management**: Writes PID to `/tmp/temuclaude_daemons/<name>.pid`. On startup, checks if another instance is running (stale PID detection). On exit, removes PID file.
- **Heartbeat**: Writes JSON to `/tmp/temuclaude_daemons/<name>_heartbeat.json` with status ("running" or "sleeping"), timestamp, and extra metadata. Coordinator checks heartbeat age to detect dead daemons.
- **Logging**: File + console logging to `/tmp/temuclaude_daemons/<name>.log`. Format: `%(asctime)s | %(name)s | %(levelname)s | %(message)s`.
- **Graceful shutdown**: SIGTERM and SIGINT handlers set `self.running = False`. The main loop checks this flag and exits cleanly. `atexit` ensures PID/heartbeat cleanup.
- **Abstract run_once()**: Each daemon implements `run_once()` which returns True to continue or False to stop. The base class handles the sleep loop.

```python
class DaemonBase(ABC):
    def __init__(self, name, config=None):
        self.pid_file = DAEMON_STATE_DIR / f"{name}.pid"
        self.heartbeat_file = DAEMON_STATE_DIR / f"{name}_heartbeat.json"
        self.log_file = DAEMON_STATE_DIR / f"{name}.log"
        # ...

    @abstractmethod
    def run_once(self) -> bool:
        """Run one iteration. Return True to continue, False to stop."""
        pass

    def run(self, interval=60.0):
        """Main daemon loop with heartbeat + sleep."""
        if self.is_already_running():
            sys.exit(1)
        self.write_pid()
        self.running = True
        while self.running:
            start = time.time()
            self.write_heartbeat("running")
            should_continue = self.run_once()
            elapsed = time.time() - start
            self.write_heartbeat("sleeping", {"cycle_duration": elapsed})
            if not should_continue:
                break
            time.sleep(max(0, interval - elapsed))
        self.cleanup()
```

## Coordinator (coordinator_daemon.py)

The coordinator is the "brain" of the swarm. It runs every 60 seconds and:

1. **Health check**: Reads all heartbeat files. If a daemon's heartbeat is stale (>2 min) or missing, it restarts the daemon.
2. **Priority update**: Runs `calculate_dynamic_priorities()` and saves to `priorities.json` + `PRIORITY_REPORT.md`.
3. **Scaling**: Placeholder for dynamic daemon scaling based on queue depth.
4. **Metrics**: Writes `daemon_metrics.json` with all daemon statuses + queue sizes.

The coordinator has a `DAEMON_SCRIPTS` dict mapping daemon names to script paths. To add a new daemon, add it here:

```python
DAEMON_SCRIPTS = {
    "scout_daemon": "research/scout_daemon.py",
    "distiller_daemon": "research/distiller_daemon.py",
    "research_daemon_1": "research/research_daemon.py",
    "research_daemon_2": "research/research_daemon.py",
    "research_daemon_3": "research/research_daemon.py",
    "integrator_daemon": "research/integrator_daemon.py",
    "cyber_daemon": "research/cyber_daemon.py",
}
```

The coordinator starts daemons using `subprocess.Popen` with `start_new_session=True` (so they survive parent exit) and `stdout/stderr=subprocess.DEVNULL` (logging goes to the daemon's own log file via DaemonBase).

## Queue System (queue.py)

Daemons communicate through a file-based queue system:

- `new_raw`: Scout pushes raw JSON file paths here → Distiller pops
- `new_findings`: Distiller pushes distilled JSON paths here → Research pops
- `research_requests`: Research pushes deep research requests → Research pops
- `research_complete`: Research pushes completed reports → Integrator pops
- `implementation_queue`: Research/anyone pushes implementation tasks → Integrator pops
- `implementation_complete`: Integrator pushes completed implementations
- `implementation_failed`: Integrator pushes failed implementations (for review)

The queue is managed by `QueueManager` class with file-based locking (`queue.lock`).

## Heartbeat Health Monitoring

The coordinator checks daemon health by reading heartbeat files:

```python
def _check_health(self):
    statuses = get_all_daemon_statuses()
    now = time.time()
    for name, status in statuses.items():
        if status is None:
            self._start_daemon(name)  # No heartbeat = dead, start it
            continue
        hb_time = datetime.fromisoformat(status["timestamp"].replace('Z', '+00:00'))
        age = now - hb_time.timestamp()
        if age > 120:  # Stale >2 min
            self._restart_daemon(name)
```

## Common Pitfalls

- **status_swarm.sh hardcoded array**: The status dashboard has a hardcoded daemon array on line 21. If you add a daemon but don't update this array, the daemon won't appear in the dashboard even if it's running.
- **Coordinator DAEMON_SCRIPTS**: If you add a daemon but don't register it in DAEMON_SCRIPTS, the coordinator won't restart it if it dies.
- **daemon_base get_all_daemon_statuses**: If you don't add the daemon name to the daemons list in this function, `get_all_daemon_statuses()` won't track it, and the coordinator won't know about it.
- **PID file stale**: If a daemon crashes without cleanup, the PID file remains. DaemonBase's `is_already_running()` checks if the PID is actually alive and removes stale PID files.
- **Python path**: Daemons use `sys.path.insert(0, "/Users/saiful/temuclaude/research")` and `sys.path.insert(0, "/Users/saiful/temuclaude/research/scripts")` to import each other. This is hardcoded to the user's path.
- **nohup vs terminal background**: To start a daemon manually, use `terminal(background=true)` in Hermes, NOT `nohup` in a foreground command (Hermes flags shell-level background wrappers).