// Database layer for users, subscriptions, usage tracking, API keys, and payments.
// Production must use Supabase. The JSON store is only a local/dev fallback unless
// ALLOW_EPHEMERAL_DB=true is explicitly set for a temporary diagnostic window.

import crypto from 'crypto';
import fs from 'fs';
import path from 'path';
import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import { PLAN_LIMITS, type PlanId } from './plans';
import { nextWeeklyResetAt, rollingWindowCutoff, WEEKLY_WINDOW_SECONDS } from './usage-windows';

function weeklyCreditsForPlan(plan: string): number {
  return PLAN_LIMITS[plan as PlanId]?.weeklyCredits ?? PLAN_LIMITS.free.weeklyCredits;
}

interface DBSchema {
  users: Record<string, User>;
  subscriptions: Record<string, SubscriptionRecord>;
  api_keys: Record<string, ApiKeyRecord>;
  usage: Record<string, UsageRecord>; // key: userId_date
  events: Record<string, UsageEvent>; // key: eventId
  payments: Record<string, PaymentRecord>;
}

interface UsageRecord {
  user_id: string;
  query_date: string;
  query_count: number;
  input_tokens: number;
  output_tokens: number;
}

export interface UsageEvent {
  id: string;
  user_id: string;
  created_at: number;
  credits_spent: number;
  query_count: number;
  model_name?: string;
  saved_usd?: number;
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
let supabaseAdmin: SupabaseClient | null | undefined;

function allowEphemeralDbFallback(): boolean {
  return ['1', 'true', 'yes', 'on'].includes((process.env.ALLOW_EPHEMERAL_DB || '').toLowerCase());
}

function isProductionRuntime(): boolean {
  return process.env.NODE_ENV === 'production' || process.env.VERCEL_ENV === 'production';
}

function assertPersistentDbAvailable(): void {
  if (isProductionRuntime() && !allowEphemeralDbFallback()) {
    throw new Error(
      'Supabase admin credentials are required in production. Set NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SECRET_KEY/SUPABASE_SERVICE_ROLE_KEY, or explicitly set ALLOW_EPHEMERAL_DB=true only for temporary diagnostics.',
    );
  }
}

function getSupabaseAdminClient(): SupabaseClient | null {
  if (supabaseAdmin !== undefined) return supabaseAdmin;

  const url = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL;
  const serviceKey =
    process.env.SUPABASE_SECRET_KEY ||
    process.env.SUPABASE_SERVICE_ROLE_KEY ||
    process.env.SUPABASE_SERVICE_KEY;

  if (!url || !serviceKey) {
    assertPersistentDbAvailable();
    supabaseAdmin = null;
    return supabaseAdmin;
  }

  supabaseAdmin = createClient(url, serviceKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  });
  return supabaseAdmin;
}

export function isSupabaseDbConfigured(): boolean {
  try {
    return Boolean(getSupabaseAdminClient());
  } catch {
    return false;
  }
}

function loadDB(): DBSchema {
  assertPersistentDbAvailable();
  if (dbCache) return dbCache;

  try {
    const data = fs.readFileSync(DB_PATH, 'utf-8');
    dbCache = JSON.parse(data);
    if (dbCache && !dbCache.events) {
      dbCache.events = {};
    }
  } catch {
    // File doesn't exist, create empty DB
    dbCache = {
      users: {},
      subscriptions: {},
      api_keys: {},
      usage: {},
      events: {},
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
    credit_balance: PLAN_LIMITS.free.weeklyCredits,
    credits_reset_at: now + 7 * 24 * 3600,
    weekly_credit_allocation: PLAN_LIMITS.free.weeklyCredits,
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
    const weeklyAllocation = weeklyCreditsForPlan(plan);
    db.users[userId].plan = plan;
    db.users[userId].weekly_credit_allocation = weeklyAllocation;
    db.users[userId].credit_balance = weeklyAllocation;
    db.users[userId].credits_reset_at = Math.floor(Date.now() / 1000) + 7 * 24 * 3600;
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

function apiKeyPepper(): string {
  const pepper = process.env.TEMUCLAUDE_API_KEY_PEPPER || process.env.SUPABASE_SECRET_KEY;
  if (pepper) return pepper;
  if (process.env.NODE_ENV === 'production') {
    throw new Error('TEMUCLAUDE_API_KEY_PEPPER or SUPABASE_SECRET_KEY is required in production');
  }
  return 'temuclaude-development-only-api-key-pepper';
}

function hashApiKey(rawKey: string): string {
  return crypto.createHmac('sha256', apiKeyPepper()).update(rawKey).digest('hex');
}

function legacyApiKeyHash(rawKey: string): string {
  // Existing records used SHA-256 over 256-bit random API keys. Keep this only
  // for a one-use migration to the keyed hash above; it is not used for newly
  // created records.
  return crypto.createHash('sha256').update(rawKey).digest('hex'); // lgtm[js/insufficient-password-hash]
}

export function createApiKey(userId: string, name = 'default'): { key: string; id: string } {
  const db = loadDB();
  const id = generateId();
  const rawKey = `tmc_${crypto.randomBytes(32).toString('hex')}`;
  const keyHash = hashApiKey(rawKey);
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
  const keyHash = hashApiKey(rawKey);
  const legacyHash = legacyApiKeyHash(rawKey);
  for (const record of Object.values(db.api_keys)) {
    if (record.key_hash === keyHash || record.key_hash === legacyHash) {
      record.key_hash = keyHash;
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

type ModelActivity = string | string[] | undefined;

function modelActivityEntries(modelActivity: ModelActivity): string[] {
  const values = Array.isArray(modelActivity) ? modelActivity : [modelActivity];
  const models = values.filter((model): model is string => typeof model === 'string' && model.trim().length > 0);
  // Retain historical rows when no model attribution exists, but never invent a
  // customer-facing routing tier such as "hard" or "fallback".
  return models.length > 0 ? models : ['unattributed-legacy'];
}

export function incrementUsage(userId: string, inputTokens: number, outputTokens: number, modelActivity?: ModelActivity): void {
  const db = loadDB();
  const today = new Date().toISOString().split('T')[0];
  const key = `${userId}_${today}`;
  const now = Math.floor(Date.now() / 1000);

  // 1. Maintain old daily summaries for safety/compat
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

  // 2. Add high-res rolling window event
  const creditsSpent = inputTokens + outputTokens;
  const savedUsd = creditsSpent * 0.00004906;
  if (!db.events) db.events = {};
  modelActivityEntries(modelActivity).forEach((modelName, index) => {
    const eventId = generateId();
    db.events[eventId] = {
      id: eventId,
      user_id: userId,
      created_at: now,
      // A request is billed once. Extra per-model events are telemetry only.
      credits_spent: index === 0 ? creditsSpent : 0,
      query_count: index === 0 ? 1 : 0,
      model_name: modelName,
      saved_usd: index === 0 ? savedUsd : 0,
    };
  });

  // 3. Deduct from credit balance
  if (db.users[userId]) {
    db.users[userId].credit_balance = Math.max(0, (db.users[userId].credit_balance ?? 50000) - creditsSpent);
    db.users[userId].updated_at = now;
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

// === SUPABASE-BACKED ASYNC OPERATIONS ===
// Production uses Supabase so customer API keys survive serverless restarts.
// Local/dev falls back to the JSON store above when a Supabase admin key is absent.

function nowUnix(): number {
  return Math.floor(Date.now() / 1000);
}

function normalizeEmail(email: string): string {
  return email.trim().toLowerCase();
}

function mapUser(row: any): User {
  const plan = row.plan || 'free';
  const allocation = Number(row.weekly_credit_allocation ?? weeklyCreditsForPlan(plan));
  return {
    id: row.id,
    email: row.email,
    name: row.name ?? null,
    plan,
    razorpay_customer_id: row.razorpay_customer_id ?? null,
    credit_balance: Number(row.credit_balance ?? allocation),
    credits_reset_at: Number(row.credits_reset_at ?? (nowUnix() + WEEKLY_WINDOW_SECONDS)),
    weekly_credit_allocation: allocation,
    created_at: Number(row.created_at || nowUnix()),
    updated_at: Number(row.updated_at || nowUnix()),
  };
}

function mapApiKey(row: any): ApiKeyRecord {
  return {
    id: row.id,
    user_id: row.user_id,
    key_hash: row.key_hash || '',
    key_prefix: row.key_prefix,
    name: row.name || 'default',
    last_used: row.last_used === null || row.last_used === undefined ? null : Number(row.last_used),
    created_at: Number(row.created_at || nowUnix()),
  };
}

export async function getUserAsync(id: string): Promise<User | null> {
  const client = getSupabaseAdminClient();
  if (!client) return getUser(id);

  const { data, error } = await client
    .from('temuclaude_users')
    .select('*')
    .eq('id', id)
    .maybeSingle();

  if (error) throw error;
  return data ? mapUser(data) : null;
}

export async function getUserByEmailAsync(email: string): Promise<User | null> {
  const client = getSupabaseAdminClient();
  const normalized = normalizeEmail(email);
  if (!client) return getUserByEmail(normalized);

  const { data, error } = await client
    .from('temuclaude_users')
    .select('*')
    .eq('email', normalized)
    .maybeSingle();

  if (error) throw error;
  return data ? mapUser(data) : null;
}

export async function createUserAsync(email: string, name?: string): Promise<User> {
  const client = getSupabaseAdminClient();
  const normalized = normalizeEmail(email);
  if (!client) return createUser(normalized, name);

  const now = nowUnix();
  const user: User = {
    id: generateId(),
    email: normalized,
    name: name || null,
    plan: 'free',
    razorpay_customer_id: null,
    credit_balance: PLAN_LIMITS.free.weeklyCredits,
    credits_reset_at: now + 7 * 24 * 3600,
    weekly_credit_allocation: PLAN_LIMITS.free.weeklyCredits,
    created_at: now,
    updated_at: now,
  };

  const { data, error } = await client
    .from('temuclaude_users')
    .insert(user)
    .select()
    .single();

  if (error) {
    const existing = await getUserByEmailAsync(normalized);
    if (existing) return existing;
    throw error;
  }

  return mapUser(data);
}

export async function getOrCreateUserByEmailAsync(email: string, name?: string): Promise<User> {
  return (await getUserByEmailAsync(email)) || createUserAsync(email, name);
}

export async function updateUserPlanAsync(userId: string, plan: string): Promise<void> {
  const client = getSupabaseAdminClient();
  if (!client) {
    updateUserPlan(userId, plan);
    return;
  }

  const weeklyAllocation = weeklyCreditsForPlan(plan);
  const { error } = await client
    .from('temuclaude_users')
    .update({
      plan,
      weekly_credit_allocation: weeklyAllocation,
      credit_balance: weeklyAllocation,
      credits_reset_at: nowUnix() + 7 * 24 * 3600,
      updated_at: nowUnix()
    })
    .eq('id', userId);

  if (error) throw error;
}

export async function updateUserRazorpayCustomerAsync(userId: string, customerId: string): Promise<void> {
  const client = getSupabaseAdminClient();
  if (!client) {
    updateUserRazorpayCustomer(userId, customerId);
    return;
  }

  const { error } = await client
    .from('temuclaude_users')
    .update({ razorpay_customer_id: customerId, updated_at: nowUnix() })
    .eq('id', userId);

  if (error) throw error;
}

export async function createSubscriptionRecordAsync(params: {
  userId: string;
  razorpaySubscriptionId: string;
  razorpayPlanId: string;
  plan: string;
}): Promise<void> {
  const client = getSupabaseAdminClient();
  if (!client) {
    createSubscriptionRecord(params);
    return;
  }

  const now = nowUnix();
  const { error } = await client
    .from('temuclaude_subscriptions')
    .insert({
      id: generateId(),
      user_id: params.userId,
      razorpay_subscription_id: params.razorpaySubscriptionId,
      razorpay_plan_id: params.razorpayPlanId,
      plan: params.plan,
      status: 'created',
      current_period_start: null,
      current_period_end: null,
      created_at: now,
      updated_at: now,
    });

  if (error) throw error;
}

export async function updateSubscriptionStatusAsync(subscriptionId: string, status: string): Promise<void> {
  const client = getSupabaseAdminClient();
  if (!client) {
    updateSubscriptionStatus(subscriptionId, status);
    return;
  }

  const { error } = await client
    .from('temuclaude_subscriptions')
    .update({ status, updated_at: nowUnix() })
    .eq('razorpay_subscription_id', subscriptionId);

  if (error) throw error;
}

export async function getActiveSubscriptionAsync(userId: string): Promise<SubscriptionRecord | null> {
  const client = getSupabaseAdminClient();
  if (!client) return getActiveSubscription(userId);

  const { data, error } = await client
    .from('temuclaude_subscriptions')
    .select('*')
    .eq('user_id', userId)
    .in('status', ['active', 'created', 'authenticated'])
    .order('created_at', { ascending: false })
    .limit(1)
    .maybeSingle();

  if (error) throw error;
  return data as SubscriptionRecord | null;
}

export async function createApiKeyAsync(userId: string, name = 'default'): Promise<{ key: string; id: string }> {
  const client = getSupabaseAdminClient();
  if (!client) return createApiKey(userId, name);

  const id = generateId();
  const rawKey = `tmc_${crypto.randomBytes(32).toString('hex')}`;
  const keyHash = hashApiKey(rawKey);
  const keyPrefix = rawKey.substring(0, 12);

  const { error } = await client
    .from('temuclaude_api_keys')
    .insert({
      id,
      user_id: userId,
      key_hash: keyHash,
      key_prefix: keyPrefix,
      name,
      last_used: null,
      created_at: nowUnix(),
    });

  if (error) throw error;
  return { key: rawKey, id };
}

export async function validateApiKeyAsync(rawKey: string): Promise<{ userId: string; user: User } | null> {
  const client = getSupabaseAdminClient();
  if (!client) return validateApiKey(rawKey);

  const keyHash = hashApiKey(rawKey);
  const legacyHash = legacyApiKeyHash(rawKey);
  const { data, error } = await client
    .from('temuclaude_api_keys')
    .select('*')
    .in('key_hash', [keyHash, legacyHash])
    .maybeSingle();

  if (error) throw error;
  if (!data) return null;

  await client
    .from('temuclaude_api_keys')
    .update({ key_hash: keyHash, last_used: nowUnix() })
    .eq('id', data.id);

  const user = await getUserAsync(data.user_id);
  if (!user) return null;
  return { userId: data.user_id, user };
}

export async function listApiKeysAsync(userId: string): Promise<ApiKeyRecord[]> {
  const client = getSupabaseAdminClient();
  if (!client) return listApiKeys(userId);

  const { data, error } = await client
    .from('temuclaude_api_keys')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false });

  if (error) throw error;
  return (data || []).map((row) => ({ ...mapApiKey(row), key_hash: '' }));
}

export async function revokeApiKeyAsync(keyId: string): Promise<void> {
  const client = getSupabaseAdminClient();
  if (!client) {
    revokeApiKey(keyId);
    return;
  }

  const { error } = await client
    .from('temuclaude_api_keys')
    .delete()
    .eq('id', keyId);

  if (error) throw error;
}

export async function getTodayUsageAsync(userId: string): Promise<{ query_count: number; input_tokens: number; output_tokens: number }> {
  const client = getSupabaseAdminClient();
  if (!client) return getTodayUsage(userId);

  const today = new Date().toISOString().split('T')[0];
  const { data, error } = await client
    .from('temuclaude_usage')
    .select('*')
    .eq('user_id', userId)
    .eq('query_date', today)
    .maybeSingle();

  if (error) throw error;
  return data || { query_count: 0, input_tokens: 0, output_tokens: 0 };
}

export async function getMonthUsageAsync(userId: string): Promise<{ totalQueries: number; totalInputTokens: number; totalOutputTokens: number }> {
  const client = getSupabaseAdminClient();
  if (!client) return getMonthUsage(userId);

  const monthStart = new Date();
  monthStart.setDate(1);
  const monthStartStr = monthStart.toISOString().split('T')[0];
  const { data, error } = await client
    .from('temuclaude_usage')
    .select('query_count,input_tokens,output_tokens')
    .eq('user_id', userId)
    .gte('query_date', monthStartStr);

  if (error) throw error;

  return (data || []).reduce(
    (sum, row) => ({
      totalQueries: sum.totalQueries + Number(row.query_count || 0),
      totalInputTokens: sum.totalInputTokens + Number(row.input_tokens || 0),
      totalOutputTokens: sum.totalOutputTokens + Number(row.output_tokens || 0),
    }),
    { totalQueries: 0, totalInputTokens: 0, totalOutputTokens: 0 },
  );
}

export async function incrementUsageAsync(userId: string, inputTokens: number, outputTokens: number, modelActivity?: ModelActivity): Promise<void> {
  const client = getSupabaseAdminClient();
  if (!client) {
    incrementUsage(userId, inputTokens, outputTokens, modelActivity);
    return;
  }

  const now = nowUnix();
  const creditsSpent = inputTokens + outputTokens;
  const savedUsd = creditsSpent * 0.00004906;
  const models = modelActivityEntries(modelActivity);

  // 1. Log one event per actual model invocation. Only the first entry carries
  // billing and request-count values, so model transparency cannot inflate
  // quotas, credit deductions, or savings totals.
  const { error: eventErr } = await client
    .from('temuclaude_usage_events')
    .insert(models.map((modelName, index) => ({
      id: generateId(),
      user_id: userId,
      created_at: now,
      credits_spent: index === 0 ? creditsSpent : 0,
      query_count: index === 0 ? 1 : 0,
      model_name: modelName,
      saved_usd: index === 0 ? savedUsd : 0,
    })));

  if (eventErr) {
    throw new Error(`Usage event ledger write failed: ${eventErr.message}`);
  }

  // 2. Deduct credits from user profile
  const { data: userRow } = await client
    .from('temuclaude_users')
    .select('credit_balance')
    .eq('id', userId)
    .maybeSingle();

  if (userRow) {
    const newBalance = Math.max(0, Number(userRow.credit_balance ?? 0) - creditsSpent);
    await client
      .from('temuclaude_users')
      .update({ credit_balance: newBalance, updated_at: now })
      .eq('id', userId);
  }

  // 3. Keep old daily usage summaries in sync
  const today = new Date().toISOString().split('T')[0];
  const current = await getTodayUsageAsync(userId);
  const { error } = await client
    .from('temuclaude_usage')
    .upsert({
      user_id: userId,
      query_date: today,
      query_count: Number(current.query_count || 0) + 1,
      input_tokens: Number(current.input_tokens || 0) + inputTokens,
      output_tokens: Number(current.output_tokens || 0) + outputTokens,
    }, { onConflict: 'user_id,query_date' });

  if (error) throw error;
}

export async function getRollingWindowUsageAsync(userId: string, hours = 5): Promise<{ query_count: number; credits_spent: number; oldest_event_at: number | null }> {
  const client = getSupabaseAdminClient();
  const cutoff = rollingWindowCutoff(nowUnix(), hours);

  if (!client) {
    const db = loadDB();
    let query_count = 0;
    let credits_spent = 0;
    let oldest_event_at: number | null = null;

    for (const event of Object.values(db.events || {})) {
      if (event.user_id === userId && event.created_at >= cutoff) {
        query_count += event.query_count;
        credits_spent += event.credits_spent;
        oldest_event_at = oldest_event_at === null ? event.created_at : Math.min(oldest_event_at, event.created_at);
      }
    }
    return { query_count, credits_spent, oldest_event_at };
  }

  const { data, error } = await client
    .from('temuclaude_usage_events')
    .select('created_at, query_count, credits_spent')
    .eq('user_id', userId)
    .gte('created_at', cutoff)
    .order('created_at', { ascending: true });

  // Daily summaries have no per-request timestamps and therefore cannot
  // truthfully answer a rolling-window query. Failing closed prevents an
  // incorrect dashboard value or accidental quota bypass when the event ledger
  // has not been migrated.
  if (error) throw new Error(`Usage event ledger is unavailable: ${error.message}`);

  let query_count = 0;
  let credits_spent = 0;
  let oldest_event_at: number | null = null;
  for (const row of data || []) {
    query_count += Number(row.query_count || 0);
    credits_spent += Number(row.credits_spent || 0);
    const timestamp = Number(row.created_at || 0);
    if (Number(row.query_count || 0) > 0 && timestamp > 0) {
      oldest_event_at = oldest_event_at === null ? timestamp : Math.min(oldest_event_at, timestamp);
    }
  }
  return { query_count, credits_spent, oldest_event_at };
}

export async function verifyAndRenewWeeklyCreditsAsync(userId: string): Promise<User | null> {
  const client = getSupabaseAdminClient();
  const now = nowUnix();

  if (!client) {
    const db = loadDB();
    const user = db.users[userId];
    if (!user) return null;

    if (now >= (user.credits_reset_at || 0)) {
      user.credit_balance = user.weekly_credit_allocation || weeklyCreditsForPlan(user.plan);
      user.credits_reset_at = nextWeeklyResetAt(user.credits_reset_at, now);
      user.updated_at = now;
      saveDB();
    }
    return user;
  }

  const { data: userRow, error: fetchErr } = await client
    .from('temuclaude_users')
    .select('*')
    .eq('id', userId)
    .maybeSingle();

  if (fetchErr || !userRow) return null;
  const user = mapUser(userRow);

  const weeklyAllocation = weeklyCreditsForPlan(user.plan);
  const needsPolicySync = user.weekly_credit_allocation !== weeklyAllocation;

  if (now >= user.credits_reset_at || needsPolicySync) {
    const newBalance = now >= user.credits_reset_at
      ? weeklyAllocation
      : Math.min(user.credit_balance, weeklyAllocation);
    const newReset = now >= user.credits_reset_at
      ? nextWeeklyResetAt(user.credits_reset_at, now)
      : user.credits_reset_at;

    const { data: updatedRow, error: updateErr } = await client
      .from('temuclaude_users')
      .update({
        credit_balance: newBalance,
        weekly_credit_allocation: weeklyAllocation,
        credits_reset_at: newReset,
        updated_at: now
      })
      .eq('id', userId)
      .select()
      .single();

    if (updateErr) throw updateErr;
    return mapUser(updatedRow);
  }

  return user;
}

export async function addCreditsToUserAsync(userId: string, amount: number): Promise<void> {
  const client = getSupabaseAdminClient();
  const now = nowUnix();

  if (!client) {
    const db = loadDB();
    if (db.users[userId]) {
      db.users[userId].credit_balance = (db.users[userId].credit_balance || 0) + amount;
      db.users[userId].updated_at = now;
      saveDB();
    }
    return;
  }

  const { data: userRow } = await client
    .from('temuclaude_users')
    .select('credit_balance')
    .eq('id', userId)
    .maybeSingle();

  if (userRow) {
    const newBalance = Number(userRow.credit_balance ?? 0) + amount;
    await client
      .from('temuclaude_users')
      .update({ credit_balance: newBalance, updated_at: now })
      .eq('id', userId);
  }
}

export async function recordPaymentAsync(params: {
  userId?: string;
  razorpayOrderId: string;
  amount: number;
  currency?: string;
  status?: string;
  type?: string;
  plan?: string;
}): Promise<void> {
  const client = getSupabaseAdminClient();
  if (!client) {
    recordPayment(params);
    return;
  }

  const { error } = await client
    .from('temuclaude_payments')
    .insert({
      id: generateId(),
      user_id: params.userId || null,
      razorpay_order_id: params.razorpayOrderId,
      razorpay_payment_id: null,
      razorpay_signature: null,
      amount: params.amount,
      currency: params.currency || 'INR',
      status: params.status || 'created',
      type: params.type || 'subscription',
      plan: params.plan || null,
      created_at: nowUnix(),
    });

  if (error) throw error;
}

export async function updatePaymentStatusAsync(razorpayOrderId: string, status: string, paymentId?: string, signature?: string): Promise<void> {
  const client = getSupabaseAdminClient();
  if (!client) {
    updatePaymentStatus(razorpayOrderId, status, paymentId, signature);
    return;
  }

  const { error } = await client
    .from('temuclaude_payments')
    .update({
      status,
      razorpay_payment_id: paymentId || null,
      razorpay_signature: signature || null,
    })
    .eq('razorpay_order_id', razorpayOrderId);

  if (error) throw error;
}

export async function getSavingsAndModelMixAsync(userId: string): Promise<{
  totalSavedUSD: number;
  modelMix: Record<string, number>;
}> {
  const client = getSupabaseAdminClient();
  let events: UsageEvent[] = [];

  if (!client) {
    // Read from mock filesystem
    const db = loadDB();
    if (db.events) {
      events = Object.values(db.events).filter((e) => e.user_id === userId);
    }
  } else {
    // Read from production database
    const { data, error } = await client
      .from('temuclaude_usage_events')
      .select('model_name, saved_usd, credits_spent')
      .eq('user_id', userId);

    if (!error && data) {
      events = data as UsageEvent[];
    }
  }

  let totalSavedUSD = 0;
  const modelMix: Record<string, number> = {};

  for (const event of events) {
    // Fallback: calculate saved_usd dynamically from credits_spent if it's not stored
    const saved = event.saved_usd !== undefined ? Number(event.saved_usd) : Number(event.credits_spent || 0) * 0.00004906;
    totalSavedUSD += saved;

    const model = event.model_name || 'unattributed-legacy';
    modelMix[model] = (modelMix[model] || 0) + 1;
  }

  return {
    totalSavedUSD,
    modelMix,
  };
}

// === TYPES ===

export interface User {
  id: string;
  email: string;
  name: string | null;
  plan: string;
  razorpay_customer_id: string | null;
  credit_balance: number;
  credits_reset_at: number;
  weekly_credit_allocation: number;
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
