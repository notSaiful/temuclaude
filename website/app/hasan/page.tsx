'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// ============================================================
// HASAN — Autonomous System Interface
// Named after Hasan ibn Ali (RA)
// ============================================================

interface DaemonStatus {
  name: string;
  pid: number | null;
  alive: boolean;
  status: string;
  heartbeatAge: number | null;
  extra: any;
}

interface ActivityItem {
  time: string;
  daemon: string;
  level: string;
  message: string;
}

interface ChatMessage {
  role: 'user' | 'hasan';
  content: string;
  timestamp: string;
}

interface HasanData {
  timestamp: string;
  system: string;
  status: string;
  daemons: { total: number; alive: number; list: DaemonStatus[] };
  queue: { newRaw: number; newFindings: number; implementationQueue: number; implementationFailed: number };
  sharedMemory: { daemons: number; recentEvents: any[]; knowledgeFacts: number };
  unlimitedMemory: { exists: boolean; sizeMB: string };
  swot: { strengths: number; weaknesses: number; opportunities: number; threats: number } | null;
  radar: { totalSignals: number } | null;
  cost: { remainingCredits: number; burnRatePerDay: number; throttleLevel: string; totalSpent24h: number; totalTokens24h: number };
  ummah: { totalDistributed: number; entries: number };
  activity: ActivityItem[];
  identity: { verified: boolean; purpose: string; goal: string };
  stats: { sourceModules: number };
}

const DAEMON_META: Record<string, { label: string; group: string; icon: string }> = {
  scout_daemon: { label: 'ArXiv Scout', group: 'Research Pipeline', icon: 'search' },
  distiller_daemon: { label: 'Finding Distiller', group: 'Research Pipeline', icon: 'filter' },
  research_daemon_1: { label: 'Deep Researcher I', group: 'Research Pipeline', icon: 'microscope' },
  research_daemon_2: { label: 'Deep Researcher II', group: 'Research Pipeline', icon: 'microscope' },
  research_daemon_3: { label: 'Deep Researcher III', group: 'Research Pipeline', icon: 'microscope' },
  integrator_daemon: { label: 'Code Integrator (Staging)', group: 'Research Pipeline', icon: 'code' },
  coordinator_daemon: { label: 'Swarm Coordinator', group: 'Core', icon: 'cpu' },
  cyber_daemon: { label: 'Cybersecurity Shield', group: 'Security', icon: 'shield' },
  efficiency_daemon: { label: 'Cost Efficiency Optimizer', group: 'Optimization', icon: 'zap' },
  media_daemon: { label: 'Media Generation Lab', group: 'Research Pipeline', icon: 'film' },
  marketing_daemon: { label: 'X/Twitter Auto-Poster', group: 'Growth', icon: 'megaphone' },
  feedback_daemon: { label: 'Performance Evaluator', group: 'Self-Improvement', icon: 'refresh' },
  meta_auditor_daemon: { label: '7-Layer Code Auditor', group: 'Self-Healing', icon: 'stethoscope' },
  swot_daemon: { label: 'SWOT Strategy Analyst', group: 'Strategy', icon: 'bar-chart' },
  website_daemon: { label: 'Website & Vercel Updater', group: 'Growth', icon: 'globe' },
  industry_radar_daemon: { label: 'Industry News Radar', group: 'Awareness', icon: 'radar' },
  model_optimizer_daemon: { label: 'Model Benchmark & Swap', group: 'Optimization', icon: 'robot' },
  cost_efficiency_daemon: { label: 'Credit & Throttle Guard', group: 'Finance', icon: 'dollar' },
  revenue_daemon: { label: 'Revenue & Charity Fund', group: 'Finance', icon: 'banknote' },
  growth_daemon: { label: 'SEO & User Growth', group: 'Growth', icon: 'trending-up' },
  competitive_dominance_daemon: { label: 'Competitive Benchmark Scorer', group: 'Strategy', icon: 'trophy' },
  self_expansion_daemon: { label: 'Auto-Daemon Creator', group: 'Self-Improvement', icon: 'seedling' },
  super_intelligence_daemon: { label: 'Prompt Evolution Engine', group: 'Self-Improvement', icon: 'sparkles' },
};

const GROUP_ORDER = ['Core', 'Research Pipeline', 'Security', 'Optimization', 'Self-Improvement', 'Self-Healing', 'Strategy', 'Awareness', 'Growth', 'Finance'];

const THROTTLE_COLORS: Record<string, string> = {
  green: '#10b981', yellow: '#f59e0b', orange: '#f97316', red: '#ef4444',
};

// SVG icon component
const Icon = ({ name, size = 18, color = 'currentColor' }: { name: string; size?: number; color?: string }) => {
  const icons: Record<string, string> = {
    search: 'M11 19a8 8 0 100-16 8 8 0 000 16zM21 21l-4.35-4.35',
    filter: 'M3 4h18l-7 8v7l-4 2v-9L3 4z',
    microscope: 'M6 18h8M9 18v3M12 14a5 5 0 100-10 5 5 0 000 10zM12 14v4M9 21h6',
    code: 'M16 18l6-6-6-6M8 6l-6 6 6 6',
    cpu: 'M4 4h16v16H4zM8 8h8v8H8z M9 1v3M15 1v3M9 20v3M15 20v3M1 9h3M1 15h3M20 9h3M20 15h3',
    shield: 'M12 2l9 4v6c0 5-3.5 9-9 10-5.5-1-9-5-9-10V6l9-4z',
    zap: 'M13 2L3 14h7l-1 8 10-12h-7l1-8z',
    film: 'M2 4h20v16H2zM2 8h20M2 16h20M7 4v16M17 4v16',
    megaphone: 'M3 11l14-7v16L3 13v-2zM3 11H1v4h2v-4z',
    refresh: 'M23 4v6h-6M1 20v-6h6M3.5 9a9 9 0 0114.85-3.36L23 10M1 14l4.65 4.36A9 9 0 0020.5 15',
    stethoscope: 'M4 3v6a5 5 0 0010 0V3M9 18a6 6 0 006-6v-3M15 9h3a3 3 0 010 6h-1',
    'bar-chart': 'M3 21V3M3 21h18M7 21v-6M12 21v-10M17 21v-4',
    globe: 'M12 2a10 10 0 100 20 10 10 0 000-20zM2 12h20M12 2a15 15 0 010 20M12 2a15 15 0 000 20',
    radar: 'M12 2a10 10 0 100 20 10 10 0 000-20zM12 12l8-4M12 12V4',
    robot: 'M12 2v4M8 6h8v8H8zM5 10v4M19 10v4M9 10h2M13 10h2M9 18h6',
    dollar: 'M12 1v22M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6',
    banknote: 'M6 3h12v18H6zM12 9a3 3 0 100 6 3 3 0 000-6z',
    'trending-up': 'M23 6l-9.5 9.5-5-5L1 18M17 6h6v6',
    trophy: 'M8 21h8M12 17v4M7 4h10v5a5 5 0 01-10 0V4zM7 4H4v3a3 3 0 003 3M17 4h3v3a3 3 0 01-3 3',
    seedling: 'M12 22V12M12 12c0-5-3-8-8-8 0 5 3 8 8 8zM12 12c0-5 3-8 8-8 0 5-3 8-8 8z',
    sparkles: 'M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z',
  };
  const d = icons[name] || '';
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d={d} />
    </svg>
  );
};

export default function HasanPage() {
  const [data, setData] = useState<HasanData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [now, setNow] = useState(new Date());
  const [selectedDaemon, setSelectedDaemon] = useState<DaemonStatus | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'daemons' | 'chat' | 'deploy'>('overview');
  const chatEndRef = useRef<HTMLDivElement>(null);
  const [deployData, setDeployData] = useState<any>(null);
  const [powerState, setPowerState] = useState<'active' | 'deactivated'>('deactivated');
  const [powerLoading, setPowerLoading] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch('/api/hasan', { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
      setError(null);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    const clock = setInterval(() => setNow(new Date()), 1000);
    // Fetch deployment data less frequently
    const fetchDeploy = async () => {
      try {
        const res = await fetch('/api/hasan/deploy', { cache: 'no-store' });
        if (res.ok) setDeployData(await res.json());
      } catch {}
    };
    fetchDeploy();
    const deployInterval = setInterval(fetchDeploy, 10000);
    // Fetch power state
    const fetchPower = async () => {
      try {
        const res = await fetch('/api/hasan/power', { cache: 'no-store' });
        if (res.ok) {
          const d = await res.json();
          setPowerState(d.status);
        }
      } catch {}
    };
    fetchPower();
    const powerInterval = setInterval(fetchPower, 5000);
    return () => { clearInterval(interval); clearInterval(clock); clearInterval(deployInterval); clearInterval(powerInterval); };
  }, [fetchData]);

  // Toggle Hasan on/off
  const togglePower = async () => {
    setPowerLoading(true);
    try {
      const action = powerState === 'active' ? 'deactivate' : 'activate';
      const res = await fetch('/api/hasan/power', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action }),
      });
      const d = await res.json();
      if (d.success) {
        setPowerState(action === 'activate' ? 'active' : 'deactivated');
        // Immediate refresh
        fetchData();
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setPowerLoading(false);
    }
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const sendChat = async () => {
    if (!chatInput.trim() || chatLoading) return;
    const userMsg: ChatMessage = { role: 'user', content: chatInput, timestamp: new Date().toISOString() };
    setChatMessages(prev => [...prev, userMsg]);
    setChatInput('');
    setChatLoading(true);
    try {
      const res = await fetch('/api/hasan/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg.content }),
      });
      const json = await res.json();
      const hasanMsg: ChatMessage = { role: 'hasan', content: json.response || 'No response', timestamp: new Date().toISOString() };
      setChatMessages(prev => [...prev, hasanMsg]);
    } catch (e: any) {
      setChatMessages(prev => [...prev, { role: 'hasan', content: `Error: ${e.message}`, timestamp: new Date().toISOString() }]);
    } finally {
      setChatLoading(false);
    }
  };

  if (loading && !data) {
    return (
      <div style={s.loadingWrap}>
        <motion.div animate={{ rotate: 360 }} transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
          style={s.loadingRing} />
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
          style={s.loadingText}>H A S A N</motion.p>
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 0.5 }} transition={{ delay: 0.6 }}
          style={s.loadingSub}>Initializing autonomous system...</motion.p>
      </div>
    );
  }

  const alive = data?.daemons.alive || 0;
  const total = data?.daemons.total || 23;
  const online = alive > 0;
  const throttleColor = THROTTLE_COLORS[data?.cost.throttleLevel || 'green'];
  const daemonsByGroup: Record<string, DaemonStatus[]> = {};
  (data?.daemons.list || []).forEach(d => {
    const meta = DAEMON_META[d.name] || { label: d.name, group: 'Other', icon: '' };
    if (!daemonsByGroup[meta.group]) daemonsByGroup[meta.group] = [];
    daemonsByGroup[meta.group].push(d);
  });

  return (
    <div style={s.page}>
      {/* Ambient background */}
      <div style={s.bgLayer1} />
      <div style={s.bgLayer2} />
      <div style={s.grain} />

      {/* Header */}
      <header style={s.header}>
        <div style={s.headerLeft}>
          <motion.div animate={{ opacity: online ? [0.4, 1, 0.4] : 0.2 }} transition={{ duration: 2, repeat: Infinity }}
            style={{ ...s.statusOrb, background: online ? '#10b981' : '#ef4444', boxShadow: `0 0 20px ${online ? '#10b981' : '#ef4444'}` }} />
          <div>
            <h1 style={s.logo}>HASAN</h1>
            <p style={s.logoSub}>Autonomous System · Named after Hasan ibn Ali (RA)</p>
          </div>
        </div>
        <div style={s.headerRight}>
          {/* Power Toggle */}
          <button
            onClick={togglePower}
            disabled={powerLoading}
            style={{
              ...s.powerBtn,
              background: powerState === 'active' ? 'rgba(239,68,68,0.1)' : 'rgba(16,185,129,0.1)',
              border: `1px solid ${powerState === 'active' ? 'rgba(239,68,68,0.3)' : 'rgba(16,185,129,0.3)'}`,
              color: powerState === 'active' ? '#ef4444' : '#10b981',
            }}
          >
            {powerLoading ? '...' : powerState === 'active' ? 'DEACTIVATE' : 'ACTIVATE'}
          </button>
          <div style={s.clockBox}>
            <span style={s.clockTime}>{now.toLocaleTimeString('en-GB', { hour12: false })}</span>
            <span style={s.clockDate}>{now.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })}</span>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <nav style={s.tabs}>
        {(['overview', 'daemons', 'chat', 'deploy'] as const).map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            style={{ ...s.tab, ...(activeTab === tab ? s.tabActive : {}) }}>
            {tab === 'overview' && 'Overview'}
            {tab === 'daemons' && `Daemons (${alive}/${total})`}
            {tab === 'chat' && 'Talk to Hasan'}
            {tab === 'deploy' && `Deploy${deployData?.pending_count > 0 ? ` (${deployData.pending_count})` : ''}`}
          </button>
        ))}
      </nav>

      <AnimatePresence mode="wait">
        {/* OVERVIEW TAB */}
        {activeTab === 'overview' && (
          <motion.div key="overview" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
            style={s.content}>
            {/* Deployment Notification Banner */}
            {deployData?.pending_count > 0 && (
              <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }}
                style={{ ...s.banner, borderColor: 'rgba(245,158,11,0.3)', background: 'rgba(245,158,11,0.05)', marginBottom: '12px' }}>
                <div style={s.bannerLeft}>
                  <h2 style={{ ...s.bannerTitle, color: '#f59e0b', fontSize: '16px' }}>
                    {deployData.pending_count} IMPROVEMENT{deployData.pending_count > 1 ? 'S' : ''} PENDING APPROVAL
                  </h2>
                  <p style={s.bannerSub}>Hasan has staged improvements. Review and deploy in the Deploy tab.</p>
                </div>
                <button onClick={() => setActiveTab('deploy')}
                  style={{ ...s.pill, cursor: 'pointer', border: '1px solid rgba(245,158,11,0.3)', background: 'rgba(245,158,11,0.1)' }}>
                  <span style={s.pillLabel}>REVIEW</span>
                  <span style={{ ...s.pillValue, color: '#f59e0b', fontSize: '14px' }}>{deployData.pending_count} →</span>
                </button>
              </motion.div>
            )}
            {/* Status Banner */}
            <div style={{ ...s.banner, borderColor: online ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)' }}>
              <div style={s.bannerLeft}>
                <h2 style={{ ...s.bannerTitle, color: online ? '#10b981' : '#ef4444' }}>
                  {online ? `${alive}/${total} SYSTEMS NOMINAL` : 'SYSTEM DEACTIVATED'}
                </h2>
                <p style={s.bannerSub}>
                  {online ? 'Hasan is watching. Learning. Improving. Serving.' : 'Say "activate Hasan" to wake the system.'}
                </p>
                {data?.identity?.verified && (
                  <p style={s.identityNote}>✓ Moral compass verified · {data.identity.purpose.substring(0, 60)}...</p>
                )}
              </div>
              <div style={s.bannerRight}>
                {[
                  { label: 'CREDITS', value: `$${(data?.cost.remainingCredits || 0).toFixed(2)}`, color: throttleColor },
                  { label: 'BURN/DAY', value: `$${(data?.cost.burnRatePerDay || 0).toFixed(2)}`, color: '#e0e0e8' },
                  { label: 'THROTTLE', value: (data?.cost.throttleLevel || 'green').toUpperCase(), color: throttleColor },
                  { label: 'TOKENS 24H', value: (data?.cost.totalTokens24h || 0).toLocaleString(), color: '#e0e0e8' },
                ].map(stat => (
                  <div key={stat.label} style={s.pill}>
                    <span style={s.pillLabel}>{stat.label}</span>
                    <span style={{ ...s.pillValue, color: stat.color }}>{stat.value}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Stat Cards */}
            <div style={s.cardGrid}>
              {/* SWOT Card */}
              <div style={s.card}>
                <div style={s.cardHead}><Icon name="bar-chart" size={16} color="#9ca3af" /><span style={s.cardTitle}>SWOT Analysis</span></div>
                {data?.swot ? (
                  <div style={s.swotRow}>
                    {[
                      { letter: 'S', count: data.swot.strengths, color: '#10b981' },
                      { letter: 'W', count: data.swot.weaknesses, color: '#ef4444' },
                      { letter: 'O', count: data.swot.opportunities, color: '#3b82f6' },
                      { letter: 'T', count: data.swot.threats, color: '#f59e0b' },
                    ].map(item => (
                      <div key={item.letter} style={s.swotCell}>
                        <span style={{ ...s.swotLetter, color: item.color }}>{item.letter}</span>
                        <span style={{ ...s.swotCount, color: item.color }}>{item.count}</span>
                      </div>
                    ))}
                  </div>
                ) : <p style={s.empty}>No SWOT data</p>}
              </div>

              {/* Queue Card */}
              <div style={s.card}>
                <div style={s.cardHead}><Icon name="code" size={16} color="#9ca3af" /><span style={s.cardTitle}>Pipeline Queue</span></div>
                <div style={s.queueRow}>
                  <div style={s.queueCell}><span style={s.queueNum}>{data?.queue.newFindings || 0}</span><span style={s.queueLabel}>Findings</span></div>
                  <div style={s.queueCell}><span style={s.queueNum}>{data?.queue.implementationQueue || 0}</span><span style={s.queueLabel}>To Build</span></div>
                  <div style={s.queueCell}><span style={{ ...s.queueNum, color: (data?.queue.implementationFailed || 0) > 0 ? '#ef4444' : '#e0e0e8' }}>{data?.queue.implementationFailed || 0}</span><span style={s.queueLabel}>Failed</span></div>
                </div>
              </div>

              {/* Memory Card */}
              <div style={s.card}>
                <div style={s.cardHead}><Icon name="cpu" size={16} color="#9ca3af" /><span style={s.cardTitle}>Memory</span></div>
                <div style={s.memRow}>
                  <div style={s.memCell}><span style={s.memNum}>{data?.sharedMemory.knowledgeFacts || 0}</span><span style={s.memLabel}>Shared Facts</span></div>
                  <div style={s.memCell}><span style={s.memNum}>{data?.unlimitedMemory.sizeMB || '0'}</span><span style={s.memLabel}>Unlimited (MB)</span></div>
                </div>
              </div>

              {/* Charity Fund Card */}
              <div style={{ ...s.card, border: '1px solid rgba(184,146,74,0.2)' }}>
                <div style={s.cardHead}><span style={{ ...s.cardTitle, color: '#b8924a' }}>💰 Charity Fund</span></div>
                <div style={s.ummahBox}>
                  <span style={s.ummahAmount}>${(data?.ummah.totalDistributed || 0).toFixed(2)}</span>
                  <span style={s.ummahLabel}>Total Distributed</span>
                  <span style={s.ummahNote}>25% of profit → Food · Clinics · Education</span>
                </div>
              </div>
            </div>

            {/* Live Activity Feed */}
            <div style={s.feedPanel}>
              <div style={s.feedHead}>
                <h3 style={s.feedTitle}>Live Activity</h3>
                <motion.div animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 1.5, repeat: Infinity }}
                  style={s.liveDot} />
              </div>
              <div style={s.feedList}>
                <AnimatePresence mode="popLayout">
                  {data?.activity.map((item, i) => (
                    <motion.div key={`${item.time}-${i}`} initial={{ opacity: 0, x: -15 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0 }}
                      style={s.feedItem}>
                      <span style={s.feedTime}>{item.time.split(' ')[1]}</span>
                      <span style={{ ...s.feedLevel, color: item.level === 'ERROR' ? '#ef4444' : item.level === 'WARNING' ? '#f59e0b' : '#10b981' }}>
                        {item.level}
                      </span>
                      <span style={s.feedDaemon}>{DAEMON_META[item.daemon]?.label || item.daemon}</span>
                      <span style={s.feedMsg}>{item.message}</span>
                    </motion.div>
                  ))}
                </AnimatePresence>
                {(!data?.activity || data.activity.length === 0) && (
                  <p style={s.empty}>{online ? 'Listening...' : 'System deactivated'}</p>
                )}
              </div>
            </div>
          </motion.div>
        )}

        {/* DAEMONS TAB */}
        {activeTab === 'daemons' && (
          <motion.div key="daemons" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
            style={s.content}>
            {GROUP_ORDER.map(group => {
              const daemons = daemonsByGroup[group];
              if (!daemons || daemons.length === 0) return null;
              return (
                <div key={group} style={s.daemonGroup}>
                  <h3 style={s.groupTitle}>{group}</h3>
                  <div style={s.daemonGrid}>
                    {daemons.map((d, i) => {
                      const meta = DAEMON_META[d.name] || { label: d.name, icon: '', group: '' };
                      const isAlive = d.alive;
                      const hbFresh = d.heartbeatAge !== null && d.heartbeatAge < 120;
                      const dotColor = isAlive ? (hbFresh ? '#10b981' : '#f59e0b') : '#ef4444';
                      return (
                        <motion.div key={d.name} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.02 }}
                          whileHover={{ scale: 1.04, y: -2 }} onClick={() => setSelectedDaemon(d)}
                          style={{ ...s.daemonCard, borderColor: `${dotColor}30` }}>
                          <div style={{ ...s.daemonIconBox, color: dotColor }}>
                            <Icon name={meta.icon} size={22} color={dotColor} />
                          </div>
                          <div style={s.daemonText}>
                            <span style={s.daemonLabel}>{meta.label}</span>
                            <span style={s.daemonStatus}>
                              {isAlive ? (hbFresh ? 'Active' : 'Stale') : 'Offline'}
                              {d.heartbeatAge !== null && ` · ${d.heartbeatAge}s`}
                            </span>
                          </div>
                          <motion.div animate={isAlive && hbFresh ? { opacity: [0.4, 1, 0.4], scale: [1, 1.2, 1] } : { opacity: 0.3 }}
                            transition={{ duration: 2, repeat: Infinity }}
                            style={{ ...s.daemonDot, background: dotColor, boxShadow: `0 0 8px ${dotColor}` }} />
                        </motion.div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </motion.div>
        )}

        {/* CHAT TAB */}
        {activeTab === 'chat' && (
          <motion.div key="chat" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
            style={s.chatContainer}>
            <div style={s.chatHeader}>
              <motion.div animate={{ opacity: online ? [0.4, 1, 0.4] : 0.2 }} transition={{ duration: 2, repeat: Infinity }}
                style={{ ...s.chatOrb, background: online ? '#10b981' : '#ef4444' }} />
              <div>
                <h2 style={s.chatTitle}>Hasan</h2>
                <p style={s.chatStatus}>{online ? 'Online · Ready to talk' : 'Offline · System deactivated'}</p>
              </div>
            </div>
            <div style={s.chatMessages}>
              {chatMessages.length === 0 && (
                <div style={s.chatWelcome}>
                  <p style={s.chatWelcomeTitle}>As-salamu alaykum, Ggs</p>
                  <p style={s.chatWelcomeSub}>I am Hasan. Ask me about the system's status, what I'm working on, or what I recommend.</p>
                  <div style={s.chatSuggestions}>
                    {['What are you working on?', 'Show me the SWOT analysis', 'What should we improve next?', 'How much have we spent?'].map(sugg => (
                      <button key={sugg} onClick={() => { setChatInput(sugg); }} style={s.suggestionBtn}>{sugg}</button>
                    ))}
                  </div>
                </div>
              )}
              {chatMessages.map((msg, i) => (
                <div key={i} style={{ ...s.msgRow, flexDirection: msg.role === 'user' ? 'row-reverse' as any : 'row' }}>
                  <div style={{ ...s.msgBubble, ...(msg.role === 'user' ? s.msgUser : s.msgHasan) }}>
                    <p style={s.msgText}>{msg.content}</p>
                  </div>
                </div>
              ))}
              {chatLoading && (
                <div style={s.msgRow}>
                  <div style={{ ...s.msgBubble, ...s.msgHasan }}>
                    <motion.span animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 1, repeat: Infinity }}
                      style={s.thinking}>Hasan is thinking...</motion.span>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
            <div style={s.chatInputBox}>
              <input
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); } }}
                placeholder="Message Hasan..."
                style={s.chatInput}
                disabled={chatLoading}
              />
              <button onClick={sendChat} disabled={chatLoading || !chatInput.trim()} style={s.sendBtn}>
                <Icon name="zap" size={18} color="#0a0a0f" />
              </button>
            </div>
          </motion.div>
        )}

        {/* DEPLOY TAB */}
        {activeTab === 'deploy' && (
          <motion.div key="deploy" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
            style={s.content}>
            <div style={{ ...s.banner, borderColor: 'rgba(59,130,246,0.2)' }}>
              <div style={s.bannerLeft}>
                <h2 style={{ ...s.bannerTitle, color: '#3b82f6', fontSize: '18px' }}>DEPLOYMENT CENTER</h2>
                <p style={s.bannerSub}>Hasan works in staging. Approve improvements to merge into main.</p>
              </div>
              <div style={s.bannerRight}>
                <div style={s.pill}><span style={s.pillLabel}>PENDING</span><span style={{ ...s.pillValue, color: '#f59e0b' }}>{deployData?.pending_count || 0}</span></div>
                <div style={s.pill}><span style={s.pillLabel}>STAGING</span><span style={{ ...s.pillValue, color: '#3b82f6' }}>{deployData?.staging_count || 0}</span></div>
                <div style={s.pill}><span style={s.pillLabel}>APPROVED</span><span style={{ ...s.pillValue, color: '#10b981' }}>{deployData?.approved_count || 0}</span></div>
                <div style={s.pill}><span style={s.pillLabel}>REJECTED</span><span style={{ ...s.pillValue, color: '#ef4444' }}>{deployData?.rejected_count || 0}</span></div>
              </div>
            </div>

            {/* Agent Scaling */}
            {deployData?.agent_scaling && (
              <div style={{ ...s.card, marginBottom: '16px' }}>
                <div style={s.cardHead}>
                  <Icon name="robot" size={16} color="#9ca3af" />
                  <span style={s.cardTitle}>Research Agents</span>
                  <span style={{ marginLeft: 'auto', fontSize: '12px', color: '#8b8b9b' }}>
                    {deployData.agent_scaling.current_research_agents} active (min {deployData.agent_scaling.min || 1}, max {deployData.agent_scaling.max || 8})
                  </span>
                </div>
                {deployData.agent_scaling.scale_reason && (
                  <p style={{ fontSize: '11px', color: '#6b6b7b', marginTop: '4px' }}>
                    Last: {deployData.agent_scaling.scale_reason} · {deployData.agent_scaling.last_scaled ? new Date(deployData.agent_scaling.last_scaled).toLocaleString() : 'N/A'}
                  </p>
                )}
              </div>
            )}

            {/* Pending Approval */}
            <div style={{ ...s.card, marginBottom: '16px' }}>
              <div style={s.cardHead}>
                <span style={s.cardTitle}>Pending Approval</span>
                {deployData?.pending_count > 0 && (
                  <button onClick={async () => { await fetch('/api/hasan/deploy', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action: 'approve_all' }) }); }}
                    style={{ marginLeft: 'auto', background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', color: '#10b981', fontSize: '11px', fontWeight: 600, padding: '6px 14px', borderRadius: '8px', cursor: 'pointer' }}>
                    APPROVE ALL
                  </button>
                )}
              </div>
              {(deployData?.pending_findings || []).filter((f: any) => f.status === 'pending_approval').length === 0 ? (
                <p style={s.empty}>No improvements pending. Hasan is working in staging.</p>
              ) : (
                (deployData?.pending_findings || []).filter((f: any) => f.status === 'pending_approval').map((f: any, i: number) => (
                  <motion.div key={f.id || i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}
                    style={{ background: 'rgba(245,158,11,0.04)', border: '1px solid rgba(245,158,11,0.15)', borderRadius: '10px', padding: '14px', marginBottom: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div style={{ flex: 1 }}>
                        <h4 style={{ fontSize: '13px', fontWeight: 600, color: '#e8e8f0', margin: 0 }}>{f.title || 'Untitled'}</h4>
                        {f.summary && <p style={{ fontSize: '12px', color: '#8b8b9b', marginTop: '6px' }}>{f.summary}</p>}
                        {f.improvements && (
                          <ul style={{ fontSize: '11px', color: '#6b6b7b', marginTop: '8px', paddingLeft: '16px' }}>
                            {f.improvements.map((imp: string, j: number) => <li key={j}>{imp}</li>)}
                          </ul>
                        )}
                        <p style={{ fontSize: '10px', color: '#6b6b7b', marginTop: '6px' }}>
                          Requested: {f.requested_at ? new Date(f.requested_at).toLocaleString() : 'N/A'}
                        </p>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginLeft: '12px' }}>
                        <button onClick={async () => { await fetch('/api/hasan/deploy', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action: 'approve', finding_id: f.id }) }); }}
                          style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', color: '#10b981', fontSize: '11px', fontWeight: 600, padding: '6px 14px', borderRadius: '8px', cursor: 'pointer' }}>
                          APPROVE
                        </button>
                        <button onClick={async () => { await fetch('/api/hasan/deploy', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action: 'reject', finding_id: f.id }) }); }}
                          style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#ef4444', fontSize: '11px', fontWeight: 600, padding: '6px 14px', borderRadius: '8px', cursor: 'pointer' }}>
                          REJECT
                        </button>
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
            </div>

            {/* In Staging */}
            <div style={{ ...s.card }}>
              <div style={s.cardHead}><span style={s.cardTitle}>In Staging (not yet requested)</span></div>
              {(deployData?.pending_findings || []).filter((f: any) => f.status === 'in_staging').length === 0 ? (
                <p style={s.empty}>No items in staging.</p>
              ) : (
                (deployData?.pending_findings || []).filter((f: any) => f.status === 'in_staging').map((f: any, i: number) => (
                  <div key={f.id || i} style={{ background: 'rgba(59,130,246,0.04)', border: '1px solid rgba(59,130,246,0.1)', borderRadius: '10px', padding: '12px', marginBottom: '8px' }}>
                    <h4 style={{ fontSize: '12px', color: '#e8e8f0', margin: 0 }}>{f.title || 'Untitled'}</h4>
                    {f.summary && <p style={{ fontSize: '11px', color: '#8b8b9b', marginTop: '4px' }}>{f.summary}</p>}
                  </div>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      <AnimatePresence>
        {selectedDaemon && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={() => setSelectedDaemon(null)} style={s.modalBg}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }}
              onClick={e => e.stopPropagation()} style={s.modal}>
              <div style={s.modalHead}>
                <div style={{ ...s.modalIcon, color: selectedDaemon.alive ? '#10b981' : '#ef4444' }}>
                  <Icon name={DAEMON_META[selectedDaemon.name]?.icon || ''} size={28} color={selectedDaemon.alive ? '#10b981' : '#ef4444'} />
                </div>
                <div>
                  <h3 style={s.modalTitle}>{DAEMON_META[selectedDaemon.name]?.label || selectedDaemon.name}</h3>
                  <span style={s.modalGroup}>{DAEMON_META[selectedDaemon.name]?.group}</span>
                </div>
              </div>
              <div style={s.modalBody}>
                {[
                  ['Status', selectedDaemon.alive ? 'ALIVE' : 'OFFLINE'],
                  ['PID', selectedDaemon.pid?.toString() || 'N/A'],
                  ['Heartbeat', selectedDaemon.heartbeatAge !== null ? `${selectedDaemon.heartbeatAge}s ago` : 'N/A'],
                  ['Cycle Duration', selectedDaemon.extra.cycle_duration ? `${selectedDaemon.extra.cycle_duration}s` : 'N/A'],
                  ['Last Run', selectedDaemon.extra.last_run ? selectedDaemon.extra.last_run.substring(0, 19) : 'N/A'],
                ].map(([k, v]) => (
                  <div key={k} style={s.modalRow}>
                    <span style={s.modalKey}>{k}</span>
                    <span style={s.modalVal}>{v}</span>
                  </div>
                ))}
              </div>
              <button onClick={() => setSelectedDaemon(null)} style={s.modalClose}>Close</button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error Toast */}
      <AnimatePresence>
        {error && (
          <motion.div initial={{ opacity: 0, y: 50 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 50 }}
            style={s.toast}>
            <span style={{ color: '#ef4444' }}>⚠</span> {error}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ============================================================
// STYLES
// ============================================================
const s: Record<string, React.CSSProperties> = {
  page: { minHeight: '100vh', background: '#08080c', color: '#c8c8d4', fontFamily: "'IBM Plex Sans', sans-serif", position: 'relative', overflow: 'hidden' },
  powerBtn: { fontSize: '11px', fontWeight: 700, letterSpacing: '1px', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer', marginRight: '14px', transition: 'all 0.2s', fontFamily: "'JetBrains Mono', monospace" },
  bgLayer1: { position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 20% 30%, rgba(59,130,246,0.08) 0%, transparent 50%)', pointerEvents: 'none' },
  bgLayer2: { position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 80% 70%, rgba(139,92,246,0.06) 0%, transparent 50%)', pointerEvents: 'none' },
  grain: { position: 'absolute', inset: 0, opacity: 0.02, pointerEvents: 'none', backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")" },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '24px 32px', position: 'relative', zIndex: 1, borderBottom: '1px solid rgba(255,255,255,0.05)' },
  headerLeft: { display: 'flex', alignItems: 'center', gap: '14px' },
  statusOrb: { width: '14px', height: '14px', borderRadius: '50%' },
  logo: { fontSize: '26px', fontWeight: 900, letterSpacing: '6px', margin: 0, color: '#e8e8f0', fontFamily: "'IBM Plex Sans', sans-serif" },
  logoSub: { fontSize: '11px', color: '#6b6b7b', letterSpacing: '0.5px', margin: 0 },
  headerRight: { display: 'flex', alignItems: 'center' },
  clockBox: { display: 'flex', flexDirection: 'column', alignItems: 'flex-end' },
  clockTime: { fontSize: '22px', fontWeight: 600, fontFamily: "'JetBrains Mono', monospace", color: '#3b82f6' },
  clockDate: { fontSize: '11px', color: '#6b6b7b', marginTop: '2px' },
  tabs: { display: 'flex', gap: '4px', padding: '0 32px', position: 'relative', zIndex: 1, borderBottom: '1px solid rgba(255,255,255,0.05)' },
  tab: { background: 'transparent', border: 'none', color: '#6b6b7b', fontSize: '13px', fontWeight: 500, padding: '14px 20px', cursor: 'pointer', borderBottom: '2px solid transparent', transition: 'all 0.2s' },
  tabActive: { color: '#e8e8f0', borderBottom: '2px solid #3b82f6' },
  content: { padding: '24px 32px', position: 'relative', zIndex: 1, maxWidth: '1400px', margin: '0 auto' },
  banner: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '16px', padding: '24px 28px', marginBottom: '20px', backdropFilter: 'blur(10px)' },
  bannerLeft: { flex: 1 },
  bannerTitle: { fontSize: '20px', fontWeight: 700, margin: 0, fontFamily: "'JetBrains Mono', monospace", letterSpacing: '1px' },
  bannerSub: { fontSize: '13px', color: '#8b8b9b', marginTop: '6px' },
  identityNote: { fontSize: '11px', color: '#10b981', marginTop: '8px' },
  bannerRight: { display: 'flex', gap: '10px' },
  pill: { display: 'flex', flexDirection: 'column', alignItems: 'center', background: 'rgba(255,255,255,0.04)', borderRadius: '10px', padding: '10px 18px', minWidth: '90px' },
  pillLabel: { fontSize: '9px', color: '#6b6b7b', letterSpacing: '1px' },
  pillValue: { fontSize: '16px', fontWeight: 600, fontFamily: "'JetBrains Mono', monospace", marginTop: '4px' },
  cardGrid: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px', marginBottom: '20px' },
  card: { background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px', padding: '18px', backdropFilter: 'blur(10px)' },
  cardHead: { display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' },
  cardTitle: { fontSize: '12px', fontWeight: 600, color: '#8b8b9b', letterSpacing: '0.5px' },
  swotRow: { display: 'flex', justifyContent: 'space-around' },
  swotCell: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' },
  swotLetter: { fontSize: '14px', fontWeight: 700 },
  swotCount: { fontSize: '28px', fontWeight: 900, fontFamily: "'JetBrains Mono', monospace" },
  queueRow: { display: 'flex', justifyContent: 'space-around' },
  queueCell: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' },
  queueNum: { fontSize: '28px', fontWeight: 900, fontFamily: "'JetBrains Mono', monospace", color: '#e8e8f0' },
  queueLabel: { fontSize: '10px', color: '#6b6b7b' },
  memRow: { display: 'flex', justifyContent: 'space-around' },
  memCell: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' },
  memNum: { fontSize: '24px', fontWeight: 900, fontFamily: "'JetBrains Mono', monospace", color: '#8b5cf6' },
  memLabel: { fontSize: '10px', color: '#6b6b7b' },
  ummahBox: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' },
  ummahAmount: { fontSize: '32px', fontWeight: 900, color: '#b8924a', fontFamily: "'JetBrains Mono', monospace" },
  ummahLabel: { fontSize: '10px', color: '#8b8b9b' },
  ummahNote: { fontSize: '9px', color: '#6b6b7b', textAlign: 'center', marginTop: '6px' },
  feedPanel: { background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px', padding: '20px', backdropFilter: 'blur(10px)' },
  feedHead: { display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' },
  feedTitle: { fontSize: '14px', fontWeight: 600, color: '#8b8b9b', margin: 0 },
  liveDot: { width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444' },
  feedList: { maxHeight: '320px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '4px' },
  feedItem: { display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 12px', background: 'rgba(255,255,255,0.01)', borderRadius: '6px', fontSize: '12px' },
  feedTime: { fontFamily: "'JetBrains Mono', monospace", color: '#6b6b7b', fontSize: '11px', flexShrink: 0 },
  feedLevel: { fontSize: '10px', fontWeight: 700, flexShrink: 0, width: '50px' },
  feedDaemon: { color: '#3b82f6', fontSize: '11px', flexShrink: 0, width: '100px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  feedMsg: { color: '#a8a8b8', fontSize: '11px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 },
  empty: { textAlign: 'center', color: '#4b4b5b', padding: '20px', fontSize: '13px' },
  // Daemons tab
  daemonGroup: { marginBottom: '24px' },
  groupTitle: { fontSize: '13px', fontWeight: 600, color: '#6b6b7b', letterSpacing: '1px', textTransform: 'uppercase', marginBottom: '12px' },
  daemonGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '10px' },
  daemonCard: { display: 'flex', alignItems: 'center', gap: '12px', padding: '14px', borderRadius: '10px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', cursor: 'pointer', transition: 'all 0.2s' },
  daemonIconBox: { width: '40px', height: '40px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(255,255,255,0.03)' },
  daemonText: { flex: 1, minWidth: 0 },
  daemonLabel: { fontSize: '13px', fontWeight: 600, color: '#e8e8f0', display: 'block' },
  daemonStatus: { fontSize: '11px', color: '#6b6b7b' },
  daemonDot: { width: '10px', height: '10px', borderRadius: '50%', flexShrink: 0 },
  // Chat tab
  chatContainer: { maxWidth: '800px', margin: '0 auto', padding: '24px', position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)' },
  chatHeader: { display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '20px', paddingBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.06)' },
  chatOrb: { width: '14px', height: '14px', borderRadius: '50%' },
  chatTitle: { fontSize: '20px', fontWeight: 700, margin: 0, color: '#e8e8f0' },
  chatStatus: { fontSize: '12px', color: '#6b6b7b', margin: 0 },
  chatMessages: { flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '16px' },
  chatWelcome: { textAlign: 'center', padding: '40px 20px' },
  chatWelcomeTitle: { fontSize: '22px', fontWeight: 700, color: '#e8e8f0', marginBottom: '8px' },
  chatWelcomeSub: { fontSize: '14px', color: '#8b8b9b', marginBottom: '20px' },
  chatSuggestions: { display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center' },
  suggestionBtn: { background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.2)', borderRadius: '20px', padding: '8px 16px', color: '#3b82f6', fontSize: '12px', cursor: 'pointer', transition: 'all 0.2s' },
  msgRow: { display: 'flex', gap: '10px' },
  msgBubble: { maxWidth: '70%', padding: '12px 16px', borderRadius: '16px' },
  msgUser: { background: '#3b82f6', color: '#fff' },
  msgHasan: { background: 'rgba(255,255,255,0.06)', color: '#c8c8d4', border: '1px solid rgba(255,255,255,0.08)' },
  msgText: { fontSize: '14px', lineHeight: 1.5, margin: 0, whiteSpace: 'pre-wrap' },
  thinking: { fontSize: '13px', color: '#8b8b9b' },
  chatInputBox: { display: 'flex', gap: '8px', paddingBottom: '4px' },
  chatInput: { flex: 1, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '12px', padding: '14px 18px', color: '#e8e8f0', fontSize: '14px', outline: 'none', fontFamily: "'IBM Plex Sans', sans-serif" },
  sendBtn: { background: '#3b82f6', border: 'none', borderRadius: '12px', padding: '0 20px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'all 0.2s' },
  // Modal
  modalBg: { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 },
  modal: { background: '#111118', border: '1px solid rgba(59,130,246,0.2)', borderRadius: '16px', padding: '28px', minWidth: '340px' },
  modalHead: { display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px' },
  modalIcon: { width: '48px', height: '48px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(255,255,255,0.03)' },
  modalTitle: { fontSize: '20px', fontWeight: 700, margin: 0, color: '#e8e8f0' },
  modalGroup: { fontSize: '11px', color: '#6b6b7b', background: 'rgba(255,255,255,0.04)', padding: '2px 8px', borderRadius: '4px' },
  modalBody: { display: 'flex', flexDirection: 'column', gap: '10px' },
  modalRow: { display: 'flex', justifyContent: 'space-between', fontSize: '13px', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.04)' },
  modalKey: { color: '#6b6b7b' },
  modalVal: { color: '#e8e8f0', fontFamily: "'JetBrains Mono', monospace" },
  modalClose: { marginTop: '20px', width: '100%', padding: '10px', background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.2)', borderRadius: '8px', color: '#3b82f6', cursor: 'pointer', fontSize: '14px' },
  // Toast
  toast: { position: 'fixed', bottom: '20px', left: '50%', transform: 'translateX(-50%)', background: '#111118', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '10px', padding: '12px 24px', fontSize: '13px', zIndex: 200 },
  // Loading
  loadingWrap: { minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#08080c', gap: '16px' },
  loadingRing: { width: '50px', height: '50px', borderRadius: '50%', border: '3px solid rgba(59,130,246,0.2)', borderTopColor: '#3b82f6' },
  loadingText: { color: '#3b82f6', fontSize: '20px', letterSpacing: '8px', fontWeight: 700 },
  loadingSub: { color: '#6b6b7b', fontSize: '13px' },
};