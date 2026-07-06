#!/usr/bin/env python3
"""
Coordinator Daemon - Monitors health, manages priorities, scales daemons.
The brain of the swarm.
"""

import json
import time
import os
import sys
import subprocess
import signal
from pathlib import Path
from datetime import datetime, timezone

# Add research dir to path
sys.path.insert(0, "/Users/saiful/temuclaude/research")
sys.path.insert(0, "/Users/saiful/temuclaude/research/scripts")

from daemon_base import DaemonBase, get_all_daemon_statuses
from dynamic_priorities import calculate_dynamic_priorities, generate_priority_report

STATE_DIR = Path("/tmp/temuclaude_daemons")
DAEMON_SCRIPTS = {
    "scout_daemon": "research/scout_daemon.py",
    "distiller_daemon": "research/distiller_daemon.py",
    "research_daemon_1": "research/research_daemon.py",
    "research_daemon_2": "research/research_daemon.py",
    "research_daemon_3": "research/research_daemon.py",
    "integrator_daemon": "research/integrator_daemon.py",
    "cyber_daemon": "research/cyber_daemon.py",
    "efficiency_daemon": "research/efficiency_daemon.py",
    "media_daemon": "research/media_daemon.py",
    "marketing_daemon": "research/marketing_daemon.py",
    "feedback_daemon": "research/feedback_daemon.py",
    "meta_auditor_daemon": "research/meta_auditor_daemon.py",
    "swot_daemon": "research/swot_daemon.py",
    "website_daemon": "research/website_daemon.py",
    "industry_radar_daemon": "research/industry_radar_daemon.py",
    "model_optimizer_daemon": "research/model_optimizer_daemon.py",
    "cost_efficiency_daemon": "research/cost_efficiency_daemon.py",
    "revenue_daemon": "research/revenue_daemon.py",
    "growth_daemon": "research/growth_daemon.py",
    "competitive_dominance_daemon": "research/competitive_dominance_daemon.py",
    "self_expansion_daemon": "research/self_expansion_daemon.py",
    "super_intelligence_daemon": "research/super_intelligence_daemon.py",
}

# Per-daemon stale thresholds (seconds) — each daemon has different expected cycle duration
DAEMON_STALE_THRESHOLD = {
    "scout_daemon": 1800,        # 30 min (61 arXiv queries × 15s = 15+ min)
    "distiller_daemon": 300,    # 5 min
    "research_daemon_1": 900,   # 15 min
    "research_daemon_2": 900,
    "research_daemon_3": 900,
    "integrator_daemon": 2400,  # 40 min (LLM code gen + tests)
    "cyber_daemon": 900,
    "efficiency_daemon": 900,
    "media_daemon": 900,
    "marketing_daemon": 7200,   # 2hr (generates content every 4h)
    "feedback_daemon": 3600,    # 1hr
    "meta_auditor_daemon": 3600, # 1hr (runs every 30min, but audit takes time)
    "swot_daemon": 7200,        # 2hr (runs every 6h)
    "website_daemon": 3600,     # 1hr (runs every 2h)
    "industry_radar_daemon": 3600, # 1hr (runs every 2h)
    "model_optimizer_daemon": 7200, # 2hr (runs every 3h)
    "cost_efficiency_daemon": 3600, # 1hr (runs every 1h)
    "revenue_daemon": 3600,     # 1hr
    "growth_daemon": 7200,      # 2hr (runs every 2h)
    "competitive_dominance_daemon": 7200, # 2hr (runs every 4h)
    "self_expansion_daemon": 43200, # 12hr (runs every 12h)
    "super_intelligence_daemon": 7200, # 2hr (runs every 6h)
}
PRIORITIES_FILE = Path("/Users/saiful/temuclaude/research/priorities.json")
METRICS_FILE = Path("/Users/saiful/temuclaude/research/daemon_metrics.json")


class CoordinatorDaemon(DaemonBase):
    """Swarm coordinator - health, priorities, scaling."""
    
    def __init__(self):
        super().__init__("coordinator_daemon")
        self.daemon_pids = {}
    
    def run_once(self) -> bool:
        """Coordinate the swarm."""
        # 1. Check daemon health
        self._check_health()
        
        # 2. Update dynamic priorities
        self._update_priorities()
        
        # 3. Manage daemon scaling
        self._manage_scaling()
        
        # 4. Log metrics
        self._log_metrics()
        
        return True
    
    def _check_health(self):
        """Check all daemons, restart dead ones using per-daemon stale thresholds."""
        statuses = get_all_daemon_statuses()
        now = time.time()
        
        for name, status in statuses.items():
            if name == "coordinator_daemon":
                continue  # Don't monitor self
            
            threshold = DAEMON_STALE_THRESHOLD.get(name, 300)  # Default 5 min
            
            if status is None:
                self.logger.warning(f"{name}: NO HEARTBEAT - starting")
                self._start_daemon(name)
                continue
            
            try:
                hb_time = datetime.fromisoformat(status["timestamp"].replace('Z', '+00:00'))
                age = now - hb_time.timestamp()
                if age > threshold:
                    self.logger.warning(f"{name}: STALE heartbeat ({age:.0f}s > {threshold}s) - restarting")
                    self._restart_daemon(name)
            except Exception:
                self.logger.warning(f"{name}: Invalid heartbeat - restarting")
                self._restart_daemon(name)
    
    def _start_daemon(self, name: str):
        """Start a daemon process."""
        script = DAEMON_SCRIPTS.get(name)
        if not script:
            self.logger.error(f"No script for {name}")
            return
        
        script_path = Path(f"/Users/saiful/temuclaude/{script}")
        if not script_path.exists():
            self.logger.error(f"Script not found: {script_path}")
            return
        
        # Parse args for research daemons
        args = [sys.executable, str(script_path)]
        if name.startswith("research_daemon"):
            daemon_id = name.split("_")[-1]
            args.extend(["--id", daemon_id])
        
        try:
            # Start in background
            proc = subprocess.Popen(
                args,
                cwd="/Users/saiful/temuclaude",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            self.daemon_pids[name] = proc.pid
            self.logger.info(f"Started {name} (PID: {proc.pid})")
        except Exception as e:
            self.logger.exception(f"Failed to start {name}: {e}")
    
    def _restart_daemon(self, name: str):
        """Restart a daemon by killing and restarting. With exponential backoff."""
        # Track restart count for circuit breaker
        if not hasattr(self, '_restart_counts'):
            self._restart_counts = {}
        count = self._restart_counts.get(name, 0)
        
        # Circuit breaker: after 5 consecutive restarts, give up
        if count >= 5:
            self.logger.error(f"{name} restarted {count} times — circuit breaker tripped, giving up")
            return
        
        self._restart_counts[name] = count + 1
        backoff = min(60 * (2 ** count), 3600)  # 60s, 120s, 240s, 480s, 600s, cap at 1h
        if count > 0:
            self.logger.warning(f"{name} restart #{count+1}, backing off {backoff}s")
            time.sleep(backoff)
        
        # Kill existing
        pid_file = STATE_DIR / f"{name}.pid"
        if pid_file.exists():
            try:
                with open(pid_file) as f:
                    pid = int(f.read().strip())
                os.kill(pid, signal.SIGTERM)
                time.sleep(2)
                # Force kill if needed
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            except Exception:
                pass
        
        self._start_daemon(name)
        
        # Update PID file after restart (the new process will write its own PID)
        # Give it a moment to write
        time.sleep(1)
    
    def _update_priorities(self):
        """Calculate and save dynamic priorities."""
        try:
            priorities = calculate_dynamic_priorities()
            with open(PRIORITIES_FILE, 'w') as f:
                json.dump(priorities, f, indent=2)
            
            # Also generate human-readable report
            report = generate_priority_report()
            report_file = Path(os.environ.get("TEMUCLAUDE_DIR", str(Path.home() / "temuclaude"))) / "research" / "PRIORITY_REPORT.md"
            with open(report_file, 'w') as f:
                f.write(report)
            
            self.logger.debug("Priorities updated")
        except Exception as e:
            self.logger.exception(f"Priority update failed: {e}")
    
    def _manage_scaling(self):
        """Scale research daemons based on queue depth."""
        # Could add logic to start/stop research daemons based on queue size
        pass
    
    def _log_metrics(self):
        """Log system metrics."""
        statuses = get_all_daemon_statuses()
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "daemons": {},
            "queue": self._get_queue_sizes(),
        }
        
        for name, status in statuses.items():
            metrics["daemons"][name] = {
                "alive": status is not None,
                "status": status.get("status") if status else "dead",
                "age_seconds": self._heartbeat_age(status) if status else None,
            }
        
        with open(METRICS_FILE, 'w') as f:
            json.dump(metrics, f, indent=2)
    
    def _heartbeat_age(self, status: dict) -> float:
        """Calculate age of heartbeat in seconds."""
        try:
            hb_time = datetime.fromisoformat(status["timestamp"].replace('Z', '+00:00'))
            return time.time() - hb_time.timestamp()
        except Exception:
            return -1
    
    def _get_queue_sizes(self) -> dict:
        """Get queue sizes."""
        try:
            from queue import QueueManager
            qm = QueueManager()
            all_q = qm.get_all()
            return {k: len(v) if isinstance(v, list) else 0 for k, v in all_q.items()}
        except Exception:
            return {}


def main():
    daemon = CoordinatorDaemon()
    # Coordinate every 60 seconds
    daemon.run(interval=60)


if __name__ == "__main__":
    main()