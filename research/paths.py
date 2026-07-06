"""
Centralized path resolution for TemuClaude research daemons.

All daemons should import paths from here instead of hardcoding
absolute paths. This makes the system portable across machines.

Usage:
    from paths import TEMUCLAUDE_DIR, RESEARCH_DIR, STATE_DIR, ...
"""
import os
from pathlib import Path

# Base directory — can be overridden via TEMUCLAUDE_DIR env var
TEMUCLAUDE_DIR = Path(os.environ.get(
    "TEMUCLAUDE_DIR",
    os.path.expanduser("~/temuclaude")
))

# Research directory
RESEARCH_DIR = TEMUCLAUDE_DIR / "research"

# Scripts directory (inside research/)
SCRIPTS_DIR = RESEARCH_DIR / "scripts"

# Source code directory
SRC_DIR = TEMUCLAUDE_DIR / "src"

# Tests directory
TESTS_DIR = TEMUCLAUDE_DIR / "tests"

# Daemon state directory (heartbeat, PID files)
STATE_DIR = Path(os.environ.get(
    "DAEMON_STATE_DIR",
    "/tmp/temuclaude_daemons"
))

# Research data directories
RAW_DIR = RESEARCH_DIR / "raw"
FINDINGS_DIR = RESEARCH_DIR / "findings"

# Queue and priorities
QUEUE_FILE = RESEARCH_DIR / "queue.json"
QUEUE_LOCK_FILE = RESEARCH_DIR / "queue.lock"
PRIORITIES_FILE = RESEARCH_DIR / "priorities.json"
METRICS_FILE = RESEARCH_DIR / "daemon_metrics.json"
PRIORITY_REPORT_FILE = RESEARCH_DIR / "PRIORITY_REPORT.md"

# Shared state files
THROTTLE_FILE = STATE_DIR / "throttle_state.json"
FEEDBACK_FILE = RESEARCH_DIR / "feedback.json"
BOOST_FILE = RESEARCH_DIR / "priority_boost.json"

# Logs
LOGS_DIR = TEMUCLAUDE_DIR / "logs"

# Config
CONFIG_DIR = TEMUCLAUDE_DIR / "config"

# Website
WEBSITE_DIR = TEMUCLAUDE_DIR / "website"

# SWOT reports
SWOT_DIR = RESEARCH_DIR / "swot_reports"

# Ensure state dir exists
STATE_DIR.mkdir(parents=True, exist_ok=True)