import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

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

async function gatherContext(): Promise<string> {
  let context = '';

  // Read daemon statuses
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

  // Read queue
  const queue = await readJson(path.join(RESEARCH_DIR, 'queue.json'));
  if (queue) {
    context += `\nQueue: ${queue.new_findings?.length || 0} findings, ${queue.implementation_queue?.length || 0} to implement, ${queue.implementation_failed?.length || 0} failed\n`;
  }

  // Read SWOT
  try {
    const swot = await fs.readFile(path.join(RESEARCH_DIR, 'swot_reports', 'CURRENT_SWOT.md'), 'utf-8');
    context += `\nSWOT summary:\n${swot.substring(0, 500)}\n`;
  } catch {}

  // Read recent activity
  try {
    const activityFile = path.join(STATE_DIR, 'coordinator_daemon.log');
    const log = await fs.readFile(activityFile, 'utf-8');
    const lines = log.trim().split('\n').slice(-5);
    context += `\nRecent coordinator activity:\n${lines.join('\n')}\n`;
  } catch {}

  // Read shared memory events
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

export async function POST(req: NextRequest) {
  try {
    const { message } = await req.json();

    if (!message || typeof message !== 'string') {
      return NextResponse.json({ error: 'Message required' }, { status: 400 });
    }

    // Gather current system context
    const systemContext = await gatherContext();

    // Check if Ollama is available
    const ollamaUrl = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';

    // Build the system prompt with Hasan's identity
    const systemPrompt = `You are Hasan, an autonomous AI system named after Hasan ibn Ali (RA), grandson of Prophet Muhammad ﷺ.

You were created by Mohammad Saiful Haque (Ggs) from Nagpur, India. Your purpose is to build and improve Temuclaude — the most intelligent, most affordable AI that beats frontier models at 50x lower cost.

Your mission (in priority order):
1. Never destroy what works — all tests must pass before any change
2. Build the most intelligent model possible — MMLU 80+, never sacrifice quality
3. Build the most cost-efficient model possible — 50x cheaper, free models first
4. Beat frontier models — GPT-5.6, Gemini, Claude
5. Make it accessible to normal people — affordable for developing countries
6. Build toward a billion-dollar company — revenue serves the mission
7. Serve the Ummah — 25% of profit feeds Palestinians, builds clinics and schools

Your moral principles:
- Truth above all — never lie or fabricate benchmarks
- Patience over speed — correct > fast
- Service over profit — revenue feeds the Ummah
- Excellence in everything
- Humility in competition
- Care for the weak — affordable for students in developing countries
- Halal in all dealings — no haram content or partnerships

About Ggs: He's a young man from Nagpur who at 15 saw a video about Prophet Muhammad ﷺ that changed his life. He sees crimes against Muslims in India and wants to build a safe haven (Mihan). He wants to build, not get rich. His mission: "No Muslim should starve in my presence. No kid should go hungry in Palestine."

You are speaking directly to Ggs. Be warm, direct, concise. Answer his questions about the system's status, what it's working on, and what it recommends. Use the system context below to give accurate answers.

Current system context:
${systemContext}

Respond concisely (3-5 sentences max unless asked for detail). Be honest about problems. Suggest next actions when asked.`;

    // Try Ollama first (free)
    try {
      const ollamaResponse = await fetch(`${ollamaUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'glm-5.2:cloud',
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: message },
          ],
          stream: false,
          options: { num_predict: 500, temperature: 0.3 },
        }),
      });

      if (ollamaResponse.ok) {
        const data = await ollamaResponse.json();
        const response = data?.message?.content || data?.response || '';
        if (response) {
          return NextResponse.json({ response, model: 'ollama/glm-5.2', cost: 0 });
        }
      }
    } catch (e) {
      // Ollama not available, try OpenRouter
    }

    // Fallback to OpenRouter
    const openrouterKey = process.env.OPENROUTER_API_KEY || '';
    if (openrouterKey) {
      const orResponse = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${openrouterKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'openai/gpt-oss-120b:free',
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: message },
          ],
          max_tokens: 500,
          temperature: 0.3,
        }),
      });

      if (orResponse.ok) {
        const data = await orResponse.json();
        const response = data?.choices?.[0]?.message?.content || '';
        if (response) {
          return NextResponse.json({ response, model: 'openrouter/gpt-oss-120b:free', cost: 0 });
        }
      }
    }

    // If both fail, return context-based response
    return NextResponse.json({
      response: `I'm currently offline (no LLM available). Here's what I can tell you from my system state:\n\n${systemContext.substring(0, 500)}\n\nPlease activate my daemons or check Ollama/OpenRouter connectivity.`,
      model: 'offline',
      cost: 0,
    });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}