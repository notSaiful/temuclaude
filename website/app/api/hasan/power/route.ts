import { NextRequest, NextResponse } from 'next/server';
import { execSync } from 'child_process';

export const runtime = 'nodejs';
export const maxDuration = 60;

const TEMUCLAUDE_DIR = process.env.TEMUCLAUDE_DIR || '/Users/saiful/temuclaude';
const STATE_DIR = '/tmp/temuclaude_daemons';

export async function POST(req: NextRequest) {
  try {
    const { action } = await req.json();

    if (action === 'activate') {
      // Clear stale PID files
      try {
        execSync(`rm -f ${STATE_DIR}/*.pid ${STATE_DIR}/*_heartbeat.json`, { timeout: 3000 });
      } catch {}

      // Start the swarm
      try {
        execSync('bash research/scripts/start_swarm.sh', {
          cwd: TEMUCLAUDE_DIR,
          timeout: 45000,
          encoding: 'utf-8',
        });

        // Wait for daemons to register
        await new Promise(r => setTimeout(r, 5000));

        // Count alive daemons
        let alive = 0;
        try {
          const pids = execSync(`ls ${STATE_DIR}/*.pid 2>/dev/null`, { encoding: 'utf-8' }).trim().split('\n').filter(Boolean);
          for (const pidfile of pids) {
            try {
              const pid = parseInt(execSync(`cat ${pidfile}`, { encoding: 'utf-8' }).trim());
              if (pid && !isNaN(pid)) {
                try { process.kill(pid, 0); alive++; } catch {}
              }
            } catch {}
          }
        } catch {}

        return NextResponse.json({
          success: true,
          message: `Hasan activated. ${alive}/23 daemons running.`,
          alive,
        });
      } catch (e: any) {
        return NextResponse.json({ success: false, error: e.message }, { status: 500 });
      }
    }

    if (action === 'deactivate') {
      // Kill watchdog first so it doesn't restart daemons
      try {
        const wdPid = parseInt(execSync(`cat ${STATE_DIR}/watchdog.pid 2>/dev/null`, { encoding: 'utf-8' }).trim());
        if (wdPid && !isNaN(wdPid)) {
          try { process.kill(wdPid, 'SIGTERM'); } catch {}
        }
        execSync(`rm -f ${STATE_DIR}/watchdog.pid ${STATE_DIR}/watchdog_heartbeat.json`, { timeout: 2000 });
      } catch {}

      // Kill sync daemon
      try {
        execSync('pkill -f "sync_daemon.py"', { timeout: 2000 });
      } catch {}

      // Kill all daemons
      try {
        const pids = execSync(`ls ${STATE_DIR}/*.pid 2>/dev/null`, { encoding: 'utf-8' }).trim().split('\n').filter(Boolean);
        let killed = 0;
        for (const pidfile of pids) {
          try {
            const pid = parseInt(execSync(`cat ${pidfile}`, { encoding: 'utf-8' }).trim());
            if (pid && !isNaN(pid)) {
              try { process.kill(pid, 'SIGTERM'); killed++; } catch {}
            }
          } catch {}
        }

        // Wait for graceful shutdown
        await new Promise(r => setTimeout(r, 2000));

        // Force kill any survivors
        for (const pidfile of pids) {
          try {
            const pid = parseInt(execSync(`cat ${pidfile}`, { encoding: 'utf-8' }).trim());
            if (pid && !isNaN(pid)) {
              try { process.kill(pid, 'SIGKILL'); } catch {}
            }
          } catch {}
        }

        // Clean up PID files
        try { execSync(`rm -f ${STATE_DIR}/*.pid`, { timeout: 3000 }); } catch {}

        return NextResponse.json({
          success: true,
          message: `Hasan deactivated. ${killed} daemons stopped.`,
        });
      } catch (e: any) {
        return NextResponse.json({ success: false, error: e.message }, { status: 500 });
      }
    }

    return NextResponse.json({ error: 'Unknown action. Use "activate" or "deactivate".' }, { status: 400 });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function GET() {
  try {
    let alive = 0;
    let total = 0;
    try {
      const { execSync } = await import('child_process');
      const pids = execSync(`ls ${STATE_DIR}/*.pid 2>/dev/null`, { encoding: 'utf-8' }).trim().split('\n').filter(Boolean);
      total = pids.length;
      for (const pidfile of pids) {
        try {
          const pid = parseInt(execSync(`cat ${pidfile}`, { encoding: 'utf-8' }).trim());
          if (pid && !isNaN(pid)) {
            try { process.kill(pid, 0); alive++; } catch {}
          }
        } catch {}
      }
    } catch {}

    return NextResponse.json({
      status: alive > 0 ? 'active' : 'deactivated',
      alive,
      total: 23,
    });
  } catch (error: any) {
    return NextResponse.json({ status: 'deactivated', alive: 0, total: 23 });
  }
}