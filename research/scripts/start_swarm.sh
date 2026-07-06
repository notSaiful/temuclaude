#!/bin/bash
# Start the complete Temuclaude Autonomous Swarm (23 daemons)
# Run from /Users/saiful/temuclaude

set -e

TEMUCLAUDE_DIR="${TEMUCLAUDE_DIR:-/Users/saiful/temuclaude}"
RESEARCH_DIR="$TEMUCLAUDE_DIR/research"
STATE_DIR="${DAEMON_STATE_DIR:-/tmp/temuclaude_daemons}"

echo "=== Starting Temuclaude Autonomous Swarm (23 daemons) ==="
echo "Time: $(date)"
echo ""

# Create state and output directories
mkdir -p "$STATE_DIR" "$RESEARCH_DIR/raw" "$RESEARCH_DIR/findings"
mkdir -p "$RESEARCH_DIR/shared_state" "$RESEARCH_DIR/memory_store"
mkdir -p "$RESEARCH_DIR/audit_reports" "$RESEARCH_DIR/swot_reports"
mkdir -p "$RESEARCH_DIR/radar_reports" "$RESEARCH_DIR/cost_reports"
mkdir -p "$RESEARCH_DIR/model_optimization_reports"

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

# Wait for all processes to fully exit
sleep 3

# Force-clear ALL state files
rm -f "$STATE_DIR"/*.pid "$STATE_DIR"/*_heartbeat.json 2>/dev/null || true

# Verify clear
remaining=$(ls "$STATE_DIR"/*.pid 2>/dev/null | wc -l)
if [ "$remaining" -gt 0 ]; then
    echo "WARNING: $remaining PID files still exist, force removing..."
    rm -f "$STATE_DIR"/*.pid 2>/dev/null || true
fi

# Start all 23 daemons
cd "$RESEARCH_DIR"
count=0

start_daemon() {
    local name=$1
    local script=$2
    local desc=$3
    count=$((count + 1))
    echo "  $count/23 Starting $name... ($desc)"
    if [ -f "$RESEARCH_DIR/$script" ]; then
        nohup python3 "$RESEARCH_DIR/$script" > "$STATE_DIR/$name.log" 2>&1 &
        sleep 1
    else
        echo "    WARNING: $script not found, skipping"
    fi
}

start_daemon_with_id() {
    local name=$1
    local script=$2
    local id=$3
    local desc=$4
    count=$((count + 1))
    echo "  $count/23 Starting $name... ($desc)"
    if [ -f "$RESEARCH_DIR/$script" ]; then
        nohup python3 "$RESEARCH_DIR/$script" --id "$id" > "$STATE_DIR/$name.log" 2>&1 &
        sleep 1
    else
        echo "    WARNING: $script not found, skipping"
    fi
}

# Core research pipeline
start_daemon "scout_daemon" "scout_daemon.py" "arXiv + GitHub + HuggingFace discovery"
start_daemon "distiller_daemon" "distiller_daemon.py" "score and dedupe findings"
start_daemon_with_id "research_daemon_1" "research_daemon.py" "1" "deep research worker 1"
start_daemon_with_id "research_daemon_2" "research_daemon.py" "2" "deep research worker 2"
start_daemon_with_id "research_daemon_3" "research_daemon.py" "3" "deep research worker 3"
start_daemon "integrator_daemon" "integrator_daemon.py" "auto-implements findings + tests + commits"
start_daemon "coordinator_daemon" "coordinator_daemon.py" "self-healing, manages all daemons"

# Domain research
start_daemon "cyber_daemon" "cyber_daemon.py" "cybersecurity research"
start_daemon "efficiency_daemon" "efficiency_daemon.py" "lossless cost reduction"
start_daemon "media_daemon" "media_daemon.py" "beat frontier media generation"

# Self-improvement layer
start_daemon "feedback_daemon" "feedback_daemon.py" "evaluates swarm performance"
start_daemon "meta_auditor_daemon" "meta_auditor_daemon.py" "7-layer audit + autonomous fix"
start_daemon "swot_daemon" "swot_daemon.py" "strategic SWOT analysis"
start_daemon "super_intelligence_daemon" "super_intelligence_daemon.py" "evolutionary prompt optimization"
start_daemon "self_expansion_daemon" "self_expansion_daemon.py" "auto-creates new daemons for gaps"

# Industry awareness
start_daemon "industry_radar_daemon" "industry_radar_daemon.py" "monitors 6+ industry sources"
start_daemon "model_optimizer_daemon" "model_optimizer_daemon.py" "benchmarks and swaps better models"

# Cost management
start_daemon "cost_efficiency_daemon" "cost_efficiency_daemon.py" "credit ROI + throttle + budgets"

# Marketing and growth
start_daemon "marketing_daemon" "marketing_daemon.py" "generates fresh tweet content"
start_daemon "growth_daemon" "growth_daemon.py" "SEO content + user acquisition"
start_daemon "competitive_dominance_daemon" "competitive_dominance_daemon.py" "benchmarks vs competitors"

# Revenue
start_daemon "revenue_daemon" "revenue_daemon.py" "tracks income + Ummah fund routing"

# Website
start_daemon "website_daemon" "website_daemon.py" "auto-updates website + Vercel deploy"

echo ""
echo "=== All 23 daemons started ==="
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
echo "Master control: bash $RESEARCH_DIR/scripts/master_control.sh status"
echo ""
echo "Swarm is now running 24/7 autonomous improvement loop!"
echo "  - 23 daemons: research, implementation, security, marketing,"
echo "    revenue, cost management, competitive dominance, self-expansion,"
echo "    super intelligence, Ummah fund routing"
echo "  - Shared memory bus: all daemons aware of each other"
echo "  - Unlimited memory: permanent knowledge base"
echo "  - 25% of profit -> Ummah fund (Palestine food relief, clinics, schools)"