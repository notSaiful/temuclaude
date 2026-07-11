// Check if user can send a query (rolling rate checks & weekly credits)
// POST /api/usage/check
// Body: { identifier: string } — email or anonymous fingerprint
// Returns: { allowed: boolean, remaining: number, plan: string, message?: string }

import { NextRequest, NextResponse } from 'next/server';
import {
  getOrCreateUserByEmailAsync,
  incrementUsageAsync,
  getRollingWindowUsageAsync,
  verifyAndRenewWeeklyCreditsAsync
} from '@/lib/db';
import { PLAN_LIMITS, ROLLING_WINDOW_HOURS } from '@/lib/plans';
import { getAuthenticatedSupabaseUser } from '@/lib/supabase-server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    const auth = await getAuthenticatedSupabaseUser(req);
    if ('error' in auth) return NextResponse.json({ error: auth.error }, { status: auth.status });
    const email = auth.user.email?.trim().toLowerCase();
    if (!email) return NextResponse.json({ error: 'Authenticated user has no email address' }, { status: 400 });
    const initialUser = await getOrCreateUserByEmailAsync(email);

    // Dynamic weekly reset check
    const user = (await verifyAndRenewWeeklyCreditsAsync(initialUser.id)) || initialUser;

    const limits = PLAN_LIMITS[user.plan as keyof typeof PLAN_LIMITS] || PLAN_LIMITS.free;
    const rollingUsage = await getRollingWindowUsageAsync(user.id, ROLLING_WINDOW_HOURS);

    // 1. Check absolute credit exhaustion
    if (user.credit_balance <= 0) {
      return NextResponse.json({
        allowed: false,
        remaining: 0,
        plan: user.plan,
        creditBalance: 0,
        message: `You've run out of credits. Please purchase a credit top-up or wait for your weekly allocation to renew.`,
        upgradeUrl: '/pricing',
      });
    }

    // 2. Check rolling window query limits (primarily for Free tier)
    if (limits.rollingQueries !== Infinity && rollingUsage.query_count >= limits.rollingQueries) {
      return NextResponse.json({
        allowed: false,
        remaining: 0,
        plan: user.plan,
        creditBalance: user.credit_balance,
        message: `You've reached your rolling limit of ${limits.rollingQueries} queries per 5 hours. Capacity recovers gradually as older queries age out.`,
        upgradeUrl: '/pricing',
      });
    }

    return NextResponse.json({
      allowed: true,
      remaining: limits.rollingQueries === Infinity ? null : limits.rollingQueries - rollingUsage.query_count,
      plan: user.plan,
      creditBalance: user.credit_balance,
      rollingQueries: rollingUsage.query_count,
      rollingLimit: limits.rollingQueries === Infinity ? null : limits.rollingQueries,
      creditsResetAt: user.credits_reset_at,
    });
  } catch (error: any) {
    console.error('Usage check error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

// Increment usage after a query is sent
// PUT /api/usage/check
export async function PUT(req: NextRequest) {
  try {
    const body = await req.json();
    const { inputTokens, outputTokens, modelName } = body;
    const auth = await getAuthenticatedSupabaseUser(req);
    if ('error' in auth) return NextResponse.json({ error: auth.error }, { status: auth.status });
    const email = auth.user.email?.trim().toLowerCase();
    if (!email) return NextResponse.json({ error: 'Authenticated user has no email address' }, { status: 400 });
    const initialUser = await getOrCreateUserByEmailAsync(email);
    const user = (await verifyAndRenewWeeklyCreditsAsync(initialUser.id)) || initialUser;

    const limits = PLAN_LIMITS[user.plan as keyof typeof PLAN_LIMITS] || PLAN_LIMITS.free;
    const rollingBefore = await getRollingWindowUsageAsync(user.id, ROLLING_WINDOW_HOURS);
    if (user.credit_balance <= 0 || (limits.rollingQueries !== Infinity && rollingBefore.query_count >= limits.rollingQueries)) {
      return NextResponse.json({ error: 'Usage limit reached', allowed: false }, { status: 429 });
    }

    // Deduct credits and log timestamped event with model metadata
    await incrementUsageAsync(user.id, inputTokens || 1000, outputTokens || 1000, modelName);

    const rollingUsage = await getRollingWindowUsageAsync(user.id, ROLLING_WINDOW_HOURS);

    return NextResponse.json({
      success: true,
      rollingQueries: rollingUsage.query_count,
      remaining: limits.rollingQueries === Infinity ? null : Math.max(0, limits.rollingQueries - rollingUsage.query_count),
    });
  } catch (error: any) {
    console.error('Usage increment error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
