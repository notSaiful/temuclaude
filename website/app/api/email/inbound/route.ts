import { NextRequest, NextResponse } from 'next/server';
import { sendEmail, EMAIL_ADDRESSES } from '@/lib/email';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

function authorized(req: NextRequest) {
  const secret = process.env.INBOUND_EMAIL_WEBHOOK_SECRET;
  if (!secret) return process.env.NODE_ENV !== 'production';

  const headerSecret = req.headers.get('x-temuclaude-email-secret');
  const bearer = req.headers.get('authorization')?.replace(/^Bearer\s+/i, '').trim();
  return headerSecret === secret || bearer === secret;
}

function asString(value: unknown) {
  return typeof value === 'string' ? value : '';
}

export async function POST(req: NextRequest) {
  if (!authorized(req)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const body = await req.json();
    const from = asString(body.from || body.sender || body.reply_to || body.replyTo);
    const to = asString(body.to || body.recipient || EMAIL_ADDRESSES.hello);
    const subject = asString(body.subject || '(no subject)');
    const text = asString(body.text || body.plain || body.body);
    const html = asString(body.html);
    const receivedAt = new Date().toISOString();

    const summaryHtml = `
      <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 680px; margin: 0 auto; padding: 20px;">
        <h1 style="font-size: 20px; color: #0f172a;">Inbound email received</h1>
        <table style="width: 100%; border-collapse: collapse; font-size: 14px; color: #334155;">
          <tr><td style="padding: 6px 0; width: 90px; color: #64748b;">From</td><td>${escapeHtml(from || 'unknown')}</td></tr>
          <tr><td style="padding: 6px 0; color: #64748b;">To</td><td>${escapeHtml(to)}</td></tr>
          <tr><td style="padding: 6px 0; color: #64748b;">Subject</td><td>${escapeHtml(subject)}</td></tr>
          <tr><td style="padding: 6px 0; color: #64748b;">Received</td><td>${receivedAt}</td></tr>
        </table>
        <div style="margin-top: 18px; padding: 16px; border: 1px solid #e2e8f0; border-radius: 8px; background: #f8fafc; white-space: pre-wrap; color: #0f172a;">
          ${html || escapeHtml(text || 'No message body provided.')}
        </div>
      </div>
    `;

    await sendEmail({
      to: EMAIL_ADDRESSES.hello,
      from: EMAIL_ADDRESSES.hello,
      replyTo: from || undefined,
      subject: `[Inbound] ${subject}`,
      html: summaryHtml,
      type: 'support',
      tags: ['inbound-email'],
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('[EMAIL] Inbound webhook error:', error);
    return NextResponse.json({ error: 'Inbound email webhook failed.' }, { status: 500 });
  }
}

function escapeHtml(value: string) {
  return value.replace(/[&<>"']/g, (char) => {
    switch (char) {
      case '&': return '&amp;';
      case '<': return '&lt;';
      case '>': return '&gt;';
      case '"': return '&quot;';
      case '\'': return '&#39;';
      default: return char;
    }
  });
}
