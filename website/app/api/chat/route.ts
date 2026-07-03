import { NextRequest } from 'next/server';

export const runtime = 'edge';

export async function POST(req: NextRequest) {
  const { messages } = await req.json();

  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      try {
        const lastMessage = messages[messages.length - 1]?.content || '';
        
        const taskType = classifyTask(lastMessage);
        const tier = determineTier(lastMessage, taskType);
        
        const responseText = `This is a simulated response from Timuclaude. In production, this will call the real orchestrator which automatically classifies your question, routes to the best models, fuses their answers, verifies with code, and quality-checks with self-QA.\n\nYour question was classified as: ${taskType}\nRouting tier: ${tier}\n\nAll of this happens invisibly — you just get the best answer.`;

        const words = responseText.split(' ');
        for (let i = 0; i < words.length; i++) {
          const chunk = i === 0 ? words[i] : ' ' + words[i];
          controller.enqueue(encoder.encode(`data: ${JSON.stringify({ chunk })}\n\n`));
          await new Promise((resolve) => setTimeout(resolve, 30));
        }

        const orchestrationData = {
          orchestration: {
            taskType,
            tier,
            models: [
              { name: 'GLM-5.2', response: 'Response from GLM-5.2', latency: 1.2, correct: true },
              { name: 'DeepSeek V4 Pro', response: 'Response from DeepSeek', latency: 1.8, correct: true },
              { name: 'Kimi K2.6', response: 'Response from Kimi', latency: 1.5, correct: true },
            ],
            aggregator: 'GLM-5.2',
            consensus: 3,
            qaScore: 9,
            codeVerified: taskType === 'math',
            totalLatency: '2.3',
            cost: '$0.019',
          },
        };
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(orchestrationData)}\n\n`));

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