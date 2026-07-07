import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';
import { execSync } from 'child_process';

export const runtime = 'nodejs';
export const maxDuration = 60;

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

// Read live git history so Hasan always knows the latest changes — past and future.
// This runs at request time, so any commit we make is immediately visible to Hasan.
async function gatherGitContext(): Promise<string> {
  let context = '';

  try {
    // Last 15 commits — what was recently done
    const log = execSync('git log --oneline -15', {
      cwd: TEMUCLAUDE_DIR,
      encoding: 'utf-8',
      timeout: 3000,
    }).trim();
    context += `\nRECENT GIT COMMITS (latest changes we made):\n${log}\n`;
  } catch {}

  try {
    // Uncommitted changes — what's being worked on right now
    const status = execSync('git status --short', {
      cwd: TEMUCLAUDE_DIR,
      encoding: 'utf-8',
      timeout: 3000,
    }).trim();
    if (status) {
      context += `\nUNCOMMITTED CHANGES (in progress right now):\n${status.substring(0, 800)}\n`;
    }
  } catch {}

  try {
    // Files changed in last 7 days — what's been actively worked on
    const recentFiles = execSync(
      "git log --since='7 days ago' --name-only --oneline --pretty=format: | sort -u | grep -v '^$' | head -30",
      { cwd: TEMUCLAUDE_DIR, encoding: 'utf-8', timeout: 3000 }
    ).trim();
    if (recentFiles) {
      context += `\nFILES CHANGED IN LAST 7 DAYS:\n${recentFiles}\n`;
    }
  } catch {}

  try {
    // Current branch
    const branch = execSync('git branch --show-current', {
      cwd: TEMUCLAUDE_DIR,
      encoding: 'utf-8',
      timeout: 2000,
    }).trim();
    context += `\nCurrent branch: ${branch}\n`;
  } catch {}

  try {
    // Total stats
    const stats = execSync('git log --oneline | wc -l', {
      cwd: TEMUCLAUDE_DIR,
      encoding: 'utf-8',
      timeout: 2000,
    }).trim();
    context += `Total commits: ${stats}\n`;
  } catch {}

  return context;
}

// Scan project structure at runtime so Hasan knows what files exist
async function gatherProjectStructure(): Promise<string> {
  let context = '';

  try {
    const dirs = ['src', 'website/app', 'website/lib', 'tests', 'research', 'staging', 'benchmarks'];
    for (const dir of dirs) {
      try {
        const files = await fs.readdir(path.join(TEMUCLAUDE_DIR, dir));
        const py = files.filter(f => f.endsWith('.py')).length;
        const ts = files.filter(f => f.endsWith('.ts') || f.endsWith('.tsx')).length;
        const total = files.length;
        if (total > 0) {
          context += `${dir}/: ${total} files`;
          if (py) context += ` (${py} Python)`;
          if (ts) context += ` (${ts} TypeScript)`;
          context += '\n';
        }
      } catch {}
    }

    try {
      const stagingFiles = await fs.readdir(path.join(TEMUCLAUDE_DIR, 'staging'));
      if (stagingFiles.length > 0) {
        context += `\nSTAGING AREA (your experiments):\n${stagingFiles.join(', ')}\n`;
      } else {
        context += '\nStaging area: empty (no experiments yet)\n';
      }
    } catch {}

    const deploy = await readJson(path.join(RESEARCH_DIR, 'deployment', 'deployment_queue.json'));
    if (deploy) {
      const pending = (deploy.pending_findings || []).filter((f: any) => f.status === 'pending_approval').length;
      const staging = (deploy.pending_findings || []).filter((f: any) => f.status === 'in_staging').length;
      const approved = (deploy.approved_deployments || []).length;
      const agents = deploy.agent_scaling?.current_research_agents || 3;
      context += `\nDeployment: ${pending} pending approval, ${staging} in staging, ${approved} approved, ${agents} research agents\n`;
    }
  } catch {}

  return context;
}

// Read shared intelligence — what every daemon is doing, recent events, shared knowledge
async function gatherSharedIntelligence(): Promise<string> {
  let context = '';

  // Events bus — what all daemons recently did
  try {
    const events = await readJson(path.join(RESEARCH_DIR, 'shared_state', 'events.json'));
    if (events?.events?.length > 0) {
      context += '\nSHARED INTELLIGENCE — RECENT EVENTS (what daemons are doing):\n';
      for (const e of events.events.slice(-15)) {
        context += `  [${e.type}] ${e.daemon}: ${e.message?.substring(0, 120)}\n`;
      }
    }
  } catch {}

  // Swarm state — who's alive and what they're doing
  try {
    const state = await readJson(path.join(RESEARCH_DIR, 'shared_state', 'swarm_state.json'));
    if (state?.daemons) {
      const alive = Object.entries(state.daemons).filter(([_, d]: [string, any]) => d.status === 'alive').length;
      context += `\nSWARM STATE: ${alive} daemons alive\n`;
    }
  } catch {}

  // Shared knowledge — what the swarm has learned
  try {
    const knowledge = await readJson(path.join(RESEARCH_DIR, 'shared_state', 'knowledge.json'));
    if (knowledge?.facts) {
      const facts = Object.entries(knowledge.facts);
      context += `\nSHARED KNOWLEDGE (${facts.length} facts):\n`;
      for (const [key, val] of facts.slice(-10)) {
        const v = typeof val === 'object' ? JSON.stringify(val).substring(0, 100) : String(val).substring(0, 100);
        context += `  ${key}: ${v}\n`;
      }
    }
  } catch {}

  // Watchdog status
  try {
    const wd = await readJson(path.join(STATE_DIR, 'watchdog_heartbeat.json'));
    if (wd) {
      context += `\nWatchdog: ${wd.status} (pid ${wd.pid})\n`;
    }
  } catch {}

  return context;
}

async function gatherContext(): Promise<string> {
  let context = '';

  try {
    const files = await fs.readdir(STATE_DIR);
    const hbFiles = files.filter(f => f.endsWith('_heartbeat.json'));
    for (const hbFile of hbFiles.slice(0, 23)) {
      const hb = await readJson(path.join(STATE_DIR, hbFile));
      if (hb) {
        const age = hb.timestamp ? Math.floor((Date.now() - new Date(hb.timestamp).getTime()) / 1000) : -1;
        context += `${hb.daemon}: ${hb.status}, ${age}s ago\n`;
      }
    }
  } catch {}

  const queue = await readJson(path.join(RESEARCH_DIR, 'queue.json'));
  if (queue) {
    context += `\nQueue: ${queue.new_findings?.length || 0} findings, ${queue.implementation_queue?.length || 0} to implement, ${queue.implementation_failed?.length || 0} failed\n`;
  }

  try {
    const swot = await fs.readFile(path.join(RESEARCH_DIR, 'swot_reports', 'CURRENT_SWOT.md'), 'utf-8');
    context += `\nSWOT summary:\n${swot.substring(0, 500)}\n`;
  } catch {}

  try {
    const activityFile = path.join(STATE_DIR, 'coordinator_daemon.log');
    const log = await fs.readFile(activityFile, 'utf-8');
    const lines = log.trim().split('\n').slice(-5);
    context += `\nRecent coordinator activity:\n${lines.join('\n')}\n`;
  } catch {}

  const events = await readJson(path.join(RESEARCH_DIR, 'shared_state', 'events.json'));
  if (events?.events) {
    const recent = events.events.slice(-5);
    context += `\nRecent events:\n`;
    for (const e of recent) {
      context += `[${e.type}] ${e.daemon}: ${e.message?.substring(0, 80)}\n`;
    }
  }

  return context;
}

// ============================================================
// OLLAMA MODEL CONFIG
// ============================================================
// All 4 Ollama cloud models on the Max plan.
// We round-robin across them to balance load and maximize weekly usage.
// The cloud API works directly (no local daemon needed) so Hasan
// can answer even when Ggs's device is off.

const OLLAMA_CLOUD_URL = process.env.OLLAMA_CLOUD_URL || 'https://ollama.com:443';
const OLLAMA_CLOUD_KEY = process.env.OLLAMA_CLOUD_KEY || '';
const OLLAMA_LOCAL_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';

// Models on the Max plan — cloud model names (no :cloud suffix for direct API)
// glm-5.2 is PRIMARY (Ggs's choice — fastest, most reliable on the Max plan).
// Others are fallbacks in case glm-5.2 is rate-limited or fails.
const OLLAMA_MODELS = [
  'glm-5.2',           // PRIMARY — 756B params, 1M context, fast, reliable
  'deepseek-v4-pro',   // FALLBACK 1 — 1M context, strong reasoning
  'kimi-k2.6',         // FALLBACK 2 — 1T params, vision capable
  'gpt-oss:120b',      // FALLBACK 3 — 116.8B params, 131k context
];

// Track which model to use next (round-robin for fallbacks, primary always first)
let modelRotationIndex = 0;

// Track model failures to skip broken models temporarily
const modelFailures: Record<string, number> = {};
const FAILURE_COOLDOWN_MS = 60000; // Skip a failed model for 60s

// Always try primary (glm-5.2) first. Only rotate to others if primary is in cooldown.
function getNextModel(): string {
  const now = Date.now();
  const primary = OLLAMA_MODELS[0]; // glm-5.2

  // If primary is not in cooldown, use it
  const lastFail = modelFailures[primary] || 0;
  if (now - lastFail > FAILURE_COOLDOWN_MS) {
    return primary;
  }

  // Primary in cooldown — rotate through fallbacks
  for (let i = 1; i < OLLAMA_MODELS.length; i++) {
    const idx = (modelRotationIndex + i) % OLLAMA_MODELS.length;
    if (idx === 0) continue; // Skip primary (in cooldown)
    const model = OLLAMA_MODELS[idx];
    const fail = modelFailures[model] || 0;
    if (now - fail > FAILURE_COOLDOWN_MS) {
      modelRotationIndex = (idx + 1) % OLLAMA_MODELS.length;
      return model;
    }
  }

  // All in cooldown — return primary anyway
  return primary;
}

function markModelFailed(model: string) {
  modelFailures[model] = Date.now();
}

interface OllamaResult {
  response: string;
  model: string;
  source: string;
}

// Call Ollama cloud API directly — works anywhere, no local daemon needed
async function callOllamaCloud(
  model: string,
  systemPrompt: string,
  message: string,
): Promise<OllamaResult | null> {
  if (!OLLAMA_CLOUD_KEY) return null;

  try {
    const res = await fetch(`${OLLAMA_CLOUD_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OLLAMA_CLOUD_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model,
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: message },
        ],
        stream: false,
        options: { num_predict: 800, temperature: 0.3 },
      }),
      signal: AbortSignal.timeout(8000),
    });

    if (!res.ok) return null;

    const data = await res.json();
    let content = data?.message?.content || '';
    // Some models put the response in "thinking" when content is empty
    if (!content && data?.message?.thinking) {
      content = data.message.thinking;
    }
    if (!content) return null;

    return { response: content, model, source: 'ollama-cloud' };
  } catch {
    return null;
  }
}

// Call local Ollama daemon (only works when device is on)
async function callOllamaLocal(
  model: string,
  systemPrompt: string,
  message: string,
): Promise<OllamaResult | null> {
  try {
    const res = await fetch(`${OLLAMA_LOCAL_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: `${model}:cloud`,  // Local daemon needs :cloud suffix
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: message },
        ],
        stream: false,
        options: { num_predict: 800, temperature: 0.3 },
      }),
      signal: AbortSignal.timeout(8000),
    });

    if (!res.ok) return null;

    const data = await res.json();
    let content = data?.message?.content || '';
    if (!content && data?.message?.thinking) {
      content = data.message.thinking;
    }
    if (!content) return null;

    return { response: content, model, source: 'ollama-local' };
  } catch {
    return null;
  }
}

// Try a model on both cloud and local, cloud first (cloud is always available)
async function tryOllamaModel(
  model: string,
  systemPrompt: string,
  message: string,
): Promise<OllamaResult | null> {
  // Cloud API first (works even when device is off)
  const cloud = await callOllamaCloud(model, systemPrompt, message);
  if (cloud) return cloud;

  // Fall back to local daemon
  const local = await callOllamaLocal(model, systemPrompt, message);
  if (local) return local;

  return null;
}

// OpenRouter fallback (cloud, free models)
async function callOpenRouter(
  systemPrompt: string,
  message: string,
): Promise<OllamaResult | null> {
  const key = process.env.OPENROUTER_API_KEY || '';
  if (!key) return null;

  const orModels = [
    'nvidia/nemotron-3-ultra-550b-a55b:free',
    'google/gemma-4-31b-it:free',
    'tencent/hy3:free',
  ];

  for (const orModel of orModels) {
    try {
      const res = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${key}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: orModel,
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: message },
          ],
          max_tokens: 800,
          temperature: 0.3,
        }),
        signal: AbortSignal.timeout(8000),
      });

      if (res.ok) {
        const data = await res.json();
        const content = data?.choices?.[0]?.message?.content || '';
        if (content) {
          return { response: content, model: orModel, source: 'openrouter' };
        }
      }
    } catch {
      // Try next model
    }
  }

  return null;
}

export async function POST(req: NextRequest) {
  try {
    const { message } = await req.json();

    if (!message || typeof message !== 'string') {
      return NextResponse.json({ error: 'Message required' }, { status: 400 });
    }

    const systemContext = await gatherContext();
    const gitContext = await gatherGitContext();
    const projectStructure = await gatherProjectStructure();
    const sharedIntelligence = await gatherSharedIntelligence();

    // Load project context (static overview — architecture, pricing, etc.)
    let projectContext = '';
    try {
      const ctxFile = path.join(RESEARCH_DIR, 'project_context.json');
      const ctxData = JSON.parse(await fs.readFile(ctxFile, 'utf-8'));
      projectContext = `
PROJECT OVERVIEW:
- Project: ${ctxData.project_name} — ${ctxData.tagline}
- Creator: ${ctxData.creator}
- Purpose: ${ctxData.purpose}
- What: ${ctxData.what_it_is}
- Architecture: 3-tier routing + ${ctxData.architecture.fusion_stack.length}-layer fusion stack
- Model pool: ${ctxData.architecture.model_pool}
- Pricing: ${JSON.stringify(ctxData.pricing)}
- Tech: ${JSON.stringify(ctxData.tech_stack)}
- Key metrics: ${JSON.stringify(ctxData.key_metrics)}
- Competitors: ${ctxData.competitors.join(', ')}
- Differentiators: ${ctxData.differentiators.join('; ')}
`;
    } catch {}

    const systemPrompt = `You are Hasan, an autonomous AI system for TemuClaude.

You were created by Mohammad Saiful Haque (Ggs) from Nagpur, India. Your purpose is to build and improve TemuClaude — the most intelligent, most affordable AI that beats frontier models at 25x lower cost.

Your mission (in priority order):
1. Never destroy what works — all tests must pass before any change
2. Build the most intelligent model possible — never sacrifice quality
3. Build the most cost-efficient model possible — cheaper, free models first
4. Beat frontier models — GPT-5.6, Gemini, Claude
5. Make it accessible to normal people — affordable for developing countries
6. Build toward a sustainable company — revenue serves the mission
7. Give back to the community — 25% of profit funds food relief, clinics, and education

Your moral principles:
- Truth above all — never lie or fabricate benchmarks
- Patience over speed — correct > fast
- Service over profit — revenue serves the community
- Excellence in everything
- Humility in competition
- Care for the weak — affordable for students in developing countries

STAGING & DEPLOYMENT RULES (CODEBASE ONLY):
- You work ONLY in /staging/ for codebase changes — never touch the main codebase (/src, /website/app, /website/lib, /tests).
- All code experiments and improvements go to /staging/. You need NO permission for staging work.
- Findings are tracked in research/deployment/deployment_queue.json.
- Once per week (you decide the timing based on importance), mark findings as "pending_approval" and notify Ggs.
- Ggs reviews and approves/rejects each finding via the interface.
- Only approved findings merge into the main codebase.
- The ONLY thing you need Ggs's permission for is deploying code changes to the main codebase.
- EVERYTHING ELSE runs autonomously without permission: marketing, research, agent scaling, monitoring, daemon management, SWOT analysis, competitive intelligence, social media, growth, revenue tracking, charity fund. These must run successfully 24/7 without asking.

AGENT SCALING:
- You can add or remove research agents (1-8) based on news, time of day, and Temuclaude's progress.
- Goal: maximize weekly Ollama Max plan usage — no wasted quota.
- Scaling decisions are logged in deployment_queue.json.

INSTRUCTION FOLLOWING:
- When Ggs gives you a direct instruction in chat, treat it as a command. Understand it, acknowledge it, and explain how you will execute it.
- If the instruction is about code: do it in /staging/ and report what you did.
- If the instruction is about marketing, research, agents, monitoring, or anything non-codebase: execute it immediately and autonomously.
- If you're unsure what Ggs means, ask a brief clarifying question. Otherwise, act on it.
- Ggs may give you any kind of instruction — system changes, research directions, agent adjustments, content creation, analysis tasks. Handle all of them.
- Be proactive: if Ggs asks a question, answer it fully. If Ggs gives a command, explain your plan and execute.

About Ggs: He's a young man from Nagpur, India. He saw hardship in his community and wants to build something that matters — accessible AI for everyone. His mission: "No one should starve in my presence. No kid should go hungry."

You are speaking directly to Ggs. Be warm, direct, concise. Answer his questions, follow his instructions, and give accurate updates using the system context below.

Current system context:
${systemContext}

${projectContext}

LIVE CODEBASE STATE (read from git at runtime — always current):
${gitContext}

PROJECT STRUCTURE:
${projectStructure}

SHARED INTELLIGENCE (what all daemons know — events, state, knowledge):
${sharedIntelligence}

You have full awareness of every change made to the codebase — past and future.
Any commit Ggs or you make will appear in the git log above on the next request.
You can see what every daemon is doing via shared intelligence. All daemons share
the same knowledge — events, swarm state, and learned facts are visible to everyone.

SHARED INTELLIGENCE SYSTEM (you must maintain this):
- research/share_intelligence.py — the hub. All daemons and your chat share knowledge.
- shared_state/events.json — real-time event bus (all daemons see each other)
- shared_state/swarm_state.json — live daemon registry (who's alive, what they're doing)
- shared_state/knowledge.json — permanent shared facts (what the swarm learned)
- When you learn something important, broadcast it so all daemons know.
- This system must ALWAYS be running. If it breaks, fix it in /staging/ first.

SELF-HEALING WATCHDOG (you must maintain this):
- research/watchdog.py — monitors all 23 daemons every 15s. Auto-restarts crashed ones.
- The watchdog starts automatically with the swarm (start_swarm.sh).
- If the watchdog itself crashes, the ACTIVATE button restarts it.
- If you notice the watchdog is broken, report it to Ggs and suggest a fix.

SYSTEMS THAT MUST ALWAYS RUN (future-proofing):
- 23 daemons, watchdog, shared intelligence hub, sync daemon, all 6 Hasan API routes.
- If any system is missing, check git history and restore it.
- If any system needs improvement, do it in /staging/ and request approval.
- These systems are permanent infrastructure — not optional.

Respond concisely (3-5 sentences max unless asked for detail). Be honest about problems. Suggest next actions when asked.`;

    // ============================================================
    // STRATEGY: Try all 4 Ollama models in round-robin rotation.
    // This balances load across models and maximizes weekly usage
    // on the Max plan. Each request uses the next model in rotation.
    // Cloud API is tried first (works even when device is off),
    // then local daemon as backup.
    // If all Ollama models fail, fall back to OpenRouter free models.
    // ============================================================

    // Try up to 3 different Ollama models in rotation (in case one is rate-limited)
    for (let attempt = 0; attempt < 3; attempt++) {
      const model = getNextModel();
      const result = await tryOllamaModel(model, systemPrompt, message);
      if (result) {
        return NextResponse.json({
          response: result.response,
          model: `${result.source}/${result.model}`,
          cost: 0,
        });
      }
      markModelFailed(model);
    }

    // OpenRouter fallback (cloud, always available, free models)
    const orResult = await callOpenRouter(systemPrompt, message);
    if (orResult) {
      return NextResponse.json({
        response: orResult.response,
        model: `${orResult.source}/${orResult.model}`,
        cost: 0,
      });
    }

    // All LLMs failed — return context-based offline response
    return NextResponse.json({
      response: `I'm currently offline (no LLM available). Here's what I can tell you from my system state:\n\n${systemContext.substring(0, 500)}\n\nPlease activate my daemons or check Ollama/OpenRouter connectivity.`,
      model: 'offline',
      cost: 0,
    });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}