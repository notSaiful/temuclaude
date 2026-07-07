/**
 * POST /api/email/security
 * 
 * Send security alert email
 * Body: { to, alertType, message }
 */
import { NextRequest, NextResponse } from 'next/server';
import { sendSecurityAlert } from '@/lib/email';

export const runtime = 'nodejs';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { to, alertType, message } = body;

    if (!to || !alertType || !message) {
      return NextResponse.json(
        { error: 'To, alertType, and message are required' },
        { status: 400 }
      );
    }

    const result = await sendSecurityAlert(to, alertType, message);

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