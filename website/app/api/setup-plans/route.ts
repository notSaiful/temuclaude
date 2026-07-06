// Setup script: Create Razorpay plans for Developer, Pro, and Enterprise
// GET /api/setup-plans — creates plans in Razorpay, returns plan IDs to add to .env

import { NextResponse } from 'next/server';
import { createPlan } from '@/lib/razorpay';
import { PLANS } from '@/lib/plans';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const results: any = {};

    // Create Developer plan
    const devPlan = await createPlan({
      name: 'Temuclaude Developer',
      amountINR: PLANS.developer.priceINR,
      period: 'monthly',
      interval: 1,
      description: '50,000 queries/month, API access, all models',
    });
    results.developer = { id: devPlan.id, amount: devPlan.item.amount };
    console.log('Developer plan created:', devPlan.id);

    // Create Pro plan
    const proPlan = await createPlan({
      name: 'Temuclaude Pro',
      amountINR: PLANS.pro.priceINR,
      period: 'monthly',
      interval: 1,
      description: '500,000 queries/month, priority routing, API access',
    });
    results.pro = { id: proPlan.id, amount: proPlan.item.amount };
    console.log('Pro plan created:', proPlan.id);

    // Create Enterprise plan
    const entPlan = await createPlan({
      name: 'Temuclaude Enterprise',
      amountINR: PLANS.enterprise.priceINR,
      period: 'monthly',
      interval: 1,
      description: 'Unlimited queries, SSO, SLA, dedicated support',
    });
    results.enterprise = { id: entPlan.id, amount: entPlan.item.amount };
    console.log('Enterprise plan created:', entPlan.id);

    return NextResponse.json({
      success: true,
      message: 'Add these plan IDs to your .env file',
      plans: results,
      envVars: {
        RAZORPAY_PLAN_DEVELOPER_ID: results.developer.id,
        RAZORPAY_PLAN_PRO_ID: results.pro.id,
        RAZORPAY_PLAN_ENTERPRISE_ID: results.enterprise.id,
      },
    });
  } catch (error: any) {
    console.error('Setup error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}