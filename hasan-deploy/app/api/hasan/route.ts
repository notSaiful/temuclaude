import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const TEMUCLAUDE_DIR = process.env.TEMUCLAUDE_DIR || '/Users/saiful/temuclaude';
const STATE_DIR = '/tmp/temuclaude_daemons';
const RESEARCH_DIR = path.join(TEMUCLAUDE_DIR, 'research');
const SYNC_FILE = path.join(RESEARCH_DIR, 'live_state.json');

// In-memory store — persists across requests within the same serverless instance
let memState: any = null;
let memStateTime = 0;

async function readJson(filePath: string): Promise<any> {
  try {
    const data = await fs.readFile(filePath, 'utf-8');
    return JSON.parse(data);
  } catch {
    return null;
  }
}

// GET — return live status. On Vercel, reads from in-memory store (pushed by sync daemon).
// Locally, reads from sync file or local daemon files.
export async function GET() {
  try {
    // 1. Check in-memory store (works on Vercel — populated by POST from sync daemon)
    if (memState && (Date.now() - memStateTime) < 30000) {
      return NextResponse.json({
        ...memState,
        timestamp: new Date().toISOString(),
        dataSource: 'memory-fresh',
        syncAge: Math.floor((Date.now() - memStateTime) / 1000),
      });
    }

    // 2. Try sync file (works locally — sync daemon writes here)
    const synced = await readJson(SYNC_FILE);
    if (synced && synced.timestamp) {
      const age = Date.now() - new Date(synced.timestamp).getTime();
      // Read evolution data
      let evolution: any = null;
      try {
        const evoLog = await readJson(path.join(RESEARCH_DIR, 'evolution_log.json'));
        const registry = await readJson(path.join(RESEARCH_DIR, 'daemon_registry.json'));
        if (evoLog && Array.isArray(evoLog) && evoLog.length > 0) {
          evolution = {
            lastCycle: evoLog[evoLog.length - 1],
            recentCycles: evoLog.slice(-5),
            pendingChanges: (registry?.changes || []).filter((c: any) => c.status === 'staged' || c.status === 'proposed'),
          };
        }
      } catch {}
      const enrich = (d: any) => ({ ...d, evolution });
      if (age < 30000) {
        return NextResponse.json({ ...enrich(synced), dataSource: 'sync-fresh', syncAge: Math.floor(age / 1000) });
      }
      if (synced.daemons) {
        return NextResponse.json({ ...enrich(synced), dataSource: 'sync-stale', syncAge: Math.floor(age / 1000) });
      }
    }

    // 3. Try local daemon files (only works locally)
    try {
      const daemons = ['scout_daemon','distiller_daemon','research_daemon_1','research_daemon_2','research_daemon_3','integrator_daemon','coordinator_daemon','cyber_daemon','efficiency_daemon','media_daemon','marketing_daemon','feedback_daemon','meta_auditor_daemon','swot_daemon','website_daemon','industry_radar_daemon','model_optimizer_daemon','cost_efficiency_daemon','revenue_daemon','growth_daemon','competitive_dominance_daemon','self_expansion_daemon','super_intelligence_daemon','daemon_evolution_daemon'];
      let alive = 0;
      const list = [];
      for (const name of daemons) {
        let pid = null;
        try { pid = parseInt(await fs.readFile(path.join(STATE_DIR, `${name}.pid`), 'utf-8')); } catch {}
        if (pid && !isNaN(pid)) alive++;
        let hb = null;
        try { hb = JSON.parse(await fs.readFile(path.join(STATE_DIR, `${name}_heartbeat.json`), 'utf-8')); } catch {}
        list.push({ name, pid, alive: pid !== null, status: hb?.status || 'unknown', heartbeatAge: null, extra: {} });
      }
      if (alive > 0) {
        return NextResponse.json({
          timestamp: new Date().toISOString(),
          system: 'hasan',
          status: alive === 24 ? 'all_systems_nominal' : 'partial',
          daemons: { total: 24, alive, list },
          queue: { newRaw: 0, newFindings: 0, implementationQueue: 0, implementationFailed: 0 },
          sharedMemory: { daemons: 0, recentEvents: [], knowledgeFacts: 0 },
          swot: null, radar: null,
          cost: { remainingCredits: 0, burnRatePerDay: 0, throttleLevel: 'green', totalSpent24h: 0, totalTokens24h: 0 },
          ummah: { totalDistributed: 0, entries: 0 },
          activity: [],
          identity: { verified: false, purpose: '', goal: '' },
          stats: { sourceModules: 0 },
          dataSource: 'local-direct',
          syncAge: 0,
        });
      }
    } catch {}

    // 4. Return stale sync data if we have it
    if (synced) {
      return NextResponse.json({ ...synced, dataSource: 'sync-stale' });
    }

    // 5. Nothing available
    return NextResponse.json({
      timestamp: new Date().toISOString(),
      system: 'hasan',
      status: 'deactivated',
      daemons: { total: 23, alive: 0, list: [] },
      queue: { newRaw: 0, newFindings: 0, implementationQueue: 0, implementationFailed: 0 },
      sharedMemory: { daemons: 0, recentEvents: [], knowledgeFacts: 0 },
      swot: null, radar: null,
      cost: { remainingCredits: 0, burnRatePerDay: 0, throttleLevel: 'green', totalSpent24h: 0, totalTokens24h: 0 },
      ummah: { totalDistributed: 0, entries: 0 },
      activity: [],
      identity: { verified: false, purpose: '', goal: '' },
      stats: { sourceModules: 0 },
      dataSource: 'none',
      syncAge: 0,
    });
  } catch (error: any) {
    return NextResponse.json({
      timestamp: new Date().toISOString(),
      system: 'hasan', status: 'deactivated',
      error: error.message, dataSource: 'error',
    });
  }
}

// POST — sync daemon pushes live data here. Stored in-memory for GET requests.
export async function POST(req: NextRequest) {
  try {
    const data = await req.json();
    if (!data || !data.timestamp || !data.system) {
      return NextResponse.json({ error: 'Invalid sync data' }, { status: 400 });
    }
    memState = data;
    memStateTime = Date.now();
    return NextResponse.json({
      success: true,
      message: 'Live state synced',
      daemons: data.daemons?.alive || 0,
    });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}