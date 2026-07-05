#!/bin/bash
# Stop the Temuclaude Research Swarm

set -e

STATE_DIR="/tmp/temuclaude_daemons"

echo "=== Stopping Temuclaude Research Swarm ==="
echo "Time: $(date)"
echo ""

if [ ! -d "$STATE_DIR" ]; then
    echo "No daemon state directory found."
    exit 0
fi

for pidfile in "$STATE_DIR"/*.pid; do
    if [ -f "$pidfile" ]; then
        name=$(basename "$pidfile" .pid)
        pid=$(cat "$pidfile" 2>/dev/null)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "Stopping $name (PID: $pid)..."
            kill -TERM "$pid" 2>/dev/null
            sleep 1
            if kill -0 "$pid" 2>/dev/null; then
                echo "  Force killing..."
                kill -KILL "$pid" 2>/dev/null
            fi
        else
            echo "$name: not running"
        fi
    fi
done

# Clean up PID files
rm -f "$STATE_DIR"/*.pid "$STATE_DIR"/*_heartbeat.json

echo ""
echo "=== Swarm stopped ==="