/**
 * POST /api/email/marketing
 * 
 * Send marketing email (newsletter, announcements)
 * Body: { to (string or array), subject, content, unsubscribeUrl }
 */
import { NextRequest, NextResponse } from 'next/server';
import { sendMarketingEmail, sendBatch } from '@/lib/email';

export const runtime = 'nodejs';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { to, subject, content, unsubscribeUrl } = body;

    if (!to || !subject || !content) {
      return NextResponse.json(
        { error: 'To, subject, and content are required' },
        { status: 400 }
      );
    }

    // Single recipient
    if (typeof to === 'string') {
      const result = await sendMarketingEmail(to, subject, content, unsubscribeUrl);
      if (result.success) {
        return NextResponse.json({ success: true, id: result.id });
      } else {
        return NextResponse.json(
          { error: result.error || 'Failed to send email' },
          { status: 500 }
        );
      }
    }

    // Batch recipients
    if (Array.isArray(to)) {
      const result = await sendBatch(to, subject, content, 'marketing');
      return NextResponse.json({
        success: true,
        sent: result.sent,
        failed: result.failed,
        errors: result.errors.length > 0 ? result.errors : undefined,
      });
    }

    return NextResponse.json(
      { error: 'To must be a string or array of strings' },
      { status: 400 }
    );
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}