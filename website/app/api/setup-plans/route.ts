// Setup script: Create Razorpay plans for Developer, Pro, Max, and Enterprise
// GET /api/setup-plans — creates plans in Razorpay, returns plan IDs to add to .env

import { NextRequest, NextResponse } from 'next/server';
import { createPlan } from '@/lib/razorpay';
import { PLANS } from '@/lib/plans';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(req: NextRequest) {
  try {
    const masterKey = process.env.TEMUCLAUDE_MASTER_KEY;
    const token = req.headers.get('authorization')?.replace(/^Bearer\s+/i, '').trim();
    if (!masterKey || token !== masterKey) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    if (process.env.NEXT_PUBLIC_BILLING_CHECKOUT_ENABLED !== 'true') {
      return NextResponse.json({
        error: 'Hosted checkout is disabled. Razorpay plan setup is intentionally parked for this production launch.',
      }, { status: 503 });
    }

    const results: any = {};

    // Create Developer plan
    const devPlan = await createPlan({
      name: 'TemuClaude Developer',
      amountINR: PLANS.developer.priceINR,
      period: 'monthly',
      interval: 1,
      description: '5M monthly credits, API access, all models',
    });
    results.developer = { id: devPlan.id, amount: devPlan.item.amount };
    console.log('Developer plan created:', devPlan.id);

    // Create Pro plan
    const proPlan = await createPlan({
      name: 'TemuClaude Pro',
      amountINR: PLANS.pro.priceINR,
      period: 'monthly',
      interval: 1,
      description: '25M monthly credits, priority routing, API access',
    });
    results.pro = { id: proPlan.id, amount: proPlan.item.amount };
    console.log('Pro plan created:', proPlan.id);

    // Create Max plan
    const maxPlan = await createPlan({
      name: 'TemuClaude Max',
      amountINR: PLANS.max.priceINR,
      period: 'monthly',
      interval: 1,
      description: '100M monthly credits, heavy coding and research usage',
    });
    results.max = { id: maxPlan.id, amount: maxPlan.item.amount };
    console.log('Max plan created:', maxPlan.id);

    // Create Enterprise plan
    const entPlan = await createPlan({
      name: 'TemuClaude Enterprise',
      amountINR: PLANS.enterprise.priceINR,
      period: 'monthly',
      interval: 1,
      description: '300M monthly credits, SSO, SLA, dedicated support',
    });
    results.enterprise = { id: entPlan.id, amount: entPlan.item.amount };
    console.log('Enterprise plan created:', entPlan.id);

    return NextResponse.json({
      success: true,
      message: 'Add these plan IDs to your .env file',
      plans: results,
      envVars: {
        RAZORPAY_PLAN_DEV_ID: results.developer.id,
        RAZORPAY_PLAN_DEVELOPER_ID: results.developer.id,
        RAZORPAY_PLAN_PRO_ID: results.pro.id,
        RAZORPAY_PLAN_MAX_ID: results.max.id,
        RAZORPAY_PLAN_ENTERPRISE_ID: results.enterprise.id,
      },
    });
  } catch (error: any) {
    console.error('Setup error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
