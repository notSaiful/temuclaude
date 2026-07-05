#!/usr/bin/env python3
"""
Live Dashboard for Temuclaude Research Swarm
Shows real-time status of all daemons, queues, and pipeline.
"""

import json
import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from flask import Flask, render_template_string, jsonify, request

app = Flask(__name__)

RESEARCH_DIR = Path("/Users/saiful/temuclaude/research")
STATE_DIR = Path("/tmp/temuclaude_daemons")

DAEMONS = [
    "scout_daemon", "distiller_daemon",
    "research_daemon_1", "research_daemon_2", "research_daemon_3",
    "integrator_daemon", "coordinator_daemon"
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Temuclaude Research Swarm - Live Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #e6edf3; line-height: 1.5; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid #30363d; }
        h1 { font-size: 1.5rem; font-weight: 600; }
        .status-indicator { display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px; border-radius: 6px; font-weight: 500; }
        .status-indicator.running { background: #1f6feb; }
        .status-indicator.stopped { background: #da3633; }
        .dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
        .dot.alive { color: #3fb950; }
        .dot.dead { color: #f85149; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); gap: 16px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }
        .card h2 { font-size: 0.875rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #8b949e; margin-bottom: 12px; }
        .daemon-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #21262d; }
        .daemon-row:last-child { border-bottom: none; }
        .daemon-info { display: flex; flex-direction: column; gap: 2px; }
        .daemon-name { font-weight: 500; font-size: 0.9rem; }
        .daemon-meta { font-size: 0.75rem; color: #8b949e; }
        .queue-item { display: flex; justify-content: space-between; padding: 8px 0; font-family: monospace; font-size: 0.85rem; }
        .queue-name { color: #8b949e; }
        .queue-count { font-weight: 600; color: #f0883e; }
        .queue-count.zero { color: #3fb950; }
        .file-list { font-family: monospace; font-size: 0.8rem; color: #8b949e; }
        .file-list li { padding: 4px 0; }
        .priority-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #21262d; }
        .priority-item:last-child { border-bottom: none; }
        .priority-name { font-weight: 500; }
        .priority-score { color: #f0883e; font-weight: 600; }
        .priority-action { font-size: 0.75rem; color: #8b949e; }
        .metrics-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
        .metric { background: #21262d; padding: 12px; border-radius: 6px; }
        .metric-label { font-size: 0.75rem; color: #8b949e; text-transform: uppercase; }
        .metric-value { font-size: 1.25rem; font-weight: 600; }
        .last-updated { font-size: 0.75rem; color: #8b949e; text-align: right; margin-top: 16px; }
        .pulse { animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 Temuclaude Research Swarm</h1>
            <div class="status-indicator running">
                <span class="dot alive pulse"></span>
                <span id="system-status">LIVE</span>
            </div>
        </header>
        
        <div class="grid">
            <!-- Daemons -->
            <div class="card">
                <h2>Daemons (7)</h2>
                <div id="daemons"></div>
            </div>
            
            <!-- Queue -->
            <div class="card">
                <h2>Pipeline Queues</h2>
                <div id="queues"></div>
            </div>
            
            <!-- Files -->
            <div class="card">
                <h2>Files</h2>
                <div style="display: grid; gap: 12px;">
                    <div>
                        <div style="font-weight: 500; margin-bottom: 8px; color: #f0883e;">Raw (unprocessed)</div>
                        <ul class="file-list" id="raw-files"></ul>
                    </div>
                    <div>
                        <div style="font-weight: 500; margin-bottom: 8px; color: #58a6ff;">Distilled Findings</div>
                        <ul class="file-list" id="distilled-files"></ul>
                    </div>
                    <div>
                        <div style="font-weight: 500; margin-bottom: 8px; color: #a371f7;">Deep Research</div>
                        <ul class="file-list" id="deep-files"></ul>
                    </div>
                </div>
            </div>
            
            <!-- Git -->
            <div class="card">
                <h2>Git Status</h2>
                <div id="git-status"></div>
            </div>
            
            <!-- Priorities -->
            <div class="card">
                <h2>Current Priorities</h2>
                <div id="priorities"></div>
            </div>
            
            <!-- Metrics -->
            <div class="card">
                <h2>Metrics</h2>
                <div class="metrics-grid" id="metrics"></div>
            </div>
        </div>
        
        <div class="last-updated">
            Last updated: <span id="last-updated">--</span> | Auto-refresh: 5s
        </div>
    </div>

    <script>
        async function fetchData() {
            try {
                const res = await fetch('/api/status');
                return await res.json();
            } catch (e) {
                console.error(e);
                return null;
            }
        }

        function renderDaemons(data) {
            const container = document.getElementById('daemons');
            container.innerHTML = data.daemons.map(d => `
                <div class="daemon-row">
                    <div class="daemon-info">
                        <span class="daemon-name">${d.name}</span>
                        <span class="daemon-meta">PID: ${d.pid || '—'} • ${d.status} • HB: ${d.heartbeat_age || '?'}</span>
                    </div>
                    <span class="dot ${d.alive ? 'alive' : 'dead'}"></span>
                </div>
            `).join('');
        }

        function renderQueues(data) {
            const container = document.getElementById('queues');
            container.innerHTML = Object.entries(data.queues).map(([name, count]) => `
                <div class="queue-item">
                    <span class="queue-name">${name}</span>
                    <span class="queue-count ${count === 0 ? 'zero' : ''}">${count}</span>
                </div>
            `).join('');
        }

        function renderFiles(data) {
            document.getElementById('raw-files').innerHTML = data.files.raw.map(f => `<li>${f}</li>`).join('');
            document.getElementById('distilled-files').innerHTML = data.files.distilled.map(f => `<li>${f}</li>`).join('');
            document.getElementById('deep-files').innerHTML = data.files.deep.map(f => `<li>${f}</li>`).join('');
        }

        function renderGit(data) {
            const container = document.getElementById('git-status');
            container.innerHTML = `
                <div class="queue-item"><span class="queue-name">Uncommitted changes</span><span class="queue-count">${data.git.changes}</span></div>
                <div class="queue-item"><span class="queue-name">Last commit</span><span class="queue-count" style="font-weight: 400; font-size: 0.8rem;">${data.git.last_commit}</span></div>
            `;
        }

        function renderPriorities(data) {
            const container = document.getElementById('priorities');
            if (!data.priorities || data.priorities.length === 0) {
                container.innerHTML = '<div style="color: #8b949e;">No priorities available</div>';
                return;
            }
            container.innerHTML = data.priorities.map(p => `
                <div class="priority-item">
                    <div>
                        <div class="priority-name">${p.name}</div>
                        <div class="priority-action">${p.action}</div>
                    </div>
                    <span class="priority-score">${p.score}</span>
                </div>
            `).join('');
        }

        function renderMetrics(data) {
            const container = document.getElementById('metrics');
            const m = data.metrics;
            container.innerHTML = `
                <div class="metric"><div class="metric-label">Daemons Up</div><div class="metric-value">${m.daemons_up}/${m.daemons_total}</div></div>
                <div class="metric"><div class="metric-label">Queue Items</div><div class="metric-value">${m.total_queue}</div></div>
                <div class="metric"><div class="metric-label">Raw Files</div><div class="metric-value">${m.raw_files}</div></div>
                <div class="metric"><div class="metric-label">Deep Reports</div><div class="metric-value">${m.deep_reports}</div></div>
            `;
        }

        async function update() {
            const data = await fetchData();
            if (!data) return;
            
            renderDaemons(data);
            renderQueues(data);
            renderFiles(data);
            renderGit(data);
            renderPriorities(data);
            renderMetrics(data);
            
            document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
            document.getElementById('system-status').textContent = data.daemons.every(d => d.alive) ? 'ALL SYSTEMS GO' : 'DEGRADED';
        }

        update();
        setInterval(update, 5000);
    </script>
</body>
</html>
"""

def get_daemon_status():
    statuses = []
    for name in DAEMONS:
        pid_file = STATE_DIR / f"{name}.pid"
        hb_file = STATE_DIR / f"{name}_heartbeat.json"
        
        alive = False
        pid = None
        status = "unknown"
        heartbeat_age = "?"
        
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                os.kill(pid, 0)
                alive = True
            except (ValueError, OSError, ProcessLookupError):
                alive = False
        
        if hb_file.exists():
            try:
                hb = json.loads(hb_file.read_text())
                status = hb.get("status", "?")
                hb_time = datetime.fromisoformat(hb["timestamp"].replace('Z', '+00:00'))
                age = int(time.time() - hb_time.timestamp())
                if age < 60:
                    heartbeat_age = f"{age}s"
                elif age < 3600:
                    heartbeat_age = f"{age//60}m"
                else:
                    heartbeat_age = f"{age//3600}h"
            except Exception:
                pass
        
        statuses.append({
            "name": name,
            "pid": pid,
            "alive": alive,
            "status": status,
            "heartbeat_age": heartbeat_age
        })
    return statuses

def get_queue_status():
    try:
        sys.path.insert(0, str(RESEARCH_DIR))
        from queue import QueueManager
        qm = QueueManager()
        q = qm.get_all()
        return {k: len(v) if isinstance(v, list) else 0 for k, v in q.items() if k != 'last_updated'}
    except Exception:
        return {}

def get_files():
    raw = sorted([f.name for f in RESEARCH_DIR.glob("raw/*.json") if not f.name.startswith("_")], reverse=True)
    distilled = sorted([f.name for f in RESEARCH_DIR.glob("findings/distilled_*.json")], reverse=True)
    deep = sorted([f.name for f in RESEARCH_DIR.glob("findings/deep_research_*.md")], reverse=True)
    return {"raw": raw[:10], "distilled": distilled[:10], "deep": deep[:10]}

def get_git_status():
    try:
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd="/Users/saiful/temuclaude")
        changes = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        commit = subprocess.run(["git", "log", "-1", "--format=%h %s (%cr)"], capture_output=True, text=True, cwd="/Users/saiful/temuclaude")
        last_commit = commit.stdout.strip() if commit.stdout else "none"
        return {"changes": changes, "last_commit": last_commit}
    except Exception:
        return {"changes": 0, "last_commit": "error"}

def get_priorities():
    try:
        sys.path.insert(0, str(RESEARCH_DIR))
        from dynamic_priorities import get_top_research_priorities
        priorities = get_top_research_priorities(10)
        return [{"name": name, "score": info["priority_score"], "action": info["action"]} for name, info in priorities]
    except Exception:
        return []

def get_metrics(data):
    daemons = data["daemons"]
    queues = data["queues"]
    files = data["files"]
    return {
        "daemons_up": sum(1 for d in daemons if d["alive"]),
        "daemons_total": len(daemons),
        "total_queue": sum(queues.values()),
        "raw_files": len(files["raw"]),
        "deep_reports": len(files["deep"])
    }

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/status")
def api_status():
    daemons = get_daemon_status()
    queues = get_queue_status()
    files = get_files()
    git = get_git_status()
    priorities = get_priorities()
    metrics = get_metrics({"daemons": daemons, "queues": queues, "files": files})
    
    return jsonify({
        "daemons": daemons,
        "queues": queues,
        "files": files,
        "git": git,
        "priorities": priorities,
        "metrics": metrics,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False, threaded=True)