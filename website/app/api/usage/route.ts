// Get current user's usage and plan limits
// GET /api/usage
// Headers: Authorization: Bearer <api_key> OR x-api-key: <api_key>

import { NextRequest, NextResponse } from 'next/server';
import { validateApiKey, getTodayUsage, getMonthUsage, getUser } from '@/lib/db';
import { QUERY_LIMITS, PLANS } from '@/lib/plans';

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

    const valid = validateApiKey(apiKey);
    if (!valid) {
      return NextResponse.json({ error: 'Invalid API key' }, { status: 401 });
    }

    const { userId, user } = valid;
    const plan = PLANS[user.plan as keyof typeof PLANS] || PLANS.free;
    const todayUsage = getTodayUsage(userId);
    const monthUsage = getMonthUsage(userId);
    const limits = QUERY_LIMITS[user.plan as keyof typeof QUERY_LIMITS] || QUERY_LIMITS.free;

    return NextResponse.json({
      plan: plan.id,
      planName: plan.name,
      queriesToday: todayUsage.query_count,
      queriesThisMonth: monthUsage.totalQueries,
      dailyLimit: limits.perDay === Infinity ? null : limits.perDay,
      monthlyLimit: limits.perMonth,
      remainingQueries: limits.perMonth === Infinity ? null : Math.max(0, limits.perMonth - monthUsage.totalQueries),
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