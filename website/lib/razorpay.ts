// Razorpay client initialization (server-side only)
// Uses direct fetch calls instead of the SDK for maximum compatibility
import crypto from 'crypto';

function getAuthHeader(): string {
  const keyId = process.env.RAZORPAY_KEY_ID;
  const keySecret = process.env.RAZORPAY_KEY_SECRET;

  if (!keyId || !keySecret) {
    throw new Error(`Razorpay keys not configured. RAZORPAY_KEY_ID: ${keyId ? 'set' : 'missing'}, RAZORPAY_KEY_SECRET: ${keySecret ? 'set' : 'missing'}`);
  }

  // Basic auth: base64(keyId:keySecret)
  return 'Basic ' + Buffer.from(`${keyId}:${keySecret}`).toString('base64');
}

const RAZORPAY_BASE = 'https://api.razorpay.com/v1';

async function razorpayRequest(method: string, endpoint: string, body?: any): Promise<any> {
  const headers: Record<string, string> = {
    'Authorization': getAuthHeader(),
    'Content-Type': 'application/json',
  };

  const response = await fetch(`${RAZORPAY_BASE}${endpoint}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  const data = await response.json();

  if (!response.ok) {
    const error: any = new Error(data?.error?.description || `Razorpay API error: ${response.status}`);
    error.statusCode = response.status;
    error.error = data?.error;
    throw error;
  }

  return data;
}

// Create a one-time order (for PAYG credits or one-time purchases)
export async function createOrder(amountINR: number, notes: Record<string, string> = {}) {
  return razorpayRequest('POST', '/orders', {
    amount: amountINR,
    currency: 'INR',
    notes: { ...notes, source: 'temuclaude-website' },
  });
}

// Create a subscription plan (run once during setup)
export async function createPlan(params: {
  name: string;
  amountINR: number;
  period: 'weekly' | 'monthly' | 'yearly';
  interval?: number;
  description?: string;
}) {
  return razorpayRequest('POST', '/plans', {
    period: params.period,
    interval: params.interval || 1,
    item: {
      name: params.name,
      amount: params.amountINR,
      currency: 'INR',
      description: params.description || '',
    },
  });
}

// Create a subscription for a customer
export async function createSubscription(params: {
  planId: string;
  customerId?: string;
  totalCount?: number;
  notes?: Record<string, string>;
}) {
  return razorpayRequest('POST', '/subscriptions', {
    plan_id: params.planId,
    customer_notify: 1,
    total_count: params.totalCount || 12,
    notes: params.notes || {},
  });
}

// Fetch subscription details
export async function fetchSubscription(subscriptionId: string) {
  return razorpayRequest('GET', `/subscriptions/${subscriptionId}`);
}

// Fetch order details (one-time / top-up purchases). Notes carry the paid plan
// and user_id, which /api/payments/verify uses as the source of truth for what
// was actually purchased — instead of trusting client-supplied values.
export async function fetchOrder(orderId: string) {
  return razorpayRequest('GET', `/orders/${orderId}`);
}

// Cancel a subscription
export async function cancelSubscription(subscriptionId: string, cancelAtCycleEnd = true) {
  return razorpayRequest('POST', `/subscriptions/${subscriptionId}/cancel`, {
    cancel_at_cycle_end: cancelAtCycleEnd ? 1 : 0,
  });
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
  return razorpayRequest('POST', '/customers', {
    name: params.name,
    email: params.email,
    contact: params.contact,
    notes: params.notes || {},
  });
}