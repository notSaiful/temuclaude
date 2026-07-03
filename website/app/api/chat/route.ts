import { NextRequest } from 'next/server';

export const runtime = 'edge';

export async function POST(req: NextRequest) {
  const { messages, mode, models, temperature } = await req.json();

  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      try {
        // Determine which backend to use (server-side — user never sees this)
        const openrouterKey = process.env.OPENROUTER_API_KEY;
        const aimlKey = process.env.AIML_API_KEY;
        const ollamaUrl = process.env.OLLAMA_API_BASE || 'http://localhost:11434';

        // Simulate orchestration (in production, this calls the real Timuclaude orchestrator)
        const lastMessage = messages[messages.length - 1]?.content || '';
        
        // Generate a response (placeholder — in production this calls our orchestrator)
        // For now, we simulate the orchestration process
        const taskType = classifyTask(lastMessage);
        const tier = determineTier(lastMessage, taskType);
        
        // Simulate streaming response
        const responseText = `This is a simulated response from Timuclaude. In production, this will call the real orchestrator which fuses responses from ${models.length} model(s) in ${mode} mode.\n\nYour question was classified as: ${taskType}\nRouting tier: ${tier}\n\nThe full orchestrator integration will be connected once the API endpoint is deployed.`;

        // Stream the response word by word
        const words = responseText.split(' ');
        for (let i = 0; i < words.length; i++) {
          const chunk = i === 0 ? words[i] : ' ' + words[i];
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ chunk })}\n\n`));
          await new Promise((resolve) => setTimeout(resolve, 30)); // 30ms delay per word
        }

        // Send orchestration data
        const orchestrationData = {
          orchestration: {
            taskType,
            tier,
            models: models.slice(0, mode === 'quick' ? 1 : 3).map((m: string) => ({
              name: m,
              response: 'Response from ' + m,
              latency: Math.random() * 2 + 1,
              correct: Math.random() > 0.2,
            })),
            aggregator: models[0] || 'glm-5.2',
            consensus: mode === 'fusion' || mode === 'verify' ? 3 : 1,
            qaScore: mode === 'verify' ? Math.floor(Math.random() * 3) + 8 : 0,
            codeVerified: mode === 'verify' && taskType === 'math',
            totalLatency: (Math.random() * 2 + 1).toFixed(1),
            cost: '$0.00' + Math.floor(Math.random() * 9 + 1),
          },
        };
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(orchestrationData)}\n\n`));

        // End stream
        controller.enqueue(encoder.encode('data: [DONE]\n\n'));
        controller.close();
      } catch (error) {
        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify({ error: 'Stream failed' })}\n\n`)
        );
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}

function classifyTask(query: string): string {
  const q = query.toLowerCase();
  if (q.match(/\d+\s*[+\-*/]\s*\d+|calculate|derivative|integral|solve|equation/)) return 'math';
  if (q.match(/code|function|python|javascript|debug|error|bug|program/)) return 'coding';
  if (q.match(/write|poem|story|essay|compose|create|generate/)) return 'creative';
  if (q.match(/explain|what is|how does|why|define|describe/)) return 'knowledge';
  if (q.match(/compare|analyze|reason|logic|deduce|infer/)) return 'reasoning';
  return 'knowledge';
}

function determineTier(query: string, taskType: string): string {
  const wordCount = query.split(' ').length;
  if (wordCount <= 8 && taskType !== 'reasoning') return 'trivial';
  if (wordCount > 50) return 'hard';
  return 'medium';
}