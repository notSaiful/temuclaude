# Shared Intelligence Hub

## File
`research/share_intelligence.py`

## Overview
A unified intelligence layer that ALL daemons, the watchdog, and Hasan's chat read from and write to. This ensures every component in the system has the same knowledge.

## Three Layers

### 1. Events Bus (`shared_state/events.json`)
- Real-time event bus — last 200 events
- All daemons see what every other daemon did
- Events have: id, timestamp, daemon, type, message, extra
- Use `si.broadcast(daemon, type, message)` to post

### 2. Swarm State (`shared_state/swarm_state.json`)
- Live daemon registry — who's alive and what they're doing
- Updated by watchdog every 15s on health check
- Use `si.update_state(daemon, status, extra)` to update

### 3. Knowledge Store (`shared_state/knowledge.json`)
- Permanent shared facts — what the swarm learned
- Capped at 500 entries (oldest pruned)
- Use `si.learn(key, value, daemon, category)` to store
- Use `si.query(category, limit)` to retrieve

## API

```python
import share_intelligence as si

# Broadcast an event to all daemons
si.broadcast('watchdog', 'restart', 'cyber_daemon restarted after crash')

# Update swarm state
si.update_state('cyber_daemon', 'alive', {'pid': 12345})

# Store a permanent fact
si.learn('best_model', 'glm-5.2', daemon='model_optimizer', category='models')

# Query shared knowledge
facts = si.query(category='models', limit=10)

# Get recent events
events = si.get_events(limit=20, daemon='cyber_daemon')

# Get swarm state
state = si.get_swarm_state()

# Get compact summary (used by chat)
summary = si.get_intelligence_summary()

# Initialize all files (called by watchdog on startup)
si.init()
```

## Chat Integration
`gatherSharedIntelligence()` in `website/app/api/hasan/chat/route.ts` reads all 3 layers at request time and injects them into the system prompt. This means Hasan sees:
- What every daemon recently did (last 15 events)
- How many daemons are alive (swarm state)
- What the swarm has learned (last 10 knowledge facts)
- Watchdog status (heartbeat)

## Watchdog Integration
`research/watchdog.py` imports `share_intelligence` and:
- Calls `si.init()` on startup (creates files if missing)
- Calls `si.update_state(name, 'alive', {pid})` for each healthy daemon
- Calls `si.broadcast('watchdog', 'restart', ...)` when restarting a daemon
- Calls `si.learn('swarm_health', {...})` after each health check cycle

## Auto-Start
`start_swarm.sh` starts the shared intelligence hub alongside the 23 daemons:
```bash
python3 "$RESEARCH_DIR/share_intelligence.py" > /dev/null 2>&1 &
```

The watchdog also calls `si.init()` on its own startup, so the hub is always initialized even if start_swarm.sh doesn't run it.

## Thread Safety
Uses a `threading.Lock()` for all read/write operations. Safe for concurrent access from multiple daemons.

## File Locations
```
research/shared_state/
├── events.json          # Event bus (last 200)
├── swarm_state.json     # Daemon registry
├── knowledge.json       # Permanent facts (max 500)
└── intelligence.json    # Compact summary (for API)
```