#!/usr/bin/env python3
"""
Shared Memory Bus — cross-daemon awareness.
Every daemon reads from and writes to this shared state.
"""

import json, os, time, fcntl
from pathlib import Path
from datetime import datetime, timezone

STATE_DIR = Path(os.environ.get("SHARED_STATE_DIR",
    f"{os.environ.get('TEMUCLAUDE_DIR', '/Users/saiful/temuclaude')}/research/shared_state"))
STATE_DIR.mkdir(exist_ok=True)

STATE_FILE = STATE_DIR / "swarm_state.json"
EVENTS_FILE = STATE_DIR / "events.json"
KNOWLEDGE_FILE = STATE_DIR / "knowledge.json"
HEALTH_FILE = STATE_DIR / "health.json"
MAX_EVENTS = 200

def _lock_and_write(filepath, data):
    with open(filepath, 'w') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        json.dump(data, f, indent=2)
        fcntl.flock(f, fcntl.LOCK_UN)

def _lock_and_read(filepath):
    if not filepath.exists():
        return {}
    with open(filepath, 'r') as f:
        fcntl.flock(f, fcntl.LOCK_SH)
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

def update_daemon_state(daemon_name, state):
    full = _lock_and_read(STATE_FILE)
    if "daemons" not in full:
        full["daemons"] = {}
    full["daemons"][daemon_name] = {"name": daemon_name, "timestamp": datetime.now(timezone.utc).isoformat(), **state}
    full["last_updated"] = datetime.now(timezone.utc).isoformat()
    _lock_and_write(STATE_FILE, full)

def read_daemon_state(daemon_name):
    return _lock_and_read(STATE_FILE).get("daemons", {}).get(daemon_name, {})

def read_all_states():
    return _lock_and_read(STATE_FILE)

def log_event(event_type, daemon, message, extra=None):
    events = _lock_and_read(EVENTS_FILE)
    if "events" not in events:
        events["events"] = []
    events["events"].append({"id": f"{daemon}_{int(time.time()*1000)}", "type": event_type,
        "daemon": daemon, "message": message, "timestamp": datetime.now(timezone.utc).isoformat(), "extra": extra or {}})
    if len(events["events"]) > MAX_EVENTS:
        events["events"] = events["events"][-MAX_EVENTS:]
    _lock_and_write(EVENTS_FILE, events)

def get_recent_events(limit=20, event_type=None, daemon=None):
    events = _lock_and_read(EVENTS_FILE).get("events", [])
    if event_type: events = [e for e in events if e.get("type") == event_type]
    if daemon: events = [e for e in events if e.get("daemon") == daemon]
    return events[-limit:]

def add_knowledge(key, value):
    knowledge = _lock_and_read(KNOWLEDGE_FILE)
    if "facts" not in knowledge:
        knowledge["facts"] = {}
    knowledge["facts"][key] = {"value": value, "timestamp": datetime.now(timezone.utc).isoformat()}
    knowledge["last_updated"] = datetime.now(timezone.utc).isoformat()
    _lock_and_write(KNOWLEDGE_FILE, knowledge)

def get_knowledge(key=None):
    knowledge = _lock_and_read(KNOWLEDGE_FILE)
    if key:
        return knowledge.get("facts", {}).get(key, {}).get("value", {})
    return knowledge.get("facts", {})

def update_health(data):
    health = _lock_and_read(HEALTH_FILE)
    health.update(data)
    health["last_updated"] = datetime.now(timezone.utc).isoformat()
    _lock_and_write(HEALTH_FILE, health)

def get_health():
    return _lock_and_read(HEALTH_FILE)

def get_context_for_daemon(daemon_name):
    return {
        "all_daemon_states": read_all_states().get("daemons", {}),
        "recent_events": get_recent_events(limit=30),
        "health": get_health(),
        "knowledge": get_knowledge(),
        "my_last_state": read_daemon_state(daemon_name),
    }

if __name__ == "__main__":
    print(json.dumps(read_all_states(), indent=2))
    for e in get_recent_events(10):
        print(f"  [{e['type']}] {e['daemon']}: {e['message']}")
