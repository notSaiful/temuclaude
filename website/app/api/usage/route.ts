// Get current user's usage and plan limits
// GET /api/usage
// Headers: Authorization: Bearer <api_key> OR x-api-key: <api_key>

import { NextRequest, NextResponse } from 'next/server';
import {
  validateApiKeyAsync,
  getTodayUsageAsync,
  getMonthUsageAsync,
  getRollingWindowUsageAsync,
  verifyAndRenewWeeklyCreditsAsync
} from '@/lib/db';
import { PLAN_LIMITS, PLANS } from '@/lib/plans';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    // Get API key from header
    const apiKey = req.headers.get('x-api-key') ||
      req.headers.get('authorization')?.replace('Bearer ', '');

    if (!apiKey) {
      return NextResponse.json({ error: 'Missing API key' }, { status: 401 });
    }

    const valid = await validateApiKeyAsync(apiKey);
    if (!valid) {
      return NextResponse.json({ error: 'Invalid API key' }, { status: 401 });
    }

    const { userId, user: initialUser } = valid;

    // Check/renew weekly credits
    const user = (await verifyAndRenewWeeklyCreditsAsync(userId)) || initialUser;

    const plan = PLANS[user.plan as keyof typeof PLANS] || PLANS.free;
    const limits = PLAN_LIMITS[user.plan as keyof typeof PLAN_LIMITS] || PLAN_LIMITS.free;
    const todayUsage = await getTodayUsageAsync(userId);
    const monthUsage = await getMonthUsageAsync(userId);
    const rollingUsage = await getRollingWindowUsageAsync(userId, 5);

    return NextResponse.json({
      plan: plan.id,
      planName: plan.name,
      creditBalance: user.credit_balance,
      weeklyCreditAllocation: user.weekly_credit_allocation,
      creditsResetAt: user.credits_reset_at,
      queriesToday: todayUsage.query_count,
      queriesThisMonth: monthUsage.totalQueries,
      rollingQueries: rollingUsage.query_count,
      rollingLimit: limits.rollingQueries === Infinity ? null : limits.rollingQueries,
      weeklyCredits: limits.weeklyCredits,
      monthlyCredits: plan.monthlyCredits,
      overagePerMillionCreditsUSD: plan.overagePerMillionCreditsUSD,
      tokensThisMonth: {
        input: monthUsage.totalInputTokens,
        output: monthUsage.totalOutputTokens,
      },
      apiAccess: plan.apiAccess,
    });
  } catch (error: any) {
    console.error('Usage API error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
