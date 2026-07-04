// Razorpay webhook handler
// POST /api/payments/webhook
// Handles: subscription.activated, subscription.charged, subscription.cancelled,
//          payment.captured, payment.failed

import { NextRequest, NextResponse } from 'next/server';
import { verifyWebhookSignature } from '@/lib/razorpay';
import { updateSubscriptionStatus, updateUserPlan, getUser, getActiveSubscription, updatePaymentStatus } from '@/lib/db';
import { getPlanByRazorpayPlanId } from '@/lib/plans';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    const rawBody = await req.text();
    const signature = req.headers.get('x-razorpay-signature') || '';

    // Verify webhook signature
    const isValid = verifyWebhookSignature({
      rawBody,
      signature,
    });

    if (!isValid) {
      console.error('Invalid webhook signature');
      return NextResponse.json({ error: 'Invalid signature' }, { status: 400 });
    }

    const event = JSON.parse(rawBody);
    const eventType = event.event;
    const payload = event.payload;

    console.log(`Webhook received: ${eventType}`);

    switch (eventType) {
      case 'subscription.activated': {
        const sub = payload.subscription.entity;
        updateSubscriptionStatus(sub.id, 'active');

        // Update user plan
        const plan = getPlanByRazorpayPlanId(sub.plan_id);
        if (plan) {
          // Find user from notes
          const userId = sub.notes?.user_id;
          if (userId) {
            updateUserPlan(userId, plan.id);
          }
        }
        break;
      }

      case 'subscription.charged': {
        const sub = payload.subscription.entity;
        updateSubscriptionStatus(sub.id, 'active');

        const plan = getPlanByRazorpayPlanId(sub.plan_id);
        if (plan) {
          const userId = sub.notes?.user_id;
          if (userId) {
            updateUserPlan(userId, plan.id);
          }
        }
        break;
      }

      case 'subscription.cancelled': {
        const sub = payload.subscription.entity;
        updateSubscriptionStatus(sub.id, 'cancelled');

        // Downgrade user to free
        const userId = sub.notes?.user_id;
        if (userId) {
          updateUserPlan(userId, 'free');
        }
        break;
      }

      case 'subscription.paused': {
        const sub = payload.subscription.entity;
        updateSubscriptionStatus(sub.id, 'paused');
        break;
      }

      case 'subscription.resumed': {
        const sub = payload.subscription.entity;
        updateSubscriptionStatus(sub.id, 'active');
        break;
      }

      case 'payment.captured': {
        const payment = payload.payment.entity;
        if (payment.order_id) {
          updatePaymentStatus(payment.order_id, 'captured', payment.id);
        }
        break;
      }

      case 'payment.failed': {
        const payment = payload.payment.entity;
        if (payment.order_id) {
          updatePaymentStatus(payment.order_id, 'failed', payment.id);
        }
        break;
      }

      default:
        console.log(`Unhandled webhook event: ${eventType}`);
    }

    return NextResponse.json({ received: true });
  } catch (error: any) {
    console.error('Webhook error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}