// Razorpay client initialization (server-side only)
import Razorpay from 'razorpay';
import crypto from 'crypto';

function getRazorpayInstance(): Razorpay {
  const keyId = process.env.RAZORPAY_KEY_ID;
  const keySecret = process.env.RAZORPAY_KEY_SECRET;

  if (!keyId || !keySecret) {
    throw new Error('Razorpay keys not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env');
  }

  return new Razorpay({
    key_id: keyId,
    key_secret: keySecret,
  });
}

// Create a one-time order (for PAYG credits or one-time purchases)
export async function createOrder(amountINR: number, notes: Record<string, string> = {}) {
  const rzp = getRazorpayInstance();
  const order = await rzp.orders.create({
    amount: amountINR, // in paise
    currency: 'INR',
    notes: {
      ...notes,
      source: 'temuclaude-website',
    },
  });
  return order;
}

// Create a subscription plan (run once during setup)
export async function createPlan(params: {
  name: string;
  amountINR: number;
  period: 'weekly' | 'monthly' | 'yearly';
  interval?: number;
  description?: string;
}) {
  const rzp = getRazorpayInstance();
  const plan = await rzp.plans.create({
    period: params.period,
    interval: params.interval || 1,
    item: {
      name: params.name,
      amount: params.amountINR,
      currency: 'INR',
      description: params.description || '',
    },
  });
  return plan;
}

// Create a subscription for a customer
export async function createSubscription(params: {
  planId: string;
  customerId?: string;
  totalCount?: number; // total billing cycles (min 1)
  notes?: Record<string, string>;
}) {
  const rzp = getRazorpayInstance();
  const subscription = await rzp.subscriptions.create({
    plan_id: params.planId,
    customer_notify: 1,
    total_count: params.totalCount || 12, // default to 12 billing cycles (1 year)
    notes: params.notes || {},
  });
  return subscription;
}

// Fetch subscription details
export async function fetchSubscription(subscriptionId: string) {
  const rzp = getRazorpayInstance();
  return rzp.subscriptions.fetch(subscriptionId);
}

// Cancel a subscription
export async function cancelSubscription(subscriptionId: string, cancelAtCycleEnd = true) {
  const rzp = getRazorpayInstance();
  return rzp.subscriptions.cancel(subscriptionId, cancelAtCycleEnd ? 1 : 0);
}

// Verify payment signature (from Razorpay checkout)
export function verifyPaymentSignature(params: {
  razorpayOrderId: string;
  razorpayPaymentId: string;
  razorpaySignature: string;
}): boolean {
  const secret = process.env.RAZORPAY_KEY_SECRET;
  if (!secret) return false;

  const body = `${params.razorpayOrderId}|${params.razorpayPaymentId}`;
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(body)
    .digest('hex');

  return expectedSignature === params.razorpaySignature;
}

// Verify webhook signature
export function verifyWebhookSignature(params: {
  rawBody: string;
  signature: string;
}): boolean {
  const secret = process.env.RAZORPAY_KEY_SECRET;
  if (!secret) return false;

  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(params.rawBody)
    .digest('hex');

  return expectedSignature === params.signature;
}

// Create a customer in Razorpay
export async function createCustomer(params: {
  name: string;
  email: string;
  contact?: string;
  notes?: Record<string, string>;
}) {
  const rzp = getRazorpayInstance();
  return rzp.customers.create({
    name: params.name,
    email: params.email,
    contact: params.contact,
    notes: params.notes || {},
  });
}