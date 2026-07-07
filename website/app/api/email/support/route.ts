/**
 * POST /api/email/support
 * 
 * Send a customer support email
 * Body: { name, email, message, category }
 */
import { NextRequest, NextResponse } from 'next/server';
import { sendSupportEmail } from '@/lib/email';

export const runtime = 'nodejs';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { name, email, message, category } = body;

    if (!email || !message) {
      return NextResponse.json(
        { error: 'Email and message are required' },
        { status: 400 }
      );
    }

    const result = await sendSupportEmail(
      email,
      name || 'Anonymous',
      message,
      category || 'general',
    );

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