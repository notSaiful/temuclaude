/**
 * POST /api/email/billing
 * 
 * Send billing/receipt email
 * Body: { to, subject, amount, plan, period, receiptId }
 */
import { NextRequest, NextResponse } from 'next/server';
import { sendBillingEmail } from '@/lib/email';

export const runtime = 'nodejs';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { to, subject, amount, plan, period, receiptId } = body;

    if (!to || !amount || !plan) {
      return NextResponse.json(
        { error: 'To, amount, and plan are required' },
        { status: 400 }
      );
    }

    const result = await sendBillingEmail(
      to,
      subject || `Receipt — ${plan}`,
      amount,
      plan,
      period || 'Monthly',
      receiptId || `RCP-${Date.now()}`,
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