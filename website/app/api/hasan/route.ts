import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const TEMUCLAUDE_DIR = process.env.TEMUCLAUDE_DIR || '/Users/saiful/temuclaude';
const STATE_DIR = '/tmp/temuclaude_daemons';
const RESEARCH_DIR = path.join(TEMUCLAUDE_DIR, 'research');

async function readJson(filePath: string): Promise<any> {
  try {
    const data = await fs.readFile(filePath, 'utf-8');
    return JSON.parse(data);
  } catch {
    return null;
  }
}

async function readHeartbeat(daemonName: string): Promise<any> {
  return await readJson(path.join(STATE_DIR, `${daemonName}_heartbeat.json`));
}

async function getDaemonStatus(): Promise<any[]> {
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
    let alive = false;
    try {
      pid = parseInt(await fs.readFile(path.join(STATE_DIR, `${name}.pid`), 'utf-8'));
      alive = true; // If PID file exists, assume alive (can't send signals in edge)
    } catch {}

    const heartbeat = await readHeartbeat(name);
    const hbAge = heartbeat?.timestamp
      ? Math.floor((Date.now() - new Date(heartbeat.timestamp).getTime()) / 1000)
      : null;

    results.push({
      name,
      pid,
      alive: pid !== null,
      status: heartbeat?.status || 'unknown',
      heartbeatAge: hbAge,
      extra: heartbeat?.extra || {},
    });
  }
  return results;
}

async function getQueueStatus(): Promise<any> {
  return await readJson(path.join(RESEARCH_DIR, 'queue.json')) || {};
}

async function getSharedMemory(): Promise<any> {
  const state = await readJson(path.join(RESEARCH_DIR, 'shared_state', 'swarm_state.json')) || {};
  const events = await readJson(path.join(RESEARCH_DIR, 'shared_state', 'events.json')) || {};
  const knowledge = await readJson(path.join(RESEARCH_DIR, 'shared_state', 'knowledge.json')) || {};
  return {
    daemons: Object.keys(state.daemons || {}).length,
    recentEvents: (events.events || []).slice(-10).reverse(),
    knowledgeFacts: Object.keys(knowledge.facts || {}).length,
  };
}

async function getUnlimitedMemoryStats(): Promise<any> {
  // Read SQLite stats via a simple file check — the actual count comes from the DB
  const dbPath = path.join(RESEARCH_DIR, 'memory_store', 'swarm_memory.db');
  let exists = false;
  let size = 0;
  try {
    const stat = await fs.stat(dbPath);
    exists = true;
    size = stat.size;
  } catch {}
  return { exists, sizeBytes: size, sizeMB: (size / 1024 / 1024).toFixed(2) };
}

async function getSwotReport(): Promise<any> {
  try {
    const content = await fs.readFile(path.join(RESEARCH_DIR, 'swot_reports', 'CURRENT_SWOT.md'), 'utf-8');
    const strengths = (content.match(/## Strengths[\s\S]*?(?=\n##|$)/)?.[0] || '').split('\n').filter(l => l.startsWith('- ')).length;
    const weaknesses = (content.match(/## Weaknesses[\s\S]*?(?=\n##|$)/)?.[0] || '').split('\n').filter(l => l.startsWith('- ')).length;
    const opportunities = (content.match(/## Opportunities[\s\S]*?(?=\n##|$)/)?.[0] || '').split('\n').filter(l => l.startsWith('- ')).length;
    const threats = (content.match(/## Threats[\s\S]*?(?=\n##|$)/)?.[0] || '').split('\n').filter(l => l.startsWith('- ')).length;
    return { strengths, weaknesses, opportunities, threats };
  } catch {
    return null;
  }
}

async function getRadarReport(): Promise<any> {
  try {
    const content = await fs.readFile(path.join(RESEARCH_DIR, 'radar_reports', 'CURRENT_RADAR.md'), 'utf-8');
    const signals = content.match(/\d+\.\s*\[/g)?.length || 0;
    return { totalSignals: signals };
  } catch {
    return null;
  }
}

async function getCostInfo(): Promise<any> {
  const credits = await readJson(path.join(RESEARCH_DIR, 'credits_state.json'));
  const throttle = await readJson(path.join(RESEARCH_DIR, 'throttle_state.json'));
  const summary = await readJson(path.join(RESEARCH_DIR, 'cost_summary.json'));
  return {
    remainingCredits: credits?.remaining_credits || 0,
    burnRatePerDay: credits?.burn_rate_per_day || 0,
    throttleLevel: throttle?.level || 'green',
    totalSpent24h: summary?.total_spent || 0,
    totalTokens24h: summary?.total_tokens || 0,
  };
}

async function getUmmahFund(): Promise<any> {
  const fund = await readJson(path.join(RESEARCH_DIR, 'ummah_fund.json'));
  if (!fund || !Array.isArray(fund)) return { totalDistributed: 0, entries: 0 };
  const total = fund.reduce((sum, e) => sum + (e.fund_total || 0), 0);
  return { totalDistributed: total, entries: fund.length, lastDistribution: fund[fund.length - 1] };
}

async function getRecentLogActivity(): Promise<any[]> {
  const activities = [];
  try {
    const files = await fs.readdir(STATE_DIR);
    for (const file of files) {
      if (!file.endsWith('.log')) continue;
      try {
        const content = await fs.readFile(path.join(STATE_DIR, file), 'utf-8');
        const lines = content.trim().split('\n').slice(-3);
        for (const line of lines) {
          if (line.includes('INFO') || line.includes('ERROR')) {
            const match = line.match(/(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*\| (\w+).*\| (\w+).*\| (.*)/);
            if (match) {
              activities.push({
                time: match[1],
                daemon: match[2],
                level: match[3],
                message: match[4].substring(0, 120),
              });
            }
          }
        }
      } catch {}
    }
  } catch {}
  // Sort by time descending, take latest 20
  activities.sort((a, b) => b.time.localeCompare(a.time));
  return activities.slice(0, 20);
}

async function getTestCount(): Promise<number> {
  try {
    const content = await fs.readFile(path.join(TEMUCLAUDE_DIR, 'tests'), 'utf-8');
  } catch {}
  // Count test files
  try {
    const files = await fs.readdir(path.join(TEMUCLAUDE_DIR, 'tests'));
    return files.filter(f => f.startsWith('test_') && f.endsWith('.py')).length;
  } catch {
    return 0;
  }
}

async function getSourceCount(): Promise<number> {
  try {
    const files = await fs.readdir(path.join(TEMUCLAUDE_DIR, 'src'));
    return files.filter(f => f.endsWith('.py')).length;
  } catch {
    return 0;
  }
}

export async function GET(req: NextRequest) {
  try {
    const [
      daemons, queue, sharedMemory, memoryStats,
      swot, radar, cost, ummah, activity, testCount, sourceCount
    ] = await Promise.all([
      getDaemonStatus(),
      getQueueStatus(),
      getSharedMemory(),
      getUnlimitedMemoryStats(),
      getSwotReport(),
      getRadarReport(),
      getCostInfo(),
      getUmmahFund(),
      getRecentLogActivity(),
      getTestCount(),
      getSourceCount(),
    ]);

    const aliveCount = daemons.filter(d => d.alive).length;

    return NextResponse.json({
      timestamp: new Date().toISOString(),
      system: 'hasan',
      status: aliveCount === 23 ? 'all_systems_nominal' : 'partial',
      daemons: {
        total: daemons.length,
        alive: aliveCount,
        list: daemons,
      },
      queue: {
        newRaw: queue.new_raw?.length || 0,
        newFindings: queue.new_findings?.length || 0,
        implementationQueue: queue.implementation_queue?.length || 0,
        implementationFailed: queue.implementation_failed?.length || 0,
      },
      sharedMemory,
      unlimitedMemory: memoryStats,
      swot,
      radar,
      cost,
      ummah,
      activity,
      stats: {
        testFiles: testCount,
        sourceModules: sourceCount,
      },
    });
  } catch (error: any) {
    return NextResponse.json({ error: error.message, system: 'hasan' }, { status: 500 });
  }
}