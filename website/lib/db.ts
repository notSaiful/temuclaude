// Database layer using JSON file storage (pure JS, no native modules)
// Handles: users, subscriptions, usage tracking, API keys, payments
// Suitable for low-to-medium traffic. For high traffic, upgrade to PostgreSQL.

import crypto from 'crypto';
import fs from 'fs';
import path from 'path';

interface DBSchema {
  users: Record<string, User>;
  subscriptions: Record<string, SubscriptionRecord>;
  api_keys: Record<string, ApiKeyRecord>;
  usage: Record<string, UsageRecord>; // key: userId_date
  payments: Record<string, PaymentRecord>;
}

interface UsageRecord {
  user_id: string;
  query_date: string;
  query_count: number;
  input_tokens: number;
  output_tokens: number;
}

interface PaymentRecord {
  id: string;
  user_id: string | null;
  razorpay_order_id: string;
  razorpay_payment_id: string | null;
  razorpay_signature: string | null;
  amount: number;
  currency: string;
  status: string;
  type: string;
  plan: string | null;
  created_at: number;
}

const DB_PATH = process.env.NODE_ENV === 'production'
  ? '/tmp/temuclaude-db.json'  // Vercel serverless writable temp directory
  : path.join(process.cwd(), 'temuclaude-db.json');

let dbCache: DBSchema | null = null;

function loadDB(): DBSchema {
  if (dbCache) return dbCache;

  try {
    const data = fs.readFileSync(DB_PATH, 'utf-8');
    dbCache = JSON.parse(data);
  } catch {
    // File doesn't exist, create empty DB
    dbCache = {
      users: {},
      subscriptions: {},
      api_keys: {},
      usage: {},
      payments: {},
    };
    saveDB();
  }
  return dbCache!;
}

function saveDB(): void {
  if (!dbCache) return;
  try {
    // Write atomically (write to temp file, then rename)
    const tmpPath = DB_PATH + '.tmp';
    fs.writeFileSync(tmpPath, JSON.stringify(dbCache, null, 2));
    fs.renameSync(tmpPath, DB_PATH);
  } catch (err) {
    // On Vercel serverless, /tmp might not persist between invocations
    // but within a single request it works. Log and continue.
    console.warn('DB save failed (non-critical on serverless):', err instanceof Error ? err.message : 'unknown');
  }
}

function generateId(): string {
  return `tmc_${crypto.randomBytes(16).toString('hex')}`;
}

// === USER OPERATIONS ===

export function createUser(email: string, name?: string): User {
  const db = loadDB();
  const id = generateId();
  const now = Math.floor(Date.now() / 1000);
  const user: User = {
    id,
    email,
    name: name || null,
    plan: 'free',
    razorpay_customer_id: null,
    created_at: now,
    updated_at: now,
  };
  db.users[id] = user;
  saveDB();
  return user;
}

export function getUser(id: string): User | null {
  const db = loadDB();
  return db.users[id] || null;
}

export function getUserByEmail(email: string): User | null {
  const db = loadDB();
  for (const user of Object.values(db.users)) {
    if (user.email === email) return user;
  }
  return null;
}

export function updateUserPlan(userId: string, plan: string): void {
  const db = loadDB();
  if (db.users[userId]) {
    db.users[userId].plan = plan;
    db.users[userId].updated_at = Math.floor(Date.now() / 1000);
    saveDB();
  }
}

export function updateUserRazorpayCustomer(userId: string, customerId: string): void {
  const db = loadDB();
  if (db.users[userId]) {
    db.users[userId].razorpay_customer_id = customerId;
    db.users[userId].updated_at = Math.floor(Date.now() / 1000);
    saveDB();
  }
}

// === SUBSCRIPTION OPERATIONS ===

export function createSubscriptionRecord(params: {
  userId: string;
  razorpaySubscriptionId: string;
  razorpayPlanId: string;
  plan: string;
}): void {
  const db = loadDB();
  const id = generateId();
  const now = Math.floor(Date.now() / 1000);
  db.subscriptions[id] = {
    id,
    user_id: params.userId,
    razorpay_subscription_id: params.razorpaySubscriptionId,
    razorpay_plan_id: params.razorpayPlanId,
    plan: params.plan,
    status: 'created',
    current_period_start: null,
    current_period_end: null,
    created_at: now,
    updated_at: now,
  };
  saveDB();
}

export function updateSubscriptionStatus(subscriptionId: string, status: string): void {
  const db = loadDB();
  for (const sub of Object.values(db.subscriptions)) {
    if (sub.razorpay_subscription_id === subscriptionId) {
      sub.status = status;
      sub.updated_at = Math.floor(Date.now() / 1000);
      saveDB();
      return;
    }
  }
}

export function getActiveSubscription(userId: string): SubscriptionRecord | null {
  const db = loadDB();
  const subs = Object.values(db.subscriptions)
    .filter(s => s.user_id === userId && ['active', 'created', 'authenticated'].includes(s.status))
    .sort((a, b) => b.created_at - a.created_at);
  return subs[0] || null;
}

// === API KEY OPERATIONS ===

export function createApiKey(userId: string, name = 'default'): { key: string; id: string } {
  const db = loadDB();
  const id = generateId();
  const rawKey = `tmc_${crypto.randomBytes(32).toString('hex')}`;
  const keyHash = crypto.createHash('sha256').update(rawKey).digest('hex');
  const keyPrefix = rawKey.substring(0, 12);

  db.api_keys[id] = {
    id,
    user_id: userId,
    key_hash: keyHash,
    key_prefix: keyPrefix,
    name,
    last_used: null,
    created_at: Math.floor(Date.now() / 1000),
  };
  saveDB();
  return { key: rawKey, id };
}

export function revokeApiKey(keyId: string): void {
  const db = loadDB();
  delete db.api_keys[keyId];
  saveDB();
}

export function validateApiKey(rawKey: string): { userId: string; user: User } | null {
  const db = loadDB();
  const keyHash = crypto.createHash('sha256').update(rawKey).digest('hex');
  for (const record of Object.values(db.api_keys)) {
    if (record.key_hash === keyHash) {
      // Update last used
      record.last_used = Math.floor(Date.now() / 1000);
      saveDB();
      const user = getUser(record.user_id);
      if (!user) return null;
      return { userId: record.user_id, user };
    }
  }
  return null;
}

export function listApiKeys(userId: string): ApiKeyRecord[] {
  const db = loadDB();
  return Object.values(db.api_keys)
    .filter(k => k.user_id === userId)
    .map(k => ({ ...k, key_hash: '' })) // don't expose hash
    .sort((a, b) => b.created_at - a.created_at);
}

// === USAGE TRACKING ===

export function getTodayUsage(userId: string): { query_count: number; input_tokens: number; output_tokens: number } {
  const db = loadDB();
  const today = new Date().toISOString().split('T')[0];
  const key = `${userId}_${today}`;
  const record = db.usage[key];
  return record || { query_count: 0, input_tokens: 0, output_tokens: 0 };
}

export function getMonthUsage(userId: string): { totalQueries: number; totalInputTokens: number; totalOutputTokens: number } {
  const db = loadDB();
  const monthStart = new Date();
  monthStart.setDate(1);
  const monthStartStr = monthStart.toISOString().split('T')[0];

  let totalQueries = 0;
  let totalInputTokens = 0;
  let totalOutputTokens = 0;

  for (const [key, record] of Object.entries(db.usage)) {
    if (key.startsWith(userId) && record.query_date >= monthStartStr) {
      totalQueries += record.query_count;
      totalInputTokens += record.input_tokens;
      totalOutputTokens += record.output_tokens;
    }
  }

  return { totalQueries, totalInputTokens, totalOutputTokens };
}

export function incrementUsage(userId: string, inputTokens: number, outputTokens: number): void {
  const db = loadDB();
  const today = new Date().toISOString().split('T')[0];
  const key = `${userId}_${today}`;

  if (db.usage[key]) {
    db.usage[key].query_count += 1;
    db.usage[key].input_tokens += inputTokens;
    db.usage[key].output_tokens += outputTokens;
  } else {
    db.usage[key] = {
      user_id: userId,
      query_date: today,
      query_count: 1,
      input_tokens: inputTokens,
      output_tokens: outputTokens,
    };
  }
  saveDB();
}

// === PAYMENT OPERATIONS ===

export function recordPayment(params: {
  userId?: string;
  razorpayOrderId: string;
  amount: number;
  currency?: string;
  status?: string;
  type?: string;
  plan?: string;
}): void {
  const db = loadDB();
  const id = generateId();
  db.payments[id] = {
    id,
    user_id: params.userId || null,
    razorpay_order_id: params.razorpayOrderId,
    razorpay_payment_id: null,
    razorpay_signature: null,
    amount: params.amount,
    currency: params.currency || 'INR',
    status: params.status || 'created',
    type: params.type || 'subscription',
    plan: params.plan || null,
    created_at: Math.floor(Date.now() / 1000),
  };
  saveDB();
}

export function updatePaymentStatus(razorpayOrderId: string, status: string, paymentId?: string, signature?: string): void {
  const db = loadDB();
  for (const payment of Object.values(db.payments)) {
    if (payment.razorpay_order_id === razorpayOrderId) {
      payment.status = status;
      payment.razorpay_payment_id = paymentId || null;
      payment.razorpay_signature = signature || null;
      saveDB();
      return;
    }
  }
}

// === TYPES ===

export interface User {
  id: string;
  email: string;
  name: string | null;
  plan: string;
  razorpay_customer_id: string | null;
  created_at: number;
  updated_at: number;
}

export interface SubscriptionRecord {
  id: string;
  user_id: string;
  razorpay_subscription_id: string;
  razorpay_plan_id: string;
  plan: string;
  status: string;
  current_period_start: number | null;
  current_period_end: number | null;
  created_at: number;
  updated_at: number;
}

export interface ApiKeyRecord {
  id: string;
  user_id: string;
  key_hash: string;
  key_prefix: string;
  name: string;
  last_used: number | null;
  created_at: number;
}