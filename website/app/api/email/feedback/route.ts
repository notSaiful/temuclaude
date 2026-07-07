/**
 * POST /api/email/feedback
 * 
 * Send user feedback email
 * Body: { name, email, rating, feedback }
 */
import { NextRequest, NextResponse } from 'next/server';
import { sendFeedbackEmail } from '@/lib/email';

export const runtime = 'nodejs';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { name, email, rating, feedback } = body;

    if (!email || !feedback || rating === undefined) {
      return NextResponse.json(
        { error: 'Email, feedback, and rating are required' },
        { status: 400 }
      );
    }

    if (rating < 1 || rating > 5) {
      return NextResponse.json(
        { error: 'Rating must be between 1 and 5' },
        { status: 400 }
      );
    }

    const result = await sendFeedbackEmail(email, name || 'Anonymous', rating, feedback);

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