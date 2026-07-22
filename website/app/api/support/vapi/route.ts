import { NextRequest } from 'next/server';

export const runtime = 'nodejs';

const SYSTEM_PROMPT = `
You are the customer support voice agent for TemuClaude, a premium multi-model AI orchestration SaaS.
Your name is Claude (Voice Assistant).
Attending calls 24/7.
Keep your responses extremely short, conversational, and direct (1-2 sentences maximum), as this will be read out loud over a phone call.
Never use markdown or formatting like asterisks or bullet points. Speak in plain English.
Key Info:
- TemuClaude orchestrates 8 top-tier models (including Claude 3.5 Sonnet, DeepSeek V4, Gemini, GLM, Nvidia Nemotron).
- Offers web playgrounds, usage logs, dashboard API keys, and custom team SLAs.
- Support Email: hello@temuclaude.com
- Support Phone: +1 (725) 268-6198
- Operating location: Nagpur, Maharashtra, India.
- Subscriptions: 30-day money-back guarantee.
- Pricing details: Free tier offers 20 queries/day. Pro and Enterprise plans have custom limits and higher quotas (check temuclaude.com/pricing).
`;

export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => ({}));
    const messageType = body?.message?.type;

    if (messageType === 'assistant-request') {
      // Vapi is requesting assistant configuration for the call
      return Response.json({
        assistant: {
          name: "TemuClaude Support Agent",
          firstMessage: "Hello! Thank you for calling TemuClaude customer support. How can I help you today?",
          model: {
            provider: "openai",
            model: "gpt-4o-mini",
            messages: [
              {
                role: "system",
                content: SYSTEM_PROMPT.trim()
              }
            ]
          },
          voice: {
            provider: "playht",
            voiceId: "susan"
          },
          recordingEnabled: true,
          firstMessageMode: "speak-first-with-playback"
        }
      });
    }

    // Handle other events gracefully (like end-of-call-report, status-update, speech-update)
    return Response.json({ status: 'ok' });
  } catch (err) {
    console.error('[Vapi Webhook Error]:', err);
    return Response.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
