/**
 * POST /api/email/legal
 * 
 * Send legal notice email
 * Body: { to, subject, content }
 * Restricted: only callable with master key
 */
import { NextRequest, NextResponse } from 'next/server';
import { sendLegalNotice, EMAIL_ADDRESSES } from '@/lib/email';

export const runtime = 'nodejs';

export async function POST(request: NextRequest) {
  try {
    // Verify master key for legal emails
    const authKey = request.headers.get('authorization')?.replace('Bearer ', '');
    const masterKey = process.env.TEMUCLAUDE_MASTER_KEY;

    if (masterKey && authKey !== masterKey) {
      return NextResponse.json(
        { error: 'Unauthorized — legal emails require master key' },
        { status: 401 }
      );
    }

    const body = await request.json();
    const { to, subject, content } = body;

    if (!to || !subject || !content) {
      return NextResponse.json(
        { error: 'To, subject, and content are required' },
        { status: 400 }
      );
    }

    const result = await sendLegalNotice(to, subject, content);

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