// Central pricing configuration — single source of truth
// All amounts in INR paise (Razorpay requirement) and USD
// Updated July 7, 2026 — based on verified competitor pricing research
// See PRICING-RESEARCH-REPORT.md for full analysis

export type PlanId = 'free' | 'developer' | 'pro' | 'enterprise';

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
    description: 'Try TemuClaude in the playground. No signup required.',
    features: [
      '20 queries/day',
      'Full 10-layer orchestration',
      'All 8 models',
      'Visible orchestration panel',
      'Community support',
    ],
    cta: 'Start Free',
    featured: false,
    queriesPerMonth: 600, // 20/day * 30
    apiAccess: false,
    support: 'Community',
  },
  developer: {
    id: 'developer',
    name: 'Developer',
    priceUSD: 15,
    priceINR: 1250, // ~₹1,040
    priceLabel: '$15',
    period: '/month',
    description: 'For indie developers, researchers, and startups.',
    features: [
      '50,000 queries/month',
      'API access',
      'All 8 models, full orchestration',
      'Email support (48h)',
      'Usage dashboard',
      '100 requests/min',
    ],
    cta: 'Get Developer',
    featured: true,
    queriesPerMonth: 50000,
    apiAccess: true,
    support: 'Email (48h)',
    razorpayPlanId: undefined,
  },
  pro: {
    id: 'pro',
    name: 'Pro',
    priceUSD: 49,
    priceINR: 4100, // ~₹3,410
    priceLabel: '$49',
    period: '/month',
    description: 'For power users and small teams who need more.',
    features: [
      '500,000 queries/month',
      'API access',
      'Priority routing + faster latency',
      'Email support (24h)',
      'Usage dashboard + analytics',
      '1,000 requests/min',
    ],
    cta: 'Get Pro',
    featured: false,
    queriesPerMonth: 500000,
    apiAccess: true,
    support: 'Email (24h) + Dashboard',
    razorpayPlanId: undefined,
  },
  enterprise: {
    id: 'enterprise',
    name: 'Enterprise',
    priceUSD: 499,
    priceINR: 41500, // ~₹34,500
    priceLabel: '$499',
    period: '/month',
    description: 'For teams and organizations at scale.',
    features: [
      'Unlimited queries',
      'SSO/SAML',
      'SLA 99.9% guarantee',
      'Dedicated support + Slack',
      '10 seats included',
      'Custom integrations + models',
      '10,000 requests/min',
    ],
    cta: 'Contact Sales',
    featured: false,
    queriesPerMonth: -1, // unlimited
    apiAccess: true,
    support: 'Dedicated + Slack + SLA',
    razorpayPlanId: undefined,
  },
};

// Pay-as-you-go token pricing (per 1M tokens)
// Blended average based on routing: 60% trivial (cheapest), 30% medium, 10% hard (full MoA)
// Positioned at ~4x cheaper than Claude Sonnet 5, ~12x cheaper than GPT-5.5
export const PAYG_PRICING = {
  inputPerMillion: 0.50,   // $0.50 per 1M input tokens (average)
  outputPerMillion: 2.00,  // $2.00 per 1M output tokens (average)
  blendedPerMillion: 1.44, // ~$1.44 per 1M blended (actual cost varies by difficulty)
  cachedInputPerMillion: 0.05, // $0.05 per 1M cached input tokens (90% discount)
  currency: 'USD',
};

// Query limits per plan (per day for free, per month for paid)
export const QUERY_LIMITS = {
  free: { perDay: 20, perMonth: 600 },
  developer: { perDay: Infinity, perMonth: 50000 },
  pro: { perDay: Infinity, perMonth: 500000 },
  enterprise: { perDay: Infinity, perMonth: -1 }, // unlimited
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