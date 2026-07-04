// Check if user can send a query (free tier limit check)
// POST /api/usage/check
// Body: { identifier: string } — email or anonymous fingerprint
// Returns: { allowed: boolean, remaining: number, plan: string, message?: string }

import { NextRequest, NextResponse } from 'next/server';
import { getUserByEmail, getTodayUsage, incrementUsage, createUser } from '@/lib/db';
import { QUERY_LIMITS } from '@/lib/plans';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { identifier } = body;

    if (!identifier) {
      return NextResponse.json({ error: 'Identifier required' }, { status: 400 });
    }

    // Find or create user by email (for free tier, we use email as identifier)
    let user = getUserByEmail(identifier);
    if (!user) {
      user = createUser(identifier);
    }

    const todayUsage = getTodayUsage(user.id);
    const limits = QUERY_LIMITS[user.plan as keyof typeof QUERY_LIMITS] || QUERY_LIMITS.free;

    // Check daily limit for free tier
    if (user.plan === 'free' && limits.perDay !== Infinity) {
      if (todayUsage.query_count >= limits.perDay) {
        return NextResponse.json({
          allowed: false,
          remaining: 0,
          plan: user.plan,
          message: `You've reached your free tier limit of ${limits.perDay} queries/day. Upgrade to Pro for 5,000 queries/month.`,
          upgradeUrl: '/pricing',
        });
      }
    }

    // Check monthly limit for paid tiers
    if (limits.perMonth !== Infinity) {
      // For monthly check, we need to sum all days this month
      // This is a simplified check — full month usage is tracked separately
      // For now, just check daily limit (which is Infinity for paid)
    }

    return NextResponse.json({
      allowed: true,
      remaining: limits.perDay === Infinity ? null : limits.perDay - todayUsage.query_count,
      plan: user.plan,
      queriesToday: todayUsage.query_count,
      dailyLimit: limits.perDay === Infinity ? null : limits.perDay,
    });
  } catch (error: any) {
    console.error('Usage check error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

// Increment usage after a query is sent
// POST /api/usage/increment
export async function PUT(req: NextRequest) {
  try {
    const body = await req.json();
    const { identifier, inputTokens, outputTokens } = body;

    if (!identifier) {
      return NextResponse.json({ error: 'Identifier required' }, { status: 400 });
    }

    let user = getUserByEmail(identifier);
    if (!user) {
      user = createUser(identifier);
    }

    incrementUsage(user.id, inputTokens || 1000, outputTokens || 1000);

    const todayUsage = getTodayUsage(user.id);
    const limits = QUERY_LIMITS[user.plan as keyof typeof QUERY_LIMITS] || QUERY_LIMITS.free;

    return NextResponse.json({
      success: true,
      queriesToday: todayUsage.query_count,
      remaining: limits.perDay === Infinity ? null : Math.max(0, limits.perDay - todayUsage.query_count),
    });
  } catch (error: any) {
    console.error('Usage increment error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}