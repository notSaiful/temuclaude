// Central pricing configuration — single source of truth
// All amounts in USD and INR paise for future checkout provider integration.
// Updated July 9, 2026 — Credit-based pricing for profitable frontier orchestration.

export type PlanId = 'free' | 'developer' | 'pro' | 'max' | 'enterprise';

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
  monthlyCredits: number;
  overagePerMillionCreditsUSD: number | null;
  queriesPerMonth: number;
  apiAccess: boolean;
  support: string;
  razorpayPlanId?: string; // optional: set when hosted checkout is enabled
}

export const PLANS: Record<PlanId, Plan> = {
  free: {
    id: 'free',
    name: 'Free',
    priceUSD: 0,
    priceINR: 0,
    priceLabel: '$0',
    period: 'forever',
    description: 'Sign in and try TemuClaude in the playground.',
    features: [
      'Standard usage limits apply',
      'Standard Mixture-of-Agents access',
      'Full 10-layer orchestration',
      'All 8 models',
      'Visible orchestration panel',
      'Community support',
    ],
    cta: 'Start Free',
    featured: false,
    monthlyCredits: 50000,
    overagePerMillionCreditsUSD: null,
    queriesPerMonth: 600, // 20/day * 30
    apiAccess: false,
    support: 'Community',
  },
  developer: {
    id: 'developer',
    name: 'Developer',
    priceUSD: 19,
    priceINR: 159900, // ~₹1,599
    priceLabel: '$19',
    period: '/month',
    description: 'For indie developers, researchers, and prototypes.',
    features: [
      '5x more usage than Free plan',
      'Full API Access enabled',
      'All 8 models, full orchestration',
      'Email support (48h)',
      'Usage dashboard + metrics',
      '60 requests/min rate limit',
      'Developer overage support',
    ],
    cta: 'Request Developer',
    featured: true,
    monthlyCredits: 5000000,
    overagePerMillionCreditsUSD: 4,
    queriesPerMonth: 50000, // compatibility only; credits are the billing source of truth
    apiAccess: true,
    support: 'Email (48h)',
    razorpayPlanId: undefined,
  },
  pro: {
    id: 'pro',
    name: 'Pro',
    priceUSD: 49,
    priceINR: 410000, // ₹4,100
    priceLabel: '$49',
    period: '/month',
    description: 'For power users and small teams who need more.',
    features: [
      '5x more usage than Developer plan',
      'Full API Access enabled',
      'Priority routing + faster latency',
      'Email support (24h)',
      'Usage dashboard + analytics',
      '300 requests/min rate limit',
      'Dedicated overage support',
    ],
    cta: 'Request Pro',
    featured: false,
    monthlyCredits: 25000000,
    overagePerMillionCreditsUSD: 3,
    queriesPerMonth: 500000, // compatibility only; credits are the billing source of truth
    apiAccess: true,
    support: 'Email (24h) + Dashboard',
    razorpayPlanId: undefined,
  },
  max: {
    id: 'max',
    name: 'Max',
    priceUSD: 149,
    priceINR: 1249900, // ~₹12,499
    priceLabel: '$149',
    period: '/month',
    description: 'For power users doing heavy coding, research, and agentic work.',
    features: [
      '10x more usage than Pro plan',
      'Full API Access enabled',
      'High-priority routing',
      'Priority support',
      'Advanced analytics',
      '1,000 requests/min rate limit',
      'Dedicated overage support',
    ],
    cta: 'Request Max',
    featured: false,
    monthlyCredits: 100000000,
    overagePerMillionCreditsUSD: 2,
    queriesPerMonth: 1000000, // compatibility only; credits are the billing source of truth
    apiAccess: true,
    support: 'Priority support + Dashboard',
    razorpayPlanId: undefined,
  },
  enterprise: {
    id: 'enterprise',
    name: 'Enterprise',
    priceUSD: 499,
    priceINR: 4150000, // ₹41,500
    priceLabel: '$499',
    period: '/month',
    description: 'For teams and organizations at scale.',
    features: [
      'Custom usage allocations',
      'SSO/SAML integration',
      'SLA 99.9% guarantee',
      'Dedicated support + Slack channel',
      '10 seats included',
      'Custom integrations + models',
      '10,000 requests/min rate limit',
    ],
    cta: 'Contact Sales',
    featured: false,
    monthlyCredits: 300000000,
    overagePerMillionCreditsUSD: 1.5,
    queriesPerMonth: -1, // compatibility only; credits are the billing source of truth
    apiAccess: true,
    support: 'Dedicated + Slack + SLA',
    razorpayPlanId: undefined,
  },
};

export const ROLLING_WINDOW_HOURS = 5;

// Query and credit limits for the 5-hour rolling window and weekly allocations
// Calibrated as ~monthly credit allocation divided by 4 to preserve margin calculations
export const PLAN_LIMITS = {
  free: {
    rollingQueries: 20,               // Max 20 queries per 5 hours
    weeklyCredits: 12500,             // Weekly allocation: 12.5K credits
  },
  developer: {
    rollingQueries: Infinity,
    weeklyCredits: 1250000,           // Weekly allocation: 1.25M credits
  },
  pro: {
    rollingQueries: Infinity,
    weeklyCredits: 6000000,           // Weekly allocation: 6M credits
  },
  max: {
    rollingQueries: Infinity,
    weeklyCredits: 25000000,          // Weekly allocation: 25M credits
  },
  enterprise: {
    rollingQueries: Infinity,
    weeklyCredits: 75000000,          // Weekly allocation: 75M credits
  },
};

export const CREDIT_MULTIPLIERS = {
  trivial: 1,
  standard: 1.5,
  hard: 4,
  frontier: 15,
  deepResearch: 20,
} as const;

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
