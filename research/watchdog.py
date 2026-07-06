#!/usr/bin/env python3
"""
Hasan Self-Healing Watchdog
===========================
Continuously monitors all 23 daemons. If any daemon dies (stale PID, no heartbeat
for >120s, or process not found), it automatically restarts that daemon.

Runs as a separate background process alongside the swarm.
Logs all actions to /tmp/temuclaude_daemons/watchdog.log
"""

import os
import sys
import time
import json
import signal
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

STATE_DIR = Path('/tmp/temuclaude_daemons')
RESEARCH_DIR = Path('/Users/saiful/temuclaude/research')
TEMUCLAUDE_DIR = Path('/Users/saiful/temuclaude')

DAEMONS = [
    ('scout_daemon', 'scout_daemon.py', []),
    ('distiller_daemon', 'distiller_daemon.py', []),
    ('research_daemon_1', 'research_daemon.py', ['--id', '1']),
    ('research_daemon_2', 'research_daemon.py', ['--id', '2']),
    ('research_daemon_3', 'research_daemon.py', ['--id', '3']),
    ('integrator_daemon', 'integrator_daemon.py', []),
    ('coordinator_daemon', 'coordinator_daemon.py', []),
    ('cyber_daemon', 'cyber_daemon.py', []),
    ('efficiency_daemon', 'efficiency_daemon.py', []),
    ('media_daemon', 'media_daemon.py', []),
    ('marketing_daemon', 'marketing_daemon.py', []),
    ('feedback_daemon', 'feedback_daemon.py', []),
    ('meta_auditor_daemon', 'meta_auditor_daemon.py', []),
    ('swot_daemon', 'swot_daemon.py', []),
    ('super_intelligence_daemon', 'super_intelligence_daemon.py', []),
    ('self_expansion_daemon', 'self_expansion_daemon.py', []),
    ('industry_radar_daemon', 'industry_radar_daemon.py', []),
    ('model_optimizer_daemon', 'model_optimizer_daemon.py', []),
    ('cost_efficiency_daemon', 'cost_efficiency_daemon.py', []),
    ('revenue_daemon', 'revenue_daemon.py', []),
    ('growth_daemon', 'growth_daemon.py', []),
    ('competitive_dominance_daemon', 'competitive_dominance_daemon.py', []),
    ('website_daemon', 'website_daemon.py', []),
]

STALE_THRESHOLD = 120  # seconds without heartbeat = stale
RESTART_COOLDOWN = 30  # don't restart same daemon more than once per 30s
MAX_RESTARTS_PER_CYCLE = 3  # max restarts per check cycle
HEALTH_CHECK_INTERVAL = 15  # check every 15s

LOG_FILE = STATE_DIR / 'watchdog.log'
WATCHDOG_PID_FILE = STATE_DIR / 'watchdog.pid'
WATCHDOG_HEARTBEAT = STATE_DIR / 'watchdog_heartbeat.json'

# Track restart history
restart_history = {}  # daemon_name -> last_restart_timestamp

running = True

def log(level, msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"{ts} | watchdog | {level} | {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(line + '\n')
    except:
        pass

def write_heartbeat(status='running'):
    try:
        with open(WATCHDOG_HEARTBEAT, 'w') as f:
            json.dump({
                'daemon': 'watchdog',
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'pid': os.getpid(),
            }, f)
    except:
        pass

def is_process_alive(pid):
    """Check if a process is actually running."""
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False

def get_heartbeat_age(name):
    """Get age of heartbeat in seconds, or None if no heartbeat."""
    hb_file = STATE_DIR / f'{name}_heartbeat.json'
    try:
        with open(hb_file) as f:
            hb = json.load(f)
        ts = hb.get('timestamp')
        if not ts:
            return None
        dt = datetime.fromisoformat(ts)
        return (datetime.now() - dt).total_seconds()
    except:
        return None

def restart_daemon(name, script, args, reason):
    """Restart a single daemon."""
    now = time.time()
    last_restart = restart_history.get(name, 0)
    if now - last_restart < RESTART_COOLDOWN:
        log('INFO', f'{name}: restart skipped (cooldown, last was {int(now - last_restart)}s ago)')
        return False

    # Kill stale PID if exists and remove PID file + heartbeat
    pid_file = STATE_DIR / f'{name}.pid'
    if pid_file.exists():
        try:
            old_pid = int(pid_file.read_text().strip())
            if is_process_alive(old_pid):
                os.kill(old_pid, signal.SIGTERM)
                time.sleep(2)
                if is_process_alive(old_pid):
                    os.kill(old_pid, signal.SIGKILL)
        except:
            pass
    # Remove stale PID + heartbeat so daemon can start fresh
    pid_file.unlink(missing_ok=True)
    hb_file = STATE_DIR / f'{name}_heartbeat.json'
    hb_file.unlink(missing_ok=True)

    # Start the daemon
    script_path = RESEARCH_DIR / script
    if not script_path.exists():
        log('ERROR', f'{name}: script {script} not found, cannot restart')
        return False

    try:
        log_file = STATE_DIR / f'{name}.log'
        with open(log_file, 'a') as lf:
            proc = subprocess.Popen(
                ['python3', str(script_path)] + args,
                stdout=lf,
                stderr=subprocess.STDOUT,
                cwd=str(RESEARCH_DIR),
            )
        # Wait briefly for daemon to write its own PID file
        time.sleep(2)
        # Verify it started
        if pid_file.exists():
            new_pid = pid_file.read_text().strip()
            log('INFO', f'{name}: RESTARTED (pid {new_pid}, reason: {reason})')
        else:
            log('WARNING', f'{name}: started (pid {proc.pid}) but no PID file written yet — daemon may have exited')
        restart_history[name] = now
        return True
    except Exception as e:
        log('ERROR', f'{name}: restart FAILED ({e})')
        return False

def health_check():
    """Check all daemons and restart any that are dead or stale."""
    restarted = 0
    
    for name, script, args in DAEMONS:
        if restarted >= MAX_RESTARTS_PER_CYCLE:
            log('WARNING', f'Max restarts per cycle ({MAX_RESTARTS_PER_CYCLE}) reached, waiting for next cycle')
            break

        pid_file = STATE_DIR / f'{name}.pid'
        
        # Check 1: PID file exists and process is alive
        pid = None
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
            except:
                pass

        if pid and is_process_alive(pid):
            # Process alive — check heartbeat freshness
            hb_age = get_heartbeat_age(name)
            if hb_age is not None and hb_age > STALE_THRESHOLD:
                log('WARNING', f'{name}: heartbeat stale ({int(hb_age)}s), restarting')
                if restart_daemon(name, script, args, f'stale heartbeat ({int(hb_age)}s)'):
                    restarted += 1
            # else: healthy
        else:
            # Process dead or no PID file
            reason = 'no PID file' if not pid else f'process dead (pid {pid})'
            log('WARNING', f'{name}: {reason}, restarting')
            if restart_daemon(name, script, args, reason):
                restarted += 1

    return restarted

def signal_handler(signum, frame):
    global running
    log('INFO', f'Received signal {signum}, shutting down watchdog')
    running = False
    write_heartbeat('stopped')

def main():
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Write our PID
    WATCHDOG_PID_FILE.write_text(str(os.getpid()))
    log('INFO', f'Hasan watchdog started (pid {os.getpid()})')
    log('INFO', f'Monitoring {len(DAEMONS)} daemons every {HEALTH_CHECK_INTERVAL}s')
    write_heartbeat('running')

    cycle = 0
    while running:
        cycle += 1
        try:
            restarted = health_check()
            write_heartbeat('running')
            
            if cycle % 4 == 0:  # Every ~60s, log a summary
                alive_count = sum(1 for name, _, _ in DAEMONS 
                    if (STATE_DIR / f'{name}.pid').exists() and 
                    is_process_alive(int((STATE_DIR / f'{name}.pid').read_text().strip() or 0)))
                log('INFO', f'Health check #{cycle}: {alive_count}/{len(DAEMONS)} alive, {restarted} restarted this cycle')
        except Exception as e:
            log('ERROR', f'Health check error: {e}')
            write_heartbeat('error')

        time.sleep(HEALTH_CHECK_INTERVAL)

    # Cleanup
    WATCHDOG_PID_FILE.unlink(missing_ok=True)
    log('INFO', 'Watchdog stopped')

if __name__ == '__main__':
    main()