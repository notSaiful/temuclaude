#!/usr/bin/env python3
"""
Hasan Shared Intelligence Hub
==============================
A unified intelligence layer that ALL daemons, the watchdog, and Hasan's chat
read from and write to. This ensures everyone has the same knowledge.

Three layers:
1. events.json — real-time event bus (last 200 events, all daemons see each other)
2. swarm_state.json — live daemon registry (who's alive, what they're doing)
3. knowledge.json — permanent shared facts (what we learned, decided, built)

The hub is a simple file-based store. Daemons call:
  - share_intelligence.broadcast(daemon, type, message)
  - share_intelligence.update_state(daemon, status, extra)
  - share_intelligence.learn(key, value, daemon)
  - share_intelligence.query(category, limit)
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from threading import Lock

SHARED_DIR = Path('/Users/saiful/temuclaude/research/shared_state')
SHARED_DIR.mkdir(parents=True, exist_ok=True)

EVENTS_FILE = SHARED_DIR / 'events.json'
STATE_FILE = SHARED_DIR / 'swarm_state.json'
KNOWLEDGE_FILE = SHARED_DIR / 'knowledge.json'
INTELLIGENCE_FILE = SHARED_DIR / 'intelligence.json'

MAX_EVENTS = 200
MAX_KNOWLEDGE = 500

_lock = Lock()

def _read_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return default

def _write_json(path, data):
    tmp = str(path) + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)

def broadcast(daemon, event_type, message, extra=None):
    """Broadcast an event to all daemons. Everyone sees this."""
    with _lock:
        events = _read_json(EVENTS_FILE, {'events': []})
        event = {
            'id': f'evt_{int(time.time()*1000)}_{daemon}',
            'timestamp': datetime.now().isoformat(),
            'daemon': daemon,
            'type': event_type,
            'message': message,
            'extra': extra or {},
        }
        events['events'].append(event)
        events['events'] = events['events'][-MAX_EVENTS:]
        events['last_update'] = datetime.now().isoformat()
        _write_json(EVENTS_FILE, events)
    return event['id']

def update_state(daemon, status, extra=None):
    """Update a daemon's state in the swarm registry. All daemons see who's alive."""
    with _lock:
        state = _read_json(STATE_FILE, {'daemons': {}, 'last_update': ''})
        state['daemons'][daemon] = {
            'status': status,
            'last_seen': datetime.now().isoformat(),
            'extra': extra or {},
        }
        state['alive_count'] = sum(1 for d in state['daemons'].values() if d['status'] != 'stopped')
        state['last_update'] = datetime.now().isoformat()
        _write_json(STATE_FILE, state)

def learn(key, value, daemon='system', category='general'):
    """Store a permanent shared fact. All daemons can query this."""
    with _lock:
        knowledge = _read_json(KNOWLEDGE_FILE, {'facts': {}})
        knowledge['facts'][key] = {
            'value': value,
            'daemon': daemon,
            'category': category,
            'timestamp': datetime.now().isoformat(),
        }
        # Cap knowledge to prevent unbounded growth
        if len(knowledge['facts']) > MAX_KNOWLEDGE:
            # Remove oldest entries
            sorted_facts = sorted(knowledge['facts'].items(), 
                key=lambda x: x[1].get('timestamp', ''), reverse=True)
            knowledge['facts'] = dict(sorted_facts[:MAX_KNOWLEDGE])
        knowledge['last_update'] = datetime.now().isoformat()
        _write_json(KNOWLEDGE_FILE, knowledge)

def query(category=None, limit=50):
    """Query shared knowledge. Optionally filter by category."""
    knowledge = _read_json(KNOWLEDGE_FILE, {'facts': {}})
    facts = knowledge.get('facts', {})
    if category:
        facts = {k: v for k, v in facts.items() if v.get('category') == category}
    return dict(list(facts.items())[-limit:])

def get_events(limit=50, daemon=None, event_type=None):
    """Get recent events. All daemons can see what others did."""
    events = _read_json(EVENTS_FILE, {'events': []})
    evts = events.get('events', [])
    if daemon:
        evts = [e for e in evts if e.get('daemon') == daemon]
    if event_type:
        evts = [e for e in evts if e.get('type') == event_type]
    return evts[-limit:]

def get_swarm_state():
    """Get the current swarm state — who's alive and what they're doing."""
    return _read_json(STATE_FILE, {'daemons': {}, 'alive_count': 0})

def get_intelligence_summary():
    """Get a compact summary of everything the swarm knows right now."""
    state = get_swarm_state()
    events = get_events(limit=20)
    knowledge = query()
    return {
        'swarm': {
            'alive_count': state.get('alive_count', 0),
            'daemons': list(state.get('daemons', {}).keys()),
        },
        'recent_events': [
            {'daemon': e.get('daemon'), 'type': e.get('type'), 'message': e.get('message', '')[:100]}
            for e in events
        ],
        'knowledge_count': len(knowledge),
        'knowledge_keys': list(knowledge.keys())[:30],
    }

def init():
    """Initialize the shared intelligence files."""
    for f, default in [(EVENTS_FILE, {'events': []}), (STATE_FILE, {'daemons': {}}), (KNOWLEDGE_FILE, {'facts': {}})]:
        if not f.exists():
            _write_json(f, default)
    
    # Store the intelligence summary for the API to read
    summary = get_intelligence_summary()
    _write_json(INTELLIGENCE_FILE, summary)
    
    # Broadcast initialization
    broadcast('watchdog', 'system', 'Shared intelligence hub initialized')

if __name__ == '__main__':
    init()
    print("Shared intelligence hub initialized.")
    print(f"  Events: {len(get_events())}")
    print(f"  Knowledge: {len(query())} facts")
    print(f"  Swarm state: {get_swarm_state().get('alive_count', 0)} daemons")