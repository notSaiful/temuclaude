#!/usr/bin/env python3
"""
Base daemon class for Temuclaude Research Swarm.
Provides PID management, heartbeat, logging, graceful shutdown.
"""

import os
import sys
import json
import time
import signal
import logging
import atexit
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

DAEMON_STATE_DIR = Path("/tmp/temuclaude_daemons")
DAEMON_STATE_DIR.mkdir(exist_ok=True)


class DaemonBase(ABC):
    """Base class for all research swarm daemons."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self.pid_file = DAEMON_STATE_DIR / f"{name}.pid"
        self.heartbeat_file = DAEMON_STATE_DIR / f"{name}_heartbeat.json"
        self.log_file = DAEMON_STATE_DIR / f"{name}.log"
        self.running = False
        self.logger = self._setup_logger()
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        atexit.register(self.cleanup)
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)
        
        # File handler
        fh = logging.FileHandler(self.log_file)
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        return logger
    
    def _signal_handler(self, signum, frame):
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def write_pid(self):
        """Write PID file."""
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
    
    def remove_pid(self):
        """Remove PID file."""
        if self.pid_file.exists():
            self.pid_file.unlink()
    
    def write_heartbeat(self, status: str = "running", extra: Optional[Dict] = None):
        """Write heartbeat file for health monitoring."""
        hb = {
            "daemon": self.name,
            "pid": os.getpid(),
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "extra": extra or {}
        }
        with open(self.heartbeat_file, 'w') as f:
            json.dump(hb, f)
    
    def is_already_running(self) -> bool:
        """Check if another instance is running."""
        if not self.pid_file.exists():
            return False
        try:
            with open(self.pid_file) as f:
                pid = int(f.read().strip())
            # Check if process exists
            os.kill(pid, 0)  # Signal 0 just checks existence
            return True
        except (ValueError, OSError, ProcessLookupError):
            # Stale PID file
            self.pid_file.unlink(missing_ok=True)
            return False
    
    def cleanup(self):
        """Cleanup on exit."""
        self.remove_pid()
        if self.heartbeat_file.exists():
            self.heartbeat_file.unlink()
        self.logger.info(f"{self.name} stopped")
    
    @abstractmethod
    def run_once(self) -> bool:
        """Run one iteration. Return True to continue, False to stop."""
        pass
    
    def run(self, interval: float = 60.0):
        """Main daemon loop."""
        if self.is_already_running():
            self.logger.error(f"{self.name} already running (PID file exists)")
            sys.exit(1)
        
        self.write_pid()
        self.running = True
        self.logger.info(f"{self.name} started (PID: {os.getpid()})")
        
        while self.running:
            try:
                start = time.time()
                self.write_heartbeat("running", {"cycle_start": start})
                
                should_continue = self.run_once()
                
                elapsed = time.time() - start
                self.write_heartbeat("sleeping", {"cycle_duration": elapsed})
                
                if not should_continue:
                    self.logger.info("run_once returned False, stopping")
                    break
                
                # Sleep for remaining interval
                sleep_time = max(0, interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                self.logger.exception(f"Error in main loop: {e}")
                self.write_heartbeat("error", {"error": str(e)})
                time.sleep(30)  # Back off on error
        
        self.cleanup()


def get_daemon_status(name: str) -> Optional[Dict]:
    """Get status of a daemon from its heartbeat file."""
    hb_file = DAEMON_STATE_DIR / f"{name}_heartbeat.json"
    if not hb_file.exists():
        return None
    try:
        with open(hb_file) as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None


def get_all_daemon_statuses() -> Dict[str, Optional[Dict]]:
    """Get status of all known daemons."""
    daemons = [
        "scout_daemon", "distiller_daemon", 
        "research_daemon_1", "research_daemon_2", "research_daemon_3",
        "integrator_daemon", "coordinator_daemon",
        "cyber_daemon",  # Added 2026-07-06
        "efficiency_daemon",  # Added 2026-07-06
    ]
    return {name: get_daemon_status(name) for name in daemons}


if __name__ == "__main__":
    # Test the base class
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--daemon", type=str)
    args = parser.parse_args()
    
    if args.status:
        if args.daemon:
            print(json.dumps(get_daemon_status(args.daemon), indent=2))
        else:
            print(json.dumps(get_all_daemon_statuses(), indent=2))