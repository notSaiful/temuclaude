import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const TEMUCLAUDE_DIR = process.env.TEMUCLAUDE_DIR || '/Users/saiful/temuclaude';
const STATE_DIR = '/tmp/temuclaude_daemons';
const RESEARCH_DIR = path.join(TEMUCLAUDE_DIR, 'research');
const SYNC_FILE = path.join(RESEARCH_DIR, 'live_state.json');

async function readJson(filePath: string): Promise<any> {
  try {
    const data = await fs.readFile(filePath, 'utf-8');
    return JSON.parse(data);
  } catch {
    return null;
  }
}

async function getDaemonStatusLocal(): Promise<any[]> {
  const daemons = [
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
  ];

  const results = [];
  for (const name of daemons) {
    let pid = null;
    try {
      pid = parseInt(await fs.readFile(path.join(STATE_DIR, `${name}.pid`), 'utf-8'));
    } catch {}

    let heartbeat = null;
    try {
      heartbeat = JSON.parse(await fs.readFile(path.join(STATE_DIR, `${name}_heartbeat.json`), 'utf-8'));
    } catch {}

    const hbAge = heartbeat?.timestamp
      ? Math.floor((Date.now() - new Date(heartbeat.timestamp).getTime()) / 1000)
      : null;

    results.push({
      name, pid, alive: pid !== null,
      status: heartbeat?.status || 'unknown',
      heartbeatAge: hbAge,
      extra: heartbeat?.extra || {},
    });
  }
  return results;
}

async function getLiveData(): Promise<any> {
  // 1. Try sync file (written by sync daemon — works on Vercel + local)
  const synced = await readJson(SYNC_FILE);
  if (synced && synced.timestamp) {
    const age = Date.now() - new Date(synced.timestamp).getTime();
    if (age < 30000) return { data: synced, source: 'sync-fresh' };
    if (synced.daemons) return { data: synced, source: 'sync-stale' };
  }

  // 2. Fall back to local daemon files (only works locally)
  try {
    const daemonStatuses = await getDaemonStatusLocal();
    if (daemonStatuses.length > 0 && daemonStatuses.some(d => d.alive)) {
      const aliveCount = daemonStatuses.filter(d => d.alive).length;
      return {
        data: {
          timestamp: new Date().toISOString(),
          status: aliveCount === 23 ? 'all_systems_nominal' : aliveCount > 0 ? 'partial' : 'deactivated',
          daemons: { total: 23, alive: aliveCount, list: daemonStatuses },
        },
        source: 'local-direct',
      };
    }
  } catch {}

  // 3. Return whatever sync data we have
  if (synced) return { data: synced, source: 'sync-stale' };

  // 4. Nothing available
  return { data: null, source: 'none' };
}

export async function GET() {
  try {
    const { data, source } = await getLiveData();

    if (!data) {
      return NextResponse.json({
        timestamp: new Date().toISOString(),
        system: 'hasan',
        status: 'deactivated',
        daemons: { total: 23, alive: 0, list: [] },
        queue: { newRaw: 0, newFindings: 0, implementationQueue: 0, implementationFailed: 0 },
        sharedMemory: { daemons: 0, recentEvents: [], knowledgeFacts: 0 },
        unlimitedMemory: { exists: false, sizeMB: '0' },
        swot: null, radar: null,
        cost: { remainingCredits: 0, burnRatePerDay: 0, throttleLevel: 'green', totalSpent24h: 0, totalTokens24h: 0 },
        charity: { totalDistributed: 0, entries: 0 },
        activity: [],
        identity: { verified: false, purpose: '', goal: '' },
        stats: { sourceModules: 0 },
        dataSource: 'none',
        syncAge: 0,
      });
    }

    const aliveCount = data.daemons?.alive || 0;
    return NextResponse.json({
      timestamp: new Date().toISOString(),
      system: 'hasan',
      status: aliveCount === 23 ? 'all_systems_nominal' : aliveCount > 0 ? 'partial' : 'deactivated',
      daemons: data.daemons || { total: 23, alive: 0, list: [] },
      queue: data.queue || { newRaw: 0, newFindings: 0, implementationQueue: 0, implementationFailed: 0 },
      sharedMemory: data.sharedMemory || { daemons: 0, recentEvents: [], knowledgeFacts: 0 },
      unlimitedMemory: data.unlimitedMemory || { exists: false, sizeMB: '0' },
      swot: data.swot || null,
      radar: data.radar || null,
      cost: data.cost || { remainingCredits: 0, burnRatePerDay: 0, throttleLevel: 'green', totalSpent24h: 0, totalTokens24h: 0 },
      charity: data.charity || { totalDistributed: 0, entries: 0 },
      activity: data.activity || [],
      identity: data.identity || { verified: false, purpose: '', goal: '' },
      stats: data.stats || { sourceModules: 0 },
      dataSource: source,
      syncAge: data.timestamp ? Math.floor((Date.now() - new Date(data.timestamp).getTime()) / 1000) : 0,
    });
  } catch (error: any) {
    return NextResponse.json({
      timestamp: new Date().toISOString(),
      system: 'hasan',
      status: 'deactivated',
      error: error.message,
      dataSource: 'error',
    });
  }
}