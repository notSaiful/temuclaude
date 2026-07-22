import { NextRequest } from 'next/server';
import { callOpenRouter } from '@/lib/openrouter';

export const runtime = 'nodejs';

const SYSTEM_PROMPT = `
You are the SMS customer support agent for TemuClaude, a premium multi-model AI orchestration SaaS.
Always respond in short, text-message friendly format (1-2 sentences maximum).
Be concise, helpful, and direct.
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
    const smsBody = formData.get('Body') as string | null;

    if (!smsBody || !smsBody.trim()) {
      const twiml = `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Message>Hello! This is TemuClaude customer support. How can we help you today? You can ask about our plans, models, or API keys.</Message>
</Response>`;
      return new Response(twiml, {
        headers: { 'Content-Type': 'text/xml' },
      });
    }

    const response = await callOpenRouter('meta-llama/llama-3.3-70b-instruct', [
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: smsBody }
    ], { temperature: 0.5, maxTokens: 200 });

    const reply = response.success ? response.content.trim() : "I'm sorry, I'm having trouble connecting to our servers right now. Please email us at hello@temuclaude.com.";

    const twiml = `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Message>${escapeXml(reply)}</Message>
</Response>`;

    return new Response(twiml, {
      headers: { 'Content-Type': 'text/xml' },
    });
  } catch (err) {
    const twiml = `<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Message>An error occurred in our messaging support. Please contact us at hello@temuclaude.com.</Message>
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
