#!/bin/bash
# Start the complete Temuclaude Research Swarm
# Run from /Users/saiful/temuclaude

set -e

TEMUCLAUDE_DIR="/Users/saiful/temuclaude"
RESEARCH_DIR="$TEMUCLAUDE_DIR/research"
STATE_DIR="/tmp/temuclaude_daemons"

echo "=== Starting Temuclaude Research Swarm ==="
echo "Time: $(date)"
echo ""

# Create state directory
mkdir -p "$STATE_DIR"
mkdir -p "$RESEARCH_DIR/raw"
mkdir -p "$RESEARCH_DIR/findings"

# Kill any existing daemons first
echo "Stopping any existing daemons..."
for pidfile in "$STATE_DIR"/*.pid; do
    if [ -f "$pidfile" ]; then
        pid=$(cat "$pidfile" 2>/dev/null)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo "  Killing $pid ($pidfile)"
            kill -TERM "$pid" 2>/dev/null
            sleep 1
            kill -KILL "$pid" 2>/dev/null || true
        fi
    fi
done

# Clear PID files
rm -f "$STATE_DIR"/*.pid "$STATE_DIR"/*_heartbeat.json

# Disable cron jobs to avoid conflicts
echo "Disabling conflicting cron jobs..."
cd "$RESEARCH_DIR"
# We'll just note this - user should disable cron manually if needed

# Start daemons in order
echo ""
echo "Starting daemons..."

# 1. Scout Daemon (runs every 6h)
echo "  1/10 Starting scout_daemon... (arXiv + GitHub + HuggingFace, with cyber + efficiency + media queries)"
cd "$RESEARCH_DIR"
nohup python3 scout_daemon.py > "$STATE_DIR/scout_daemon.log" 2>&1 &
sleep 2

# 2. Distiller Daemon (polls every 30s)
echo "  2/10 Starting distiller_daemon... (with cyber + efficiency + media keyword filtering)"
nohup python3 distiller_daemon.py > "$STATE_DIR/distiller_daemon.log" 2>&1 &
sleep 2

# 3-5. Research Daemons (3 parallel)
for i in 1 2 3; do
    echo "  $((2+i))/10 Starting research_daemon_$i... (orchestration/reasoning)"
    nohup python3 research_daemon.py --id $i > "$STATE_DIR/research_daemon_$i.log" 2>&1 &
    sleep 1
done

# 6. Cyber Research Daemon (runs every 5min) — Added 2026-07-06
echo "  6/10 Starting cyber_daemon... (cybersecurity research + Red-Blue loop)"
nohup python3 cyber_daemon.py > "$STATE_DIR/cyber_daemon.log" 2>&1 &
sleep 2

# 7. Efficiency Research Daemon (runs every 5min) — Added 2026-07-06
echo "  7/10 Starting efficiency_daemon... (lossless cost reduction + quality guardrail)"
nohup python3 efficiency_daemon.py > "$STATE_DIR/efficiency_daemon.log" 2>&1 &
sleep 2

# 8. Media Research Daemon (runs every 5min) — Added 2026-07-06
echo "  8/10 Starting media_daemon... (beat frontier image/video generation)"
nohup python3 media_daemon.py > "$STATE_DIR/media_daemon.log" 2>&1 &
sleep 2

# 9. Integrator Daemon (checks every 2min)
echo "  9/10 Starting integrator_daemon... (auto-implements findings)"
nohup python3 integrator_daemon.py > "$STATE_DIR/integrator_daemon.log" 2>&1 &
sleep 2

# 10. Coordinator Daemon (checks every 60s)
echo "  10/10 Starting coordinator_daemon... (self-healing, manages all 10 daemons)"
nohup python3 coordinator_daemon.py > "$STATE_DIR/coordinator_daemon.log" 2>&1 &
sleep 3

echo ""
echo "=== All daemons started ==="
echo ""
echo "PIDs:"
for pidfile in "$STATE_DIR"/*.pid; do
    if [ -f "$pidfile" ]; then
        name=$(basename "$pidfile" .pid)
        pid=$(cat "$pidfile")
        echo "  $name: $pid"
    fi
done

echo ""
echo "Logs in: $STATE_DIR/"
echo "Monitor with: $RESEARCH_DIR/scripts/status_swarm.sh"
echo ""
echo "Swarm is now running 24/7 continuous improvement loop!"
echo "  - 7 orchestration/reasoning daemons (existing)"
echo "  - 1 cybersecurity daemon (researches defenses 24/7)"
echo "  - 1 efficiency daemon (researches lossless cost reduction 24/7)"
echo "  - 1 media daemon (researches how to beat frontier image/video models 24/7)"
echo "  - Scouts search cyber + efficiency + media queries on arXiv/GitHub/HuggingFace"
echo "  - Priority engine tracks 15+ cyber + 14 efficiency + 17 media techniques"
echo "  - Coordinator auto-restarts all 10 daemons (self-healing)"
echo "  - QUALITY GUARDRAIL: efficiency must be LOSSLESS or QUALITY-PRESERVING"
echo "  - MISSION: Always beat frontier media generation via orchestration"