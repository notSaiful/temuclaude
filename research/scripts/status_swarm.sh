#!/bin/bash
# Status dashboard for Temuclaude Research Swarm

set -e

STATE_DIR="/tmp/temuclaude_daemons"
RESEARCH_DIR="/Users/saiful/temuclaude/research"

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║     TEMUCLAUDE RESEARCH SWARM - STATUS DASHBOARD                    ║"
echo "╠══════════════════════════════════════════════════════════════════════╣"
echo "║ Time: $(date)                                  ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Daemon status
echo "┌─ DAEMONS ────────────────────────────────────────────────────────────┐"
printf "│ %-20s │ %-8s │ %-6s │ %-10s │ %s │\n" "NAME" "PID" "ALIVE" "STATUS" "HEARTBEAT AGE"
echo "├──────────────────────┼──────────┼────────┼────────────┼────────────────┤"

daemons=("scout_daemon" "distiller_daemon" "research_daemon_1" "research_daemon_2" "research_daemon_3" "integrator_daemon" "coordinator_daemon" "cyber_daemon" "efficiency_daemon" "media_daemon")

for name in "${daemons[@]}"; do
    pidfile="$STATE_DIR/$name.pid"
    hbfile="$STATE_DIR/${name}_heartbeat.json"
    
    if [ -f "$pidfile" ]; then
        pid=$(cat "$pidfile" 2>/dev/null)
        if kill -0 "$pid" 2>/dev/null; then
            alive="YES"
        else
            alive="NO (dead)"
        fi
    else
        pid="-"
        alive="NO (no pid)"
    fi
    
    if [ -f "$hbfile" ]; then
        status=$(python3 -c "import json, sys; d=json.load(open('$hbfile')); print(d.get('status', '?'))" 2>/dev/null || echo "?")
        hb_time=$(python3 -c "import json, sys; d=json.load(open('$hbfile')); print(d.get('timestamp', ''))" 2>/dev/null || echo "")
        if [ -n "$hb_time" ]; then
            hb_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${hb_time%.*}" +%s 2>/dev/null || date -d "${hb_time%.*}" +%s 2>/dev/null || echo 0)
            now=$(date +%s)
            age=$((now - hb_epoch))
            if [ $age -lt 60 ]; then
                hb_age="${age}s"
            elif [ $age -lt 3600 ]; then
                hb_age="$((age/60))m"
            else
                hb_age="$((age/3600))h"
            fi
        else
            hb_age="?"
        fi
    else
        status="?"
        hb_age="?"
    fi
    
    printf "│ %-20s │ %-8s │ %-6s │ %-10s │ %s │\n" "$name" "$pid" "$alive" "$status" "$hb_age"
done

echo "└──────────────────────────────────────────────────────────────────────┘"
echo ""

# Queue status
echo "┌─ QUEUE STATUS ───────────────────────────────────────────────────────┐"
python3 -c "
import sys
sys.path.insert(0, '$RESEARCH_DIR')
from queue import QueueManager
qm = QueueManager()
q = qm.get_all()
for k, v in q.items():
    if isinstance(v, list) and v:
        print(f'│ {k}: {len(v)} items')
    elif k != 'last_updated':
        print(f'│ {k}: empty')
" 2>/dev/null || echo "│ Queue not accessible"
echo "└──────────────────────────────────────────────────────────────────────┘"
echo ""

# Raw files
echo "┌─ RAW FILES (unprocessed) ────────────────────────────────────────────┤"
raw_count=$(ls -1 "$RESEARCH_DIR/raw"/*.json 2>/dev/null | wc -l | tr -d ' ')
echo "│ Count: $raw_count"
ls -1t "$RESEARCH_DIR/raw"/*.json 2>/dev/null | head -5 | while read f; do
    echo "│   $(basename "$f")"
done
echo "└──────────────────────────────────────────────────────────────────────┘"
echo ""

# Findings
echo "┌─ DISTILLED FINDINGS ─────────────────────────────────────────────────┤"
find_count=$(ls -1 "$RESEARCH_DIR/findings"/distilled_*.json 2>/dev/null | wc -l | tr -d ' ')
echo "│ Count: $find_count"
ls -1t "$RESEARCH_DIR/findings"/distilled_*.json 2>/dev/null | head -3 | while read f; do
    echo "│   $(basename "$f")"
done
echo "└──────────────────────────────────────────────────────────────────────┘"
echo ""

# Deep research
echo "┌─ DEEP RESEARCH REPORTS ──────────────────────────────────────────────┤"
deep_count=$(ls -1 "$RESEARCH_DIR/findings"/deep_research_*.md 2>/dev/null | wc -l | tr -d ' ')
echo "│ Count: $deep_count"
ls -1t "$RESEARCH_DIR/findings"/deep_research_*.md 2>/dev/null | head -3 | while read f; do
    echo "│   $(basename "$f")"
done
echo "└──────────────────────────────────────────────────────────────────────┘"
echo ""

# Git status
echo "┌─ GIT STATUS ─────────────────────────────────────────────────────────┤"
cd /Users/saiful/temuclaude
git_status=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
echo "│ Uncommitted changes: $git_status"
if [ "$git_status" -gt 0 ]; then
    git status --porcelain | head -5 | while read line; do
        echo "│   $line"
    done
fi
last_commit=$(git log -1 --format="%h %s (%cr)" 2>/dev/null)
echo "│ Last commit: $last_commit"
echo "└──────────────────────────────────────────────────────────────────────┘"
echo ""

# Priorities
echo "┌─ CURRENT PRIORITIES ─────────────────────────────────────────────────┤"
python3 -c "
import sys
sys.path.insert(0, '$RESEARCH_DIR')
from dynamic_priorities import get_top_research_priorities
p = get_top_research_priorities(5)
for i, (name, info) in enumerate(p, 1):
    print(f'│ {i}. {name} (score: {info[\"priority_score\"]}) - {info[\"action\"]}')
" 2>/dev/null || echo "│ Priorities not available"
echo "└──────────────────────────────────────────────────────────────────────┘"
echo ""

# Metrics
echo "┌─ METRICS ────────────────────────────────────────────────────────────┤"
metrics_file="$RESEARCH_DIR/daemon_metrics.json"
if [ -f "$metrics_file" ]; then
    python3 -c "
import json
with open('$metrics_file') as f:
    m = json.load(f)
print(f'│ Last update: {m.get(\"timestamp\", \"?\")}')
for name, info in m.get('daemons', {}).items():
    alive = 'UP' if info.get('alive') else 'DOWN'
    print(f'│ {name}: {alive}')
" 2>/dev/null
else
    echo "│ No metrics yet"
fi
echo "└──────────────────────────────────────────────────────────────────────┘"