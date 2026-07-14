import { NextRequest } from 'next/server';
import { callOpenRouter } from '@/lib/openrouter';

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
- Pricing details: Free tier offers 20 queries/day and 50K monthly credits. Paid plans use monthly credits: Developer 5M, Pro 25M, Max 100M, Enterprise 300M+ (check temuclaude.com/pricing).
`;

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const speechResult = formData.get('SpeechResult') as string | null;

    if (!speechResult || !speechResult.trim()) {
      // First time user calls, or user didn't speak
      const twiml = `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Brian" language="en-US">Hello, thank you for calling TemuClaude customer support. How can I help you today?</Say>
  <Gather input="speech" timeout="5" speechTimeout="auto" action="/api/support/voice" method="POST" />
  <Say voice="Polly.Brian" language="en-US">I didn't hear anything. If you need help, please say something, or email us at hello@temuclaude.com. Goodbye.</Say>
  <Hangup/>
</Response>`;
      return new Response(twiml, {
        headers: { 'Content-Type': 'text/xml' },
      });
    }

    // Call OpenRouter with the user's speech
    const response = await callOpenRouter('meta-llama/llama-3.3-70b-instruct', [
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: speechResult }
    ], { temperature: 0.5, maxTokens: 150 });

    const reply = response.success ? response.content.trim() : "I'm sorry, I'm having trouble connecting to our servers right now. Please email us at hello@temuclaude.com.";

    const twiml = `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Brian" language="en-US">${escapeXml(reply)}</Say>
  <Gather input="speech" timeout="5" speechTimeout="auto" action="/api/support/voice" method="POST" />
  <Say voice="Polly.Brian" language="en-US">Thank you for calling TemuClaude. Have a great day.</Say>
  <Hangup/>
</Response>`;

    return new Response(twiml, {
      headers: { 'Content-Type': 'text/xml' },
    });
  } catch (err) {
    const twiml = `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Brian" language="en-US">An error occurred in our support system. Please email us at hello@temuclaude.com. Goodbye.</Say>
  <Hangup/>
</Response>`;
    return new Response(twiml, {
      headers: { 'Content-Type': 'text/xml' },
    });
  }
}

function escapeXml(unsafe: string): string {
  return unsafe.replace(/[<>&'"]/g, (c) => {
    switch (c) {
      case '<': return '&lt;';
      case '>': return '&gt;';
      case '&': return '&amp;';
      case '\'': return '&apos;';
      case '"': return '&quot;';
      default: return c;
    }
  });
}
