#!/bin/bash
# Temuclaude Master Controller — one command for the entire autonomous system
# Usage: bash master_control.sh start|stop|status|restart

ACTION="${1:-status}"
DAEMON_DIR="${RESEARCH_DIR:-/Users/saiful/temuclaude/research}"

case "$ACTION" in
    start)
        echo "Starting Temuclaude autonomous system..."
        bash "$DAEMON_DIR/scripts/start_swarm.sh"
        ;;
    stop)
        echo "Stopping Temuclaude autonomous system..."
        bash "$DAEMON_DIR/scripts/stop_swarm.sh"
        ;;
    status)
        echo "=== DAEMON STATUS ==="
        bash "$DAEMON_DIR/scripts/status_swarm.sh"
        echo ""
        echo "=== SHARED MEMORY ==="
        cd "${TEMUCLAUDE_DIR:-/Users/saiful/temuclaude}"
        python3 -c "
import sys; sys.path.insert(0, 'research')
from shared_memory import read_all_states, get_recent_events
states = read_all_states().get('daemons', {})
print(f'Active daemons in shared memory: {len(states)}')
for name, state in sorted(states.items()):
    print(f'  {name}: {state.get(\"status\", \"?\")} @ {state.get(\"timestamp\", \"?\")[:19]}')
events = get_recent_events(5)
if events:
    print(f'\\nRecent events:')
    for e in events:
        print(f'  [{e[\"type\"]}] {e[\"daemon\"]}: {e[\"message\"][:80]}')
" 2>/dev/null || echo "  (shared memory not available)"
        echo ""
        echo "=== UNLIMITED MEMORY ==="
        python3 -c "
import sys; sys.path.insert(0, 'research')
from unlimited_memory import get_stats
stats = get_stats()
print(f'Total memories: {stats[\"total_memories\"]}')
for cat, count in stats.get('by_category', {}).items():
    print(f'  {cat}: {count}')
" 2>/dev/null || echo "  (unlimited memory not available)"
        ;;
    restart)
        bash "$0" stop
        sleep 3
        bash "$0" start
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        exit 1
        ;;
esac