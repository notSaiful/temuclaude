import { NextRequest, NextResponse } from 'next/server';
import {
  getActiveSubscriptionAsync,
  getMonthUsageAsync,
  getOrCreateUserByEmailAsync,
  getTodayUsageAsync,
  listApiKeysAsync,
  getRollingWindowUsageAsync,
  verifyAndRenewWeeklyCreditsAsync,
  getSavingsAndModelMixAsync,
} from '@/lib/db';
import { PLANS, PLAN_LIMITS, type PlanId } from '@/lib/plans';
import { nextRollingRecoveryAt } from '@/lib/usage-windows';
import { getAuthenticatedSupabaseUser } from '@/lib/supabase-server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

function getDisplayName(user: { email?: string; user_metadata?: Record<string, any> }) {
  const metadata = user.user_metadata || {};
  return (
    metadata.full_name ||
    metadata.name ||
    metadata.user_name ||
    metadata.preferred_username ||
    user.email?.split('@')[0]?.replace(/[._-]+/g, ' ')
  );
}

function isPlanId(plan: string): plan is PlanId {
  return plan in PLANS;
}

export async function GET(req: NextRequest) {
  try {
    const auth = await getAuthenticatedSupabaseUser(req);
    if ('error' in auth) {
      return NextResponse.json({ error: auth.error }, { status: auth.status });
    }

    const email = auth.user.email?.trim().toLowerCase();
    if (!email) {
      return NextResponse.json({ error: 'Authenticated user has no email address' }, { status: 400 });
    }

    const initialUser = await getOrCreateUserByEmailAsync(email, getDisplayName(auth.user));
    const user = (await verifyAndRenewWeeklyCreditsAsync(initialUser.id)) || initialUser;

    const planId = isPlanId(user.plan) ? user.plan : 'free';
    const plan = PLANS[planId];
    const limits = PLAN_LIMITS[planId];
    const todayUsage = await getTodayUsageAsync(user.id);
    const monthUsage = await getMonthUsageAsync(user.id);
    const rollingUsage = await getRollingWindowUsageAsync(user.id, 5);
    const apiKeys = await listApiKeysAsync(user.id);
    const subscription = await getActiveSubscriptionAsync(user.id);
    const { totalSavedUSD, modelMix } = await getSavingsAndModelMixAsync(user.id);

    return NextResponse.json({
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        plan: user.plan,
        created_at: user.created_at,
        credit_balance: user.credit_balance,
        credits_reset_at: user.credits_reset_at,
        weekly_credit_allocation: user.weekly_credit_allocation,
      },
      plan: {
        id: plan.id,
        name: plan.name,
        priceUSD: plan.priceUSD,
        priceLabel: plan.priceLabel,
        period: plan.period,
        apiAccess: plan.apiAccess,
        support: plan.support,
        queriesPerMonth: plan.queriesPerMonth,
        monthlyCredits: plan.monthlyCredits,
        overagePerMillionCreditsUSD: plan.overagePerMillionCreditsUSD,
      },
      limits: {
        rollingQueries: limits.rollingQueries === Infinity ? null : limits.rollingQueries,
        weeklyCredits: limits.weeklyCredits,
      },
      usage: {
        today: {
          queries: todayUsage.query_count,
          inputTokens: todayUsage.input_tokens,
          outputTokens: todayUsage.output_tokens,
        },
        month: {
          queries: monthUsage.totalQueries,
          inputTokens: monthUsage.totalInputTokens,
          outputTokens: monthUsage.totalOutputTokens,
        },
        rolling: {
          queries: rollingUsage.query_count,
          creditsSpent: rollingUsage.credits_spent,
        },
      },
      capacity: {
        windowHours: 5,
        isUnlimited: limits.rollingQueries === Infinity,
        limit: limits.rollingQueries === Infinity ? null : limits.rollingQueries,
        remaining: limits.rollingQueries === Infinity ? null : Math.max(0, limits.rollingQueries - rollingUsage.query_count),
        nextRecoveryAt: limits.rollingQueries === Infinity
          ? null
          : nextRollingRecoveryAt(rollingUsage.oldest_event_at, 5),
      },
      apiKeys,
      savings: totalSavedUSD,
      modelMix,
      billing: {
        creditsBalanceUSD: null,
        projectedSpendUSD: null,
        nextInvoiceAt: subscription?.current_period_end || user.credits_reset_at || null,
      },
    });
  } catch (error: any) {
    console.error('Dashboard API error:', error);
    return NextResponse.json({ error: error.message || 'Dashboard data unavailable' }, { status: 500 });
  }
}
