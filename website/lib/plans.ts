// Central pricing configuration — single source of truth
// All amounts in INR paise (Razorpay requirement) and USD cents

export type PlanId = 'free' | 'pro' | 'enterprise';

export interface Plan {
  id: PlanId;
  name: string;
  priceUSD: number;
  priceINR: number; // in paise (1 INR = 100 paise)
  priceLabel: string;
  period: string;
  description: string;
  features: string[];
  cta: string;
  featured: boolean;
  queriesPerMonth: number;
  apiAccess: boolean;
  support: string;
  razorpayPlanId?: string; // set after creating plans in Razorpay dashboard
}

export const PLANS: Record<PlanId, Plan> = {
  free: {
    id: 'free',
    name: 'Free',
    priceUSD: 0,
    priceINR: 0,
    priceLabel: '$0',
    period: 'forever',
    description: 'Try Temuclaude in the playground. No signup required.',
    features: [
      '50 queries/day',
      'Full 10-layer orchestration',
      'All 5 models',
      'Visible orchestration panel',
      'Community support',
    ],
    cta: 'Start Free',
    featured: false,
    queriesPerMonth: 1500, // 50/day * 30
    apiAccess: false,
    support: 'Community',
  },
  pro: {
    id: 'pro',
    name: 'Pro',
    priceUSD: 29,
    priceINR: 2900, // ~₹2,400 (approx, will adjust based on exchange rate)
    priceLabel: '$29',
    period: '/month',
    description: 'For developers, researchers, and startups.',
    features: [
      '5,000 queries/month',
      'API access',
      'All 5 models, full orchestration',
      'Priority routing',
      'Email support (48h)',
      'Usage dashboard',
    ],
    cta: 'Get Pro',
    featured: true,
    queriesPerMonth: 5000,
    apiAccess: true,
    support: 'Email (48h)',
    razorpayPlanId: undefined, // set server-side, not needed on client
  },
  enterprise: {
    id: 'enterprise',
    name: 'Enterprise',
    priceUSD: 499,
    priceINR: 49900, // ~₹41,500
    priceLabel: '$499',
    period: '/month',
    description: 'For teams and organizations.',
    features: [
      '200,000 queries/month',
      'SSO/SAML',
      'SLA 99.9% guarantee',
      'Dedicated support + Slack',
      '10 seats included',
      'Custom integrations',
    ],
    cta: 'Contact Sales',
    featured: false,
    queriesPerMonth: 200000,
    apiAccess: true,
    support: 'Dedicated + Slack',
    razorpayPlanId: undefined, // set server-side, not needed on client
  },
};

// Pay-as-you-go token pricing (per 1M tokens)
export const PAYG_PRICING = {
  inputPerMillion: 2.00,  // $2 per 1M input tokens
  outputPerMillion: 10.00, // $10 per 1M output tokens
  cachedInputPerMillion: 0.20, // $0.20 per 1M cached input tokens
  currency: 'USD',
};

// Query limits per plan (per day for free, per month for paid)
export const QUERY_LIMITS = {
  free: { perDay: 50, perMonth: 1500 },
  pro: { perDay: Infinity, perMonth: 5000 },
  enterprise: { perDay: Infinity, perMonth: 200000 },
};

// Get plan by ID
export function getPlan(id: string): Plan | null {
  return PLANS[id as PlanId] || null;
}

// Get plan from Razorpay subscription ID (stored in DB)
export function getPlanByRazorpayPlanId(razorpayPlanId: string): Plan | null {
  for (const plan of Object.values(PLANS)) {
    if (plan.razorpayPlanId === razorpayPlanId) return plan;
  }
  return null;
}