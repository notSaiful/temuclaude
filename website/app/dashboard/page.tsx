'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Navbar } from '@/components/Navbar';
import { getAccessToken, getStoredSession, signOut, syncAuthenticatedUser, type LocalSession } from '@/lib/auth';

type ApiKeyRecord = {
  id: string;
  key_prefix: string;
  name: string;
  last_used: number | null;
  created_at: number;
};

type DashboardData = {
  user: {
    id: string;
    email: string;
    name: string | null;
    plan: string;
    created_at: number;
    credit_balance?: number;
    credits_reset_at?: number;
    weekly_credit_allocation?: number;
  };
  plan: {
    id: string;
    name: string;
    priceUSD: number;
    priceLabel: string;
    period: string;
    apiAccess: boolean;
    support: string;
    monthlyCredits: number;
    overagePerMillionCreditsUSD: number | null;
  };
  limits: {
    rollingQueries: number | null;
    weeklyCredits: number;
  };
  usage: {
    today: {
      queries: number;
      inputTokens: number;
      outputTokens: number;
    };
    month: {
      queries: number;
      inputTokens: number;
      outputTokens: number;
    };
    rolling?: {
      queries: number;
      creditsSpent: number;
    };
  };
  apiKeys: ApiKeyRecord[];
  savings: number;
  modelMix: Record<string, number>;
  billing: {
    creditsBalanceUSD: number | null;
    projectedSpendUSD: number | null;
    nextInvoiceAt: number | null;
  };
};

function formatNumber(value: number) {
  return new Intl.NumberFormat('en-US').format(value);
}

function formatTokens(value: number) {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(2)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return formatNumber(value);
}

function formatDate(timestamp: number | null) {
  if (!timestamp) return 'Not scheduled';
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(
    new Date(timestamp * 1000)
  );
}

function formatLastUsed(timestamp: number | null) {
  return timestamp ? formatDate(timestamp) : 'Never';
}

function moneyOrUnavailable(value: number | null) {
  return value === null ? 'Not tracked' : `$${value.toFixed(2)}`;
}

function authProviderLabel(session: LocalSession) {
  const labels: Record<string, string> = {
    email: 'Email',
    google: 'Google',
    github: 'GitHub',
  };
  const providers = session.providers?.length ? session.providers : [session.provider];
  return Array.from(new Set(providers)).map((provider) => labels[provider] || provider).join(' + ');
}

export default function DashboardPage() {
  const router = useRouter();
  const [session, setSession] = useState<LocalSession | null>(null);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [newApiKey, setNewApiKey] = useState<string | null>(null);
  const [newApiKeyId, setNewApiKeyId] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [showManageModal, setShowManageModal] = useState(false);
  const [isLoadingDashboard, setIsLoadingDashboard] = useState(true);
  const [isProcessingUpdate, setIsProcessingUpdate] = useState(false);
  const [keyStatus, setKeyStatus] = useState<string | null>(null);
  const [dataError, setDataError] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    const token = await getAccessToken();
    if (!token) throw new Error('Please sign in again to view dashboard data.');

    const res = await fetch('/api/dashboard', {
      headers: { Authorization: `Bearer ${token}` },
      cache: 'no-store',
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Dashboard data unavailable.');
    setDashboardData(data);
    setDataError(null);
  }, []);

  useEffect(() => {
    let mounted = true;

    getStoredSession()
      .then(async (stored) => {
        if (!mounted) return;
        if (!stored) {
          router.replace('/login?returnTo=/dashboard');
          return;
        }

        setSession(stored);
        try {
          await syncAuthenticatedUser();
          await loadDashboard();
        } catch (error) {
          if (mounted) {
            setDataError(error instanceof Error ? error.message : 'Dashboard data unavailable.');
          }
        }
      })
      .catch(() => {
        if (!mounted) return;
        router.replace('/login?returnTo=/dashboard');
      })
      .finally(() => {
        if (mounted) setIsLoadingDashboard(false);
      });

    return () => {
      mounted = false;
    };
  }, [loadDashboard, router]);

  const handleGenerateKey = async () => {
    setKeyStatus('Creating API key...');
    setIsProcessingUpdate(true);

    try {
      const token = await getAccessToken();
      if (!token) {
        setKeyStatus('Please sign in again before creating an API key.');
        return;
      }

      const res = await fetch('/api/keys', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: 'default' }),
      });
      const data = await res.json();
      if (!res.ok || !data.key) {
        setKeyStatus(data.error || 'API key creation failed.');
        return;
      }

      setNewApiKey(data.key);
      setNewApiKeyId(data.id);
      setKeyStatus('Live API key created. It is shown once, so copy it now.');
      await loadDashboard();
    } catch (error) {
      setKeyStatus(error instanceof Error ? error.message : 'API key service is unavailable.');
    } finally {
      setIsProcessingUpdate(false);
    }
  };

  const handleCopyKey = () => {
    if (newApiKey) {
      navigator.clipboard.writeText(newApiKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    if (!confirm('Are you sure you want to revoke this API key? Any applications currently using it will be blocked.')) {
      return;
    }

    setIsProcessingUpdate(true);
    setKeyStatus('Revoking API key...');

    try {
      const token = await getAccessToken();
      if (!token) {
        setKeyStatus('Please sign in again before revoking an API key.');
        return;
      }

      const res = await fetch('/api/keys', {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ keyId }),
      });
      const data = await res.json();
      if (!res.ok) {
        setKeyStatus(data.error || 'API key revoke failed.');
        return;
      }

      if (keyId === newApiKeyId) {
        setNewApiKey(null);
        setNewApiKeyId(null);
      }
      setKeyStatus('API key revoked.');
      await loadDashboard();
    } catch (error) {
      setKeyStatus(error instanceof Error ? error.message : 'API key service is unavailable.');
    } finally {
      setIsProcessingUpdate(false);
    }
  };

  const handleDashboardSignOut = () => {
    signOut().finally(() => router.push('/login'));
  };

  const activePlan = dashboardData?.plan;
  const creditBalance = dashboardData?.user.credit_balance ?? 12500;
  const weeklyAllocation = dashboardData?.user.weekly_credit_allocation ?? 12500;
  const weeklyPercent = weeklyAllocation === 0 ? 0 : Math.max(0, Math.min(100, Math.round((creditBalance / weeklyAllocation) * 100)));

  const rollingQueries = dashboardData?.usage.rolling?.queries ?? 0;
  const rollingLimit = dashboardData?.limits.rollingQueries === null
    ? Infinity
    : (dashboardData?.limits.rollingQueries ?? 20);
  const rollingPercent = rollingLimit === Infinity
    ? 100
    : (rollingLimit === 0 ? 0 : Math.max(0, Math.min(100, Math.round(((rollingLimit - rollingQueries) / rollingLimit) * 100))));

  const displayName = dashboardData?.user.name || session?.name || 'TemuClaude User';
  const displayEmail = dashboardData?.user.email || session?.email || '';

  if (!session) {
    return (
      <>
        <Navbar />
        <main className="min-h-screen pt-28 px-6 bg-bg-primary">
          <div className="container-max">
            <div className="card max-w-md mx-auto text-center">Checking your session...</div>
          </div>
        </main>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <main className="min-h-screen pt-28 pb-24 px-6 bg-bg-primary">
        <div className="container-max">
          <div className="mb-10">
            <h1 className="text-4xl font-serif text-text-primary mb-1.5" style={{ fontWeight: 300 }}>
              Developer Dashboard
            </h1>
            <p className="text-sm text-text-secondary">
              Live account data from your authenticated TemuClaude profile, API credentials, and usage records.
            </p>
          </div>

          {dataError && (
            <div className="card mb-8 border-red-200 bg-red-50 text-red-700">
              {dataError}
            </div>
          )}

          <div className="grid lg:grid-cols-12 gap-8 items-start">
            <div className="lg:col-span-8 space-y-8">
              <div className="card">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-5">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 rounded-full bg-accent-primary text-white flex items-center justify-center text-lg font-semibold">
                      {session.avatarInitials}
                    </div>
                    <div>
                      <h2 className="text-xl font-serif text-text-primary">{displayName}</h2>
                      <p className="text-sm text-text-secondary">{displayEmail}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-right">
                    <div>
                      <div className="text-xs text-text-muted">Available Usage</div>
                      <div className="text-2xl font-mono text-accent-olive">
                        {isLoadingDashboard ? '...' : `${weeklyPercent}%`}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-text-muted">Plan</div>
                      <div className="text-2xl font-mono capitalize text-text-primary">
                        {activePlan?.name || (isLoadingDashboard ? 'Loading' : 'Free')}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-8 h-8 rounded-lg bg-accent-olive/10 flex items-center justify-center">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#738E54" strokeWidth="2">
                      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                    </svg>
                  </div>
                  <span className="text-xs font-mono text-text-muted uppercase tracking-wider">Authentication Credentials</span>
                </div>

                <h2 className="text-xl font-serif text-text-primary mb-2">Developer API Keys</h2>
                <p className="text-sm text-text-secondary mb-6 leading-relaxed">
                  Server-side API keys are stored hashed. Existing keys can only be shown by prefix; newly generated keys are shown once.
                </p>

                {newApiKey && (
                  <div className="space-y-4 mb-6">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-bg-secondary p-3 rounded-sm font-mono text-sm border border-border-subtle overflow-x-auto text-text-primary">
                        {newApiKey}
                      </div>
                      <button onClick={handleCopyKey} className="btn-secondary py-3 px-5 text-sm">
                        {copied ? 'Copied' : 'Copy'}
                      </button>
                    </div>
                    <div className="flex items-center justify-between text-xs text-text-muted">
                      <span>Generated just now · Active</span>
                      {newApiKeyId && (
                        <button
                          onClick={() => handleRevokeKey(newApiKeyId)}
                          className="text-red-600 hover:text-red-700 font-medium hover:underline"
                        >
                          Revoke Key
                        </button>
                      )}
                    </div>
                  </div>
                )}

                <div className="space-y-3 mb-5">
                  {(dashboardData?.apiKeys.length || 0) > 0 ? (
                    dashboardData?.apiKeys.map((key) => (
                      <div key={key.id} className="grid md:grid-cols-[1fr_140px_100px] gap-3 p-3 bg-bg-secondary border border-border-subtle rounded-sm text-xs">
                        <div>
                          <div className="font-mono text-text-primary">{key.key_prefix}...</div>
                        <div className="text-text-muted">{key.name || 'default'} · Created {formatDate(key.created_at)}</div>
                      </div>
                        <div className="text-text-secondary md:text-right">Last used {formatLastUsed(key.last_used)}</div>
                        <button
                          onClick={() => handleRevokeKey(key.id)}
                          disabled={isProcessingUpdate}
                          className="text-red-600 hover:text-red-700 font-medium md:text-right disabled:opacity-50"
                        >
                          Revoke
                        </button>
                      </div>
                    ))
                  ) : (
                    <div className="p-4 bg-bg-secondary border border-border-subtle rounded-sm text-sm text-text-secondary">
                      No API keys are stored for this account yet.
                    </div>
                  )}
                </div>

                <button onClick={handleGenerateKey} disabled={isProcessingUpdate} className="btn-accent disabled:opacity-60">
                  {isProcessingUpdate ? 'Working...' : 'Generate API Key'}
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                </button>
                {keyStatus && <p className="text-xs text-accent-primary mt-3">{keyStatus}</p>}
              </div>

              <div className="card">
                <h2 className="text-lg font-serif text-text-primary mb-4">Usage Analytics</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div className="p-4 bg-bg-secondary border border-border-subtle rounded-sm">
                    <span className="text-[10px] uppercase tracking-wider text-text-muted block mb-1">Weekly Usage Remaining</span>
                    <strong className="text-2xl text-text-primary">{weeklyPercent}%</strong>
                  </div>
                  <div className="p-4 bg-bg-secondary border border-border-subtle rounded-sm">
                    <span className="text-[10px] uppercase tracking-wider text-text-muted block mb-1">5h Capacity Remaining</span>
                    <strong className="text-2xl text-text-primary">{rollingPercent}%</strong>
                  </div>
                  <div className="p-4 bg-bg-secondary border border-border-subtle rounded-sm">
                    <span className="text-[10px] uppercase tracking-wider text-text-muted block mb-1">5h Queries Sent</span>
                    <strong className="text-2xl text-text-primary">
                      {rollingQueries}
                    </strong>
                  </div>
                  <div className="p-4 bg-bg-secondary border border-border-subtle rounded-sm">
                    <span className="text-[10px] uppercase tracking-wider text-text-muted block mb-1">Rate Status</span>
                    <strong className="text-2xl text-accent-olive">Active</strong>
                  </div>
                </div>

                <div className="border border-border-default rounded-md p-4 bg-green-50/30 border-green-200/50">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-text-secondary mb-3 flex items-center gap-1.5 text-accent-olive">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <line x1="12" y1="1" x2="12" y2="23"></line>
                      <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                    </svg>
                    Estimated Cumulative Savings
                  </h3>
                  <div className="flex items-baseline gap-2 mb-1">
                    <span className="text-3xl font-mono font-bold text-accent-olive">
                      ${(dashboardData?.savings ?? 0).toFixed(2)}
                    </span>
                    <span className="text-xs text-text-secondary">saved vs. configured frontier-direct baseline pricing</span>
                  </div>
                  <p className="text-xs text-text-muted leading-relaxed">
                    Calculated in real-time by analyzing actual input/output token volume against comparable baseline vendor costs.
                  </p>
                </div>
              </div>

              <div className="card">
                <h2 className="text-lg font-serif text-text-primary mb-2">Activity By Model</h2>
                <p className="text-xs text-text-secondary mb-5 leading-relaxed">
                  Distribution of queries routed across the hybrid model pool.
                </p>

                {dashboardData?.modelMix && Object.keys(dashboardData.modelMix).length > 0 ? (
                  <div className="space-y-4">
                    {(() => {
                      const totalQueries = Object.values(dashboardData.modelMix).reduce((sum, val) => sum + val, 0);

                      const modelMeta: Record<string, { label: string; colorClass: string }> = {
                        'glm-5.2': { label: 'GLM-5.2 (Orchestrator)', colorClass: 'bg-accent-olive' },
                        'deepseek-pro': { label: 'DeepSeek Pro (Reasoning)', colorClass: 'bg-accent-primary' },
                        'llama-3.3': { label: 'Llama 3.3 (Specialist)', colorClass: 'bg-blue-600' },
                        'gemini-2.5': { label: 'Gemini 2.5 Flash (Worker)', colorClass: 'bg-sky-500' },
                        'mistral-large': { label: 'Mistral Large 3 (Logic)', colorClass: 'bg-amber-600' },
                        'temuclaude-standard': { label: 'TemuClaude Standard', colorClass: 'bg-emerald-600' },
                      };

                      return Object.entries(dashboardData.modelMix).map(([modelId, count]) => {
                        const meta = modelMeta[modelId] || { label: modelId, colorClass: 'bg-text-secondary' };
                        const percent = Math.round((count / totalQueries) * 100);
                        return (
                          <div key={modelId} className="space-y-1.5">
                            <div className="flex justify-between text-xs font-mono">
                              <span className="text-text-primary font-medium">{meta.label}</span>
                              <span className="text-text-secondary">{count} queries ({percent}%)</span>
                            </div>
                            <div className="w-full bg-border-default h-2 rounded-full overflow-hidden">
                              <div
                                className={`${meta.colorClass} h-full transition-all duration-500`}
                                style={{ width: `${percent}%` }}
                              />
                            </div>
                          </div>
                        );
                      });
                    })()}
                  </div>
                ) : (
                  <div className="p-4 bg-bg-secondary border border-border-subtle rounded-sm text-sm text-text-secondary text-center">
                    No active model queries recorded yet.
                  </div>
                )}
              </div>

              <div className="card">
                <h2 className="text-lg font-serif text-text-primary mb-4">Recent Logs</h2>
                <div className="divide-y divide-border-subtle border border-border-subtle rounded-sm overflow-hidden">
                  <div className="grid md:grid-cols-[140px_100px_1fr] gap-2 p-3 text-xs bg-white/50">
                    <span className="font-mono text-text-primary">account.plan</span>
                    <span className="text-accent-olive font-semibold">Current</span>
                    <span className="text-text-secondary">{activePlan?.name || 'Free'} plan from authenticated user record</span>
                  </div>
                  <div className="grid md:grid-cols-[140px_100px_1fr] gap-2 p-3 text-xs bg-white/50">
                    <span className="font-mono text-text-primary">usage.month</span>
                    <span className="text-accent-olive font-semibold">Current</span>
                    <span className="text-text-secondary">{formatNumber(dashboardData?.usage.month.queries ?? 0)} tracked API requests this month</span>
                  </div>
                  <div className="grid md:grid-cols-[140px_100px_1fr] gap-2 p-3 text-xs bg-white/50">
                    <span className="font-mono text-text-primary">api.keys</span>
                    <span className="text-accent-olive font-semibold">Current</span>
                    <span className="text-text-secondary">{formatNumber(dashboardData?.apiKeys.length ?? 0)} active stored keys</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="lg:col-span-4 space-y-8">
              <div className="card h-full flex flex-col justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-8 h-8 rounded-lg bg-accent-primary/10 flex items-center justify-center">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#E25822" strokeWidth="2">
                        <rect x="2" y="4" width="20" height="16" rx="2" />
                        <line x1="2" y1="10" x2="22" y2="10" />
                      </svg>
                    </div>
                    <span className="text-xs font-mono text-text-muted uppercase tracking-wider">Subscription</span>
                  </div>

                  <h2 className="text-xl font-serif text-text-primary mb-1">Active Plan</h2>
                  <p className="text-xs text-text-secondary mb-6 leading-relaxed">
                    Plan and limits are loaded from the authenticated account record.
                  </p>

                  <div className="p-6 bg-bg-secondary rounded-sm text-center mb-6 border border-border-subtle">
                    <span className="text-xs text-text-muted uppercase block mb-1">Active Tier</span>
                    <strong className="text-3xl text-text-primary font-serif font-semibold capitalize">
                      {activePlan?.name || 'Free'} Plan
                    </strong>
                    <span className="text-xs text-text-muted block mt-1">
                      {activePlan ? `${activePlan.priceLabel}${activePlan.period === 'forever' ? '' : activePlan.period}` : '$0'}
                    </span>
                  </div>

                  <div className="space-y-2 mb-6">
                    <div className="flex justify-between text-xs text-text-secondary font-medium">
                      <span>5h Request Capacity</span>
                      <span>
                        {rollingPercent}% remaining
                      </span>
                    </div>
                    <div className="w-full bg-border-default h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-accent-primary h-full transition-all duration-500"
                        style={{
                          width: `${rollingPercent}%`
                        }}
                      />
                    </div>
                    <div className="text-[10px] text-text-muted flex justify-between">
                      <span>Capacity recovers over time</span>
                      <span>Next reset: {formatDate(dashboardData?.user.credits_reset_at ?? null)}</span>
                    </div>
                  </div>
                </div>

                <button onClick={() => setShowManageModal(true)} className="btn-accent w-full py-3">
                  Manage Subscription
                </button>
              </div>

              <div className="card">
                <h2 className="text-lg font-serif text-text-primary mb-4">Billing & Usage</h2>
                <div className="space-y-3 text-sm mb-5">
                  <div className="flex justify-between">
                    <span className="text-text-secondary">Weekly Usage Capacity</span>
                    <strong className="text-text-primary font-mono">{weeklyPercent}%</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-secondary">5h Request Capacity</span>
                    <strong className="text-text-primary font-mono">{rollingPercent}%</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-secondary">Next Renewal Reset</span>
                    <strong className="text-text-primary">
                      {formatDate(dashboardData?.user.credits_reset_at ?? null)}
                    </strong>
                  </div>
                </div>
                <a href="/pricing" className="btn-accent w-full text-center block py-2.5 text-xs">
                  Purchase Usage Top-Up
                </a>
              </div>

              <div className="card">
                <h2 className="text-lg font-serif text-text-primary mb-4">Docs & Help Center</h2>
                <div className="grid gap-2">
                  <a href="/docs" className="btn-secondary justify-start">API Docs</a>
                  <a href="/playground" className="btn-secondary justify-start">Playground</a>
                  <a href="mailto:hello@temuclaude.com" className="btn-secondary justify-start">Help Center</a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {showManageModal && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="bg-white rounded-xl border border-border-subtle shadow-lg p-6 max-w-sm w-full animate-scale-up">
            <h3 className="text-lg font-serif text-text-primary mb-2">Manage Subscription</h3>
            <p className="text-xs text-text-secondary mb-6">
              Your current dashboard plan is <strong className="capitalize">{activePlan?.name || 'Free'}</strong>.
              Subscription changes are handled through the pricing and payment flow.
            </p>

            <div className="space-y-3 mb-6">
              <a href="/pricing" className="btn-accent w-full py-2.5 text-sm">
                View Plans
              </a>
              <a href="mailto:hello@temuclaude.com" className="btn-secondary w-full py-2.5 text-sm">
                Contact Support
              </a>
            </div>

            <button
              onClick={() => setShowManageModal(false)}
              className="text-xs text-text-muted hover:text-text-primary w-full text-center block mt-2 font-medium"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </>
  );
}
