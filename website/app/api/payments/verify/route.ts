// Verify payment after Razorpay checkout
// POST /api/payments/verify
// Body: { razorpayOrderId, razorpayPaymentId, razorpaySignature, subscriptionId? }
//
// Security: the caller must be authenticated, and the plan granted is taken from
// the Razorpay subscription/order notes (set at creation), NOT from the client
// body. This prevents a user from paying for one plan and granting themselves a
// higher plan, more credits, or another user's entitlement (IDOR / privilege
// escalation). Body-supplied userId/planId are ignored.

import { NextRequest, NextResponse } from 'next/server';
import { verifyPaymentSignature, fetchSubscription, fetchOrder } from '@/lib/razorpay';
import { getAuthenticatedSupabaseUser } from '@/lib/supabase-server';
import {
  getOrCreateUserByEmailAsync,
  updatePaymentStatusAsync,
  updateSubscriptionStatusAsync,
  updateUserPlanAsync,
  addCreditsToUserAsync,
} from '@/lib/db';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

function creditsForPlanId(planId: string): number {
  if (planId.endsWith('100m')) return 100_000_000;
  if (planId.endsWith('25m')) return 25_000_000;
  if (planId.endsWith('10m')) return 10_000_000;
  if (planId.endsWith('5m')) return 5_000_000;
  return 1_000_000; // default 1M
}

export async function POST(req: NextRequest) {
  try {
    // 1) Authenticate the caller. userId is derived from the session, never
    //    trusted from the request body.
    const auth = await getAuthenticatedSupabaseUser(req);
    if ('error' in auth) {
      return NextResponse.json({ error: auth.error }, { status: auth.status || 401 });
    }
    const email = auth.user.email?.trim().toLowerCase();
    if (!email) {
      return NextResponse.json({ error: 'Authenticated user has no email address' }, { status: 400 });
    }
    const authUser = await getOrCreateUserByEmailAsync(email);

    const body = await req.json();
    const { razorpayOrderId, razorpayPaymentId, razorpaySignature, subscriptionId } = body;

    if (!razorpayOrderId || !razorpayPaymentId || !razorpaySignature) {
      return NextResponse.json({ error: 'Missing payment parameters' }, { status: 400 });
    }

    // 2) Verify the Razorpay signature (proves the payment is real).
    const isValid = verifyPaymentSignature({ razorpayOrderId, razorpayPaymentId, razorpaySignature });
    if (!isValid) {
      return NextResponse.json({ error: 'Invalid payment signature' }, { status: 400 });
    }

    // 3) Determine what was actually paid from Razorpay's own records (source of
    //    truth), not from the client. Subscriptions carry notes { user_id, plan };
    //    one-time/top-up orders carry the same notes.
    let paidUserId: string | undefined;
    let paidPlanId: string | undefined;
    try {
      if (subscriptionId) {
        const sub = await fetchSubscription(subscriptionId);
        paidUserId = sub?.notes?.user_id;
        paidPlanId = sub?.notes?.plan;
      } else {
        const order = await fetchOrder(razorpayOrderId);
        paidUserId = order?.notes?.user_id;
        paidPlanId = order?.notes?.plan;
      }
    } catch (err: any) {
      console.error('Failed to fetch Razorpay record for verification:', err?.message || err);
      return NextResponse.json({ error: 'Unable to verify paid plan from Razorpay' }, { status: 400 });
    }

    if (!paidPlanId) {
      return NextResponse.json({ error: 'Paid plan not found on the Razorpay record' }, { status: 400 });
    }

    // 4) Ownership: the record must belong to the authenticated user.
    if (paidUserId && paidUserId !== authUser.id) {
      return NextResponse.json({ error: 'This payment does not belong to the authenticated user' }, { status: 403 });
    }

    // 5) Apply the VERIFIED plan (never the client-supplied planId).
    await updatePaymentStatusAsync(razorpayOrderId, 'paid', razorpayPaymentId, razorpaySignature);
    if (subscriptionId) {
      await updateSubscriptionStatusAsync(subscriptionId, 'active');
    }

    if (paidPlanId.startsWith('credits_') || paidPlanId.startsWith('topup_')) {
      await addCreditsToUserAsync(authUser.id, creditsForPlanId(paidPlanId));
    } else {
      await updateUserPlanAsync(authUser.id, paidPlanId);
    }

    return NextResponse.json({
      verified: true,
      message: 'Payment verified successfully',
      plan: paidPlanId,
    });
  } catch (error: any) {
    console.error('Payment verification error:', error);
    return NextResponse.json({ error: error.message || 'Verification failed' }, { status: 500 });
  }
}