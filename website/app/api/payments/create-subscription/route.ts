// Create subscription order for Pro or Enterprise plan
// POST /api/payments/create-subscription
// Body: { planId: 'pro' | 'enterprise', email: string, name?: string }

import { NextRequest, NextResponse } from 'next/server';
import { PLANS } from '@/lib/plans';
import { createSubscription, createCustomer } from '@/lib/razorpay';
import { createUser, getUserByEmail, updateUserRazorpayCustomer, createSubscriptionRecord } from '@/lib/db';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { planId, email, name } = body;

    // Validate
    if (!planId || !email) {
      return NextResponse.json({ error: 'Missing planId or email' }, { status: 400 });
    }

    const plan = PLANS[planId as 'pro' | 'enterprise'];
    if (!plan || plan.id === 'free') {
      return NextResponse.json({ error: 'Invalid plan. Choose pro or enterprise.' }, { status: 400 });
    }

    if (!plan.razorpayPlanId) {
      return NextResponse.json({
        error: 'Razorpay plan ID not configured. Set RAZORPAY_PLAN_PRO_ID or RAZORPAY_PLAN_ENTERPRISE_ID in .env',
      }, { status: 500 });
    }

    // Find or create user
    let user = getUserByEmail(email);
    if (!user) {
      user = createUser(email, name);
    }

    // Create Razorpay customer if not exists
    if (!user.razorpay_customer_id) {
      try {
        const customer = await createCustomer({
          name: name || email.split('@')[0],
          email,
          notes: { user_id: user.id, plan: planId },
        });
        updateUserRazorpayCustomer(user.id, customer.id);
      } catch (custErr: any) {
        // Customer might already exist in Razorpay — that's fine, skip creation
        console.log('Customer creation skipped (may already exist):', custErr.message);
      }
    }

    // Create Razorpay subscription
    const subscription = await createSubscription({
      planId: plan.razorpayPlanId,
      notes: {
        user_id: user.id,
        plan: planId,
        email,
      },
    }) as any;

    // Record in DB
    createSubscriptionRecord({
      userId: user.id,
      razorpaySubscriptionId: subscription.id,
      razorpayPlanId: plan.razorpayPlanId,
      plan: planId,
    });

    return NextResponse.json({
      subscriptionId: subscription.id,
      shortUrl: subscription.short_url,
      website: subscription.website,
      status: subscription.status,
      plan: planId,
      amount: plan.priceINR,
      currency: 'INR',
    });
  } catch (error: any) {
    console.error('Create subscription error:', error);
    return NextResponse.json({ error: error.message || 'Failed to create subscription' }, { status: 500 });
  }
}