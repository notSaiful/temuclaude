// Verify payment after Razorpay checkout
// POST /api/payments/verify
// Body: { razorpayOrderId, razorpayPaymentId, razorpaySignature, subscriptionId?, userId, planId }

import { NextRequest, NextResponse } from 'next/server';
import { verifyPaymentSignature } from '@/lib/razorpay';
import { updatePaymentStatus, updateSubscriptionStatus, updateUserPlan, getUser } from '@/lib/db';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { razorpayOrderId, razorpayPaymentId, razorpaySignature, subscriptionId, userId, planId } = body;

    if (!razorpayOrderId || !razorpayPaymentId || !razorpaySignature) {
      return NextResponse.json({ error: 'Missing payment parameters' }, { status: 400 });
    }

    // Verify signature
    const isValid = verifyPaymentSignature({
      razorpayOrderId,
      razorpayPaymentId,
      razorpaySignature,
    });

    if (!isValid) {
      return NextResponse.json({ error: 'Invalid payment signature' }, { status: 400 });
    }

    // Update payment record
    updatePaymentStatus(razorpayOrderId, 'paid', razorpayPaymentId, razorpaySignature);

    // If subscription, update subscription status
    if (subscriptionId) {
      updateSubscriptionStatus(subscriptionId, 'active');
    }

    // Update user plan
    if (userId && planId) {
      updateUserPlan(userId, planId);
    }

    return NextResponse.json({
      verified: true,
      message: 'Payment verified successfully',
      plan: planId,
    });
  } catch (error: any) {
    console.error('Payment verification error:', error);
    return NextResponse.json({ error: error.message || 'Verification failed' }, { status: 500 });
  }
}