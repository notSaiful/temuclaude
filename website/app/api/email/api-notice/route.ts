/**
 * POST /api/email/api-notice
 * 
 * Send API communication email (key generation, usage alerts, etc)
 * Body: { to, subject, content, action }
 */
import { NextRequest, NextResponse } from 'next/server';
import { sendApiEmail } from '@/lib/email';

export const runtime = 'nodejs';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { to, subject, content, action } = body;

    if (!to || !subject || !content) {
      return NextResponse.json(
        { error: 'To, subject, and content are required' },
        { status: 400 }
      );
    }

    const result = await sendApiEmail(to, subject, content, action || 'notification');

    if (result.success) {
      return NextResponse.json({ success: true, id: result.id });
    } else {
      return NextResponse.json(
        { error: result.error || 'Failed to send email' },
        { status: 500 }
      );
    }
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}