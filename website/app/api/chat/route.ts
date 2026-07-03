import { NextRequest } from 'next/server';

export const runtime = 'edge';
export const maxDuration = 60;

export async function POST(req: NextRequest) {
  const { messages } = await req.json();
  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      try {
        const lastMessage = messages[messages.length - 1]?.content || '';

        // Call the Timuclaude orchestrator API
        // In production this hits our Python backend
        const orchestratorUrl = process.env.TIMUCLAUDE_API_URL || 'http://localhost:8000';
        
        let responseText = '';
        let orchestrationData: any = null;

        try {
          // Try to call the real orchestrator
          const orchResponse = await fetch(`${orchestratorUrl}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: lastMessage }),
            signal: AbortSignal.timeout(55000),
          });

          if (orchResponse.ok) {
            const data = await orchResponse.json();
            responseText = data.response || data.answer || '';
            orchestrationData = {
              orchestration: {
                taskType: data.task_type || 'general',
                tier: data.tier || 'auto',
                models: (data.models || []).map((m: any) => ({
                  name: m.name,
                  response: m.response?.substring(0, 200) || '',
                  latency: m.latency || 0,
                  correct: m.correct !== false,
                })),
                aggregator: data.aggregator || 'GLM-5.2',
                consensus: data.consensus || 3,
                qaScore: data.qa_score || 0,
                codeVerified: data.code_verified || false,
                totalLatency: ((data.total_latency || 2.3)).toFixed(1),
                cost: data.cost || '$0.019',
              },
            };
          } else {
            throw new Error(`Orchestrator returned ${orchResponse.status}`);
          }
        } catch (err) {
          // Fallback: if orchestrator is not running, return a helpful message
          responseText = `Timuclaude orchestrator is not running. Start it with:\n\npython -m src.orchestrator --serve\n\nOr set TIMUCLAUDE_API_URL to point to your orchestrator instance.\n\nYour question was: "${lastMessage}"`;
          orchestrationData = {
            orchestration: {
              taskType: 'unknown',
              tier: 'fallback',
              models: [],
              aggregator: 'none',
              consensus: 0,
              qaScore: 0,
              codeVerified: false,
              totalLatency: '0',
              cost: '$0.000',
            },
          };
        }

        // Stream the response word by word
        const words = responseText.split(' ');
        for (let i = 0; i < words.length; i++) {
          const chunk = i === 0 ? words[i] : ' ' + words[i];
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ chunk })}\n\n`));
          await new Promise((resolve) => setTimeout(resolve, 30));
        }

        // Send orchestration data
        if (orchestrationData) {
          controller.enqueue(encoder.encode(`data: ${JSON.stringify(orchestrationData)}\n\n`));
        }

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