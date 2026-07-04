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

    // Get Razorpay plan ID from environment (server-side only)
    const razorpayPlanId: string | undefined = planId === 'pro'
      ? process.env.RAZORPAY_PLAN_PRO_ID
      : process.env.RAZORPAY_PLAN_ENTERPRISE_ID;

    if (!razorpayPlanId) {
      return NextResponse.json({
        error: `Razorpay plan ID not configured for ${planId}. Set RAZORPAY_PLAN_${planId.toUpperCase()}_ID in environment.`,
      }, { status: 500 });
    }

    const planIdConfirmed: string = razorpayPlanId;

    // Find or create user
    let user = getUserByEmail(email);
    if (!user) {
      try {
        user = createUser(email, name);
      } catch (e) {
        // DB write might fail on serverless — create a temporary user object
        user = { id: `tmc_${Date.now()}_${Math.random().toString(36).substring(2, 10)}`, email, name: name || null, plan: 'free', razorpay_customer_id: null, created_at: Math.floor(Date.now()/1000), updated_at: Math.floor(Date.now()/1000) };
      }
    }

    // Create Razorpay customer if not exists (skip if already exists)
    if (!user.razorpay_customer_id) {
      try {
        const customer = await createCustomer({
          name: name || email.split('@')[0],
          email,
          notes: { user_id: user.id, plan: planId },
        });
        try { updateUserRazorpayCustomer(user.id, customer.id); } catch {}
      } catch (custErr: any) {
        // Customer might already exist in Razorpay — that's fine, continue without customer ID
        console.log('Customer creation skipped:', custErr.message);
      }
    }

    // Create Razorpay subscription
    const subscription = await createSubscription({
      planId: planIdConfirmed,
      notes: {
        user_id: user.id,
        plan: planId,
        email,
      },
    }) as any;

    // Record in DB (non-critical — subscription still works if DB write fails)
    try {
      createSubscriptionRecord({
        userId: user.id,
        razorpaySubscriptionId: subscription.id,
        razorpayPlanId: planIdConfirmed,
        plan: planId,
      });
    } catch (dbErr) {
      console.log('DB record skipped:', dbErr instanceof Error ? dbErr.message : 'unknown');
    }

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
    const errMsg = error?.message || error?.error?.description || 'Failed to create subscription';
    const statusCode = error?.statusCode || 500;
    return NextResponse.json({ error: errMsg, details: JSON.stringify(error?.error || error) }, { status: statusCode });
  }
}