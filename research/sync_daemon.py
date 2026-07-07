#!/usr/bin/env python3
"""
Hasan Live State Sync Daemon
=============================
Runs on the local machine. Every 10 seconds it:
1. Reads all live daemon data (PIDs, heartbeats, activity, SWOT, queue, etc.)
2. Writes it to research/live_state.json (the sync file the Vercel API reads)
3. Pushes it to the Vercel deployment via POST /api/hasan/sync

This ensures the Vercel deployment ALWAYS shows live, accurate data
even though Vercel can't read local files.
"""

import json
import os
import time
import subprocess
from datetime import datetime
from pathlib import Path
import urllib.request

STATE_DIR = Path('/tmp/temuclaude_daemons')
RESEARCH_DIR = Path('/Users/saiful/temuclaude/research')
SYNC_FILE = RESEARCH_DIR / 'live_state.json'

# Vercel deployment URL for pushing live data
VERCEL_URL = os.environ.get('VERCEL_DEPLOY_URL', '')  # e.g. https://temuclaude.vercel.app
SYNC_INTERVAL = 10  # seconds

DAEMONS = [
    'scout_daemon', 'distiller_daemon',
    'research_daemon_1', 'research_daemon_2', 'research_daemon_3',
    'integrator_daemon', 'coordinator_daemon',
    'cyber_daemon', 'efficiency_daemon', 'media_daemon',
    'marketing_daemon', 'feedback_daemon',
    'meta_auditor_daemon', 'swot_daemon', 'website_daemon',
    'industry_radar_daemon', 'model_optimizer_daemon',
    'cost_efficiency_daemon', 'revenue_daemon', 'growth_daemon',
    'competitive_dominance_daemon', 'self_expansion_daemon',
    'super_intelligence_daemon',
]

def read_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return None

def is_alive(pid):
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except:
        return False

def get_daemon_statuses():
    results = []
    now = datetime.now()
    for name in DAEMONS:
        pid = None
        try:
            pid = int((STATE_DIR / f'{name}.pid').read_text().strip())
        except:
            pass

        hb = read_json(STATE_DIR / f'{name}_heartbeat.json')
        hb_age = None
        if hb and hb.get('timestamp'):
            try:
                hb_age = int((now - datetime.fromisoformat(hb['timestamp'])).total_seconds())
            except:
                pass

        alive = is_alive(pid)
        
        # Health check: a daemon is healthy if alive AND heartbeat < 5 min old
        # AND no error in heartbeat extra
        healthy = False
        health_reason = ''
        if not alive:
            healthy = False
            health_reason = 'process_dead'
        elif hb_age is None:
            healthy = False
            health_reason = 'no_heartbeat'
        elif hb_age > 300:
            healthy = False
            health_reason = f'heartbeat_stale_{hb_age}s'
        elif hb and hb.get('extra', {}).get('error'):
            healthy = False
            health_reason = f'error: {hb["extra"]["error"][:50]}'
        else:
            healthy = True
            health_reason = 'ok'
        
        results.append({
            'name': name,
            'pid': pid,
            'alive': alive,
            'healthy': healthy,
            'healthReason': health_reason,
            'status': hb.get('status', 'unknown') if hb else 'unknown',
            'heartbeatAge': hb_age,
            'extra': hb.get('extra', {}) if hb else {},
        })
    return results

def get_activity():
    activities = []
    try:
        for f in os.listdir(STATE_DIR):
            if not f.endswith('.log') or f == 'watchdog.log':
                continue
            try:
                content = (STATE_DIR / f).read_text()
                lines = content.strip().split('\n')[-5:]
                for line in lines:
                    if 'INFO' in line or 'ERROR' in line or 'WARNING' in line:
                        # Parse: timestamp | daemon | level | message
                        parts = line.split('|', 3)
                        if len(parts) >= 4:
                            activities.append({
                                'time': parts[0].strip(),
                                'daemon': parts[1].strip(),
                                'level': parts[2].strip(),
                                'message': parts[3].strip()[:150],
                            })
            except:
                pass
    except:
        pass
    activities.sort(key=lambda x: x['time'], reverse=True)
    return activities[:30]

def get_queue():
    return read_json(RESEARCH_DIR / 'queue.json') or {}

def get_swot():
    try:
        content = (RESEARCH_DIR / 'swot_reports' / 'CURRENT_SWOT.md').read_text()
        sections = {'strengths': 0, 'weaknesses': 0, 'opportunities': 0, 'threats': 0}
        current = None
        for line in content.split('\n'):
            if line.startswith('## '):
                name = line.replace('## ', '').strip().split()[0].lower()
                if name in sections:
                    current = name
            elif line.startswith('- ') and current:
                sections[current] += 1
        return sections
    except:
        return None

def get_cost():
    credits = read_json(RESEARCH_DIR / 'credits_state.json') or {}
    throttle = read_json(RESEARCH_DIR / 'throttle_state.json') or {}
    summary = read_json(RESEARCH_DIR / 'cost_summary.json') or {}
    return {
        'remainingCredits': credits.get('remaining_credits', 0),
        'burnRatePerDay': credits.get('burn_rate_per_day', 0),
        'throttleLevel': throttle.get('level', 'green'),
        'totalSpent24h': summary.get('total_spent', 0),
        'totalTokens24h': summary.get('total_tokens', 0),
    }

def get_ummah():
    fund = read_json(RESEARCH_DIR / 'ummah_fund.json')
    if not fund or not isinstance(fund, list):
        return {'totalDistributed': 0, 'entries': 0}
    total = sum(e.get('fund_total', 0) for e in fund)
    return {'totalDistributed': total, 'entries': len(fund)}

def get_identity():
    try:
        content = (RESEARCH_DIR / 'hasan_identity.py').read_text()
        import re
        purpose = re.search(r'"purpose":\s*"([^"]+)"', content)
        goal = re.search(r'"ultimate_goal":\s*"([^"]+)"', content)
        return {
            'verified': True,
            'purpose': purpose.group(1)[:100] if purpose else '',
            'goal': goal.group(1)[:100] if goal else '',
        }
    except:
        return {'verified': False, 'purpose': '', 'goal': ''}

def get_shared_intelligence():
    events = read_json(RESEARCH_DIR / 'shared_state' / 'events.json') or {}
    knowledge = read_json(RESEARCH_DIR / 'shared_state' / 'knowledge.json') or {}
    return {
        'daemons': len(events.get('events', [])),
        'recentEvents': events.get('events', [])[-10:],
        'knowledgeFacts': len(knowledge.get('facts', {})),
    }

def get_watchdog_status():
    wd = read_json(STATE_DIR / 'watchdog_heartbeat.json')
    if wd:
        return {'status': wd.get('status'), 'pid': wd.get('pid')}
    return None

def gather_all_data():
    daemons = get_daemon_statuses()
    alive_count = sum(1 for d in daemons if d['alive'])
    healthy_count = sum(1 for d in daemons if d.get('healthy'))
    
    # Real health status: not just "are processes alive" but "are they healthy"
    if alive_count == 0:
        status = 'deactivated'
    elif healthy_count == 23:
        status = 'all_systems_nominal'
    elif healthy_count >= 18:
        status = 'mostly_healthy'
    elif healthy_count > 0:
        status = 'partial'
    else:
        status = 'all_unhealthy'
    
    # Health score: 0-100 based on healthy daemons
    health_score = round((healthy_count / 23) * 100) if alive_count > 0 else 0
    
    # Collect unhealthy daemon names for diagnostics
    unhealthy_daemons = [
        {'name': d['name'], 'reason': d.get('healthReason', 'unknown')}
        for d in daemons if not d.get('healthy')
    ]
    
    return {
        'timestamp': datetime.now().isoformat(),
        'system': 'hasan',
        'status': status,
        'healthScore': health_score,
        'healthSummary': {
            'alive': alive_count,
            'healthy': healthy_count,
            'unhealthy': 23 - healthy_count,
            'unhealthyDaemons': unhealthy_daemons,
        },
        'daemons': {
            'total': 23,
            'alive': alive_count,
            'healthy': healthy_count,
            'list': daemons,
        },
        'queue': {
            'newRaw': len(get_queue().get('new_raw', [])),
            'newFindings': len(get_queue().get('new_findings', [])),
            'implementationQueue': len(get_queue().get('implementation_queue', [])),
            'implementationFailed': len(get_queue().get('implementation_failed', [])),
        },
        'sharedMemory': get_shared_intelligence(),
        'swot': get_swot(),
        'cost': get_cost(),
        'ummah': get_ummah(),
        'activity': get_activity(),
        'identity': get_identity(),
        'watchdog': get_watchdog_status(),
        'stats': {
            'sourceModules': len([f for f in os.listdir('/Users/saiful/temuclaude/src') if f.endswith('.py')]) if os.path.exists('/Users/saiful/temuclaude/src') else 0,
        },
    }

def write_sync_file(data):
    """Write live data to the sync file that Vercel reads."""
    tmp = str(SYNC_FILE) + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, SYNC_FILE)

def push_to_vercel(data):
    """Push live data to Vercel deployment via status endpoint."""
    if not VERCEL_URL:
        return False
    try:
        # Push main status data
        url = f"{VERCEL_URL}/api/hasan"
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        urllib.request.urlopen(req, timeout=5)

        # Push power state
        power_state = {
            'status': 'active' if data.get('daemons', {}).get('alive', 0) > 0 else 'deactivated',
            'alive': data.get('daemons', {}).get('alive', 0),
            'total': 23,
        }
        power_req = urllib.request.Request(
            f"{VERCEL_URL}/api/hasan/power",
            data=json.dumps({'action': 'sync', 'powerState': power_state}).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST',
        )
        urllib.request.urlopen(power_req, timeout=5)
        return True
    except Exception as e:
        print(f"  Vercel push failed: {e}", flush=True)
        return False

def main():
    print("Hasan Live State Sync Daemon started", flush=True)
    print(f"  Sync file: {SYNC_FILE}", flush=True)
    print(f"  Vercel URL: {VERCEL_URL or 'not set (local only)'}", flush=True)
    print(f"  Interval: {SYNC_INTERVAL}s", flush=True)
    
    while True:
        try:
            data = gather_all_data()
            write_sync_file(data)
            
            alive = data['daemons']['alive']
            ts = datetime.now().strftime('%H:%M:%S')
            print(f"[{ts}] Sync: {alive}/23 daemons, {len(data['activity'])} activities, status={data['status']}", flush=True)
            
            # Push to Vercel if URL is set
            if VERCEL_URL:
                push_to_vercel(data)
                
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {e}", flush=True)
        
        time.sleep(SYNC_INTERVAL)

if __name__ == '__main__':
    main()