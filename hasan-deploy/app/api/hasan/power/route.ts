import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const TEMUCLAUDE_DIR = process.env.TEMUCLAUDE_DIR || '/Users/saiful/temuclaude';
const STATE_DIR = '/tmp/temuclaude_daemons';

// In-memory store for power state (pushed by sync daemon)
let memPowerState: any = null;

export async function POST(req: NextRequest) {
  try {
    const { action } = await req.json();
    
    if (action === 'sync') {
      // Sync daemon pushes power state
      const data = await req.json();
      memPowerState = data.powerState;
      return NextResponse.json({ success: true });
    }
    
    // activate/deactivate only work locally
    const { execSync } = await import('child_process');
    
    if (action === 'activate') {
      try {
        execSync(`rm -f ${STATE_DIR}/*.pid ${STATE_DIR}/*_heartbeat.json`, { timeout: 3000 });
      } catch {}
      try {
        execSync('bash research/scripts/start_swarm.sh', { cwd: TEMUCLAUDE_DIR, timeout: 45000, encoding: 'utf-8' });
        await new Promise(r => setTimeout(r, 6000));
        let alive = 0;
        try {
          const pids = execSync(`ls ${STATE_DIR}/*.pid 2>/dev/null`, { encoding: 'utf-8' }).trim().split('\n').filter(Boolean);
          for (const pidfile of pids) {
            try {
              const pid = parseInt(execSync(`cat ${pidfile}`, { encoding: 'utf-8' }).trim());
              if (pid && !isNaN(pid)) { try { process.kill(pid, 0); alive++; } catch {} }
            } catch {}
          }
        } catch {}
        return NextResponse.json({ success: true, message: `Hasan activated. ${alive}/23 daemons running.`, alive });
      } catch (e: any) {
        return NextResponse.json({ success: false, error: e.message }, { status: 500 });
      }
    }

    if (action === 'deactivate') {
      try {
        const { execSync } = await import('child_process');
        // Kill watchdog
        try { const wdPid = parseInt(execSync(`cat ${STATE_DIR}/watchdog.pid 2>/dev/null`, { encoding: 'utf-8' }).trim()); if (wdPid && !isNaN(wdPid)) { try { process.kill(wdPid, 'SIGTERM'); } catch {} } } catch {}
        try { execSync('pkill -f "sync_daemon.py"', { timeout: 2000 }); } catch {}
        const pids = execSync(`ls ${STATE_DIR}/*.pid 2>/dev/null`, { encoding: 'utf-8' }).trim().split('\n').filter(Boolean);
        let killed = 0;
        for (const pidfile of pids) {
          try { const pid = parseInt(execSync(`cat ${pidfile}`, { encoding: 'utf-8' }).trim()); if (pid && !isNaN(pid)) { try { process.kill(pid, 'SIGTERM'); killed++; } catch {} } } catch {}
        }
        await new Promise(r => setTimeout(r, 2000));
        for (const pidfile of pids) {
          try { const pid = parseInt(execSync(`cat ${pidfile}`, { encoding: 'utf-8' }).trim()); if (pid && !isNaN(pid)) { try { process.kill(pid, 'SIGKILL'); } catch {} } } catch {}
        }
        try { execSync(`rm -f ${STATE_DIR}/*.pid`, { timeout: 3000 }); } catch {}
        return NextResponse.json({ success: true, message: `Hasan deactivated. ${killed} daemons stopped.` });
      } catch (e: any) {
        return NextResponse.json({ success: false, error: e.message }, { status: 500 });
      }
    }

    return NextResponse.json({ error: 'Unknown action' }, { status: 400 });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function GET() {
  // 1. Check in-memory store (from sync daemon)
  if (memPowerState) {
    return NextResponse.json(memPowerState);
  }
  
  // 2. Try local files
  try {
    const { execSync } = await import('child_process');
    let alive = 0;
    const pids = execSync(`ls ${STATE_DIR}/*.pid 2>/dev/null`, { encoding: 'utf-8' }).trim().split('\n').filter(Boolean);
    for (const pidfile of pids) {
      try { const pid = parseInt(execSync(`cat ${pidfile}`, { encoding: 'utf-8' }).trim()); if (pid && !isNaN(pid)) { try { process.kill(pid, 0); alive++; } catch {} } } catch {}
    }
    if (alive > 0) {
      return NextResponse.json({ status: 'active', alive, total: 23 });
    }
  } catch {}
  
  return NextResponse.json({ status: 'deactivated', alive: 0, total: 23 });
}
