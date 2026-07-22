// Razorpay webhook handler
// POST /api/payments/webhook
// Handles: subscription.activated, subscription.charged, subscription.cancelled,
//          payment.captured, payment.failed

import { NextRequest, NextResponse } from 'next/server';
import { verifyWebhookSignature } from '@/lib/razorpay';
import { updatePaymentStatusAsync, updateSubscriptionStatusAsync, updateUserPlanAsync } from '@/lib/db';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

// Get plan from Razorpay subscription plan_id (matched against env vars)
function getPlanByRazorpayPlanIdLocal(razorpayPlanId: string): { id: string } | null {
  if ((process.env.RAZORPAY_PLAN_DEV_ID || process.env.RAZORPAY_PLAN_DEVELOPER_ID) === razorpayPlanId) return { id: 'developer' };
  if (process.env.RAZORPAY_PLAN_PRO_ID === razorpayPlanId) return { id: 'pro' };
  if (process.env.RAZORPAY_PLAN_MAX_ID === razorpayPlanId) return { id: 'max' };
  if (process.env.RAZORPAY_PLAN_ENTERPRISE_ID === razorpayPlanId) return { id: 'enterprise' };
  return null;
}

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
        await updateSubscriptionStatusAsync(sub.id, 'active');

        // Update user plan
        const plan = getPlanByRazorpayPlanIdLocal(sub.plan_id);
        if (plan) {
          // Find user from notes
          const userId = sub.notes?.user_id;
          if (userId) {
            await updateUserPlanAsync(userId, plan.id);
          }
        }
        break;
      }

      case 'subscription.charged': {
        const sub = payload.subscription.entity;
        await updateSubscriptionStatusAsync(sub.id, 'active');

        const plan = getPlanByRazorpayPlanIdLocal(sub.plan_id);
        if (plan) {
          const userId = sub.notes?.user_id;
          if (userId) {
            await updateUserPlanAsync(userId, plan.id);
          }
        }
        break;
      }

      case 'subscription.cancelled': {
        const sub = payload.subscription.entity;
        await updateSubscriptionStatusAsync(sub.id, 'cancelled');

        // Downgrade user to free
        const userId = sub.notes?.user_id;
        if (userId) {
          await updateUserPlanAsync(userId, 'free');
        }
        break;
      }

      case 'subscription.paused': {
        const sub = payload.subscription.entity;
        await updateSubscriptionStatusAsync(sub.id, 'paused');
        break;
      }

      case 'subscription.resumed': {
        const sub = payload.subscription.entity;
        await updateSubscriptionStatusAsync(sub.id, 'active');
        break;
      }

      case 'payment.captured': {
        const payment = payload.payment.entity;
        if (payment.order_id) {
          await updatePaymentStatusAsync(payment.order_id, 'captured', payment.id);
        }
        break;
      }

      case 'payment.failed': {
        const payment = payload.payment.entity;
        if (payment.order_id) {
          await updatePaymentStatusAsync(payment.order_id, 'failed', payment.id);
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
