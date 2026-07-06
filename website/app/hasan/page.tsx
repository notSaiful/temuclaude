'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// ============================================================
// HASAN — Autonomous System Live Interface
// Named after Hasan ibn Ali (RA), grandson of Prophet Muhammad ﷺ
// "The chief of the youth of Paradise"
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
  ummah: { totalDistributed: number; entries: number; lastDistribution: any };
  activity: ActivityItem[];
  stats: { testFiles: number; sourceModules: number };
}

// Daemon display config — friendly names + categories + icons
const DAEMON_INFO: Record<string, { friendly: string; category: string; icon: string }> = {
  scout_daemon: { friendly: 'Scout', category: 'Research', icon: '🔍' },
  distiller_daemon: { friendly: 'Distiller', category: 'Research', icon: '⚗️' },
  research_daemon_1: { friendly: 'Researcher 1', category: 'Research', icon: '🔬' },
  research_daemon_2: { friendly: 'Researcher 2', category: 'Research', icon: '🔬' },
  research_daemon_3: { friendly: 'Researcher 3', category: 'Research', icon: '🔬' },
  integrator_daemon: { friendly: 'Integrator', category: 'Research', icon: '⚙️' },
  coordinator_daemon: { friendly: 'Coordinator', category: 'Core', icon: '🧠' },
  cyber_daemon: { friendly: 'Cyber Shield', category: 'Security', icon: '🛡️' },
  efficiency_daemon: { friendly: 'Efficiency', category: 'Optimization', icon: '⚡' },
  media_daemon: { friendly: 'Media Lab', category: 'Research', icon: '🎬' },
  marketing_daemon: { friendly: 'Marketing', category: 'Growth', icon: '📢' },
  feedback_daemon: { friendly: 'Feedback', category: 'Self-Improvement', icon: '🔄' },
  meta_auditor_daemon: { friendly: 'Meta-Auditor', category: 'Self-Healing', icon: '🩺' },
  swot_daemon: { friendly: 'SWOT Analyst', category: 'Strategy', icon: '📊' },
  website_daemon: { friendly: 'Website Updater', category: 'Growth', icon: '🌐' },
  industry_radar_daemon: { friendly: 'Industry Radar', category: 'Awareness', icon: '📡' },
  model_optimizer_daemon: { friendly: 'Model Optimizer', category: 'Optimization', icon: '🤖' },
  cost_efficiency_daemon: { friendly: 'Cost Guard', category: 'Finance', icon: '💰' },
  revenue_daemon: { friendly: 'Revenue Engine', category: 'Finance', icon: '💵' },
  growth_daemon: { friendly: 'Growth Engine', category: 'Growth', icon: '📈' },
  competitive_dominance_daemon: { friendly: 'Competitive Edge', category: 'Strategy', icon: '🏆' },
  self_expansion_daemon: { friendly: 'Self-Expander', category: 'Self-Improvement', icon: '🌱' },
  super_intelligence_daemon: { friendly: 'Super Intelligence', category: 'Self-Improvement', icon: '✨' },
};

const THROTTLE_COLORS: Record<string, string> = {
  green: '#10b981',
  yellow: '#f59e0b',
  orange: '#f97316',
  red: '#ef4444',
};

export default function HasanPage() {
  const [data, setData] = useState<HasanData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [time, setTime] = useState(new Date());
  const [selectedDaemon, setSelectedDaemon] = useState<string | null>(null);
  const [pulse, setPulse] = useState(0);

  // Fetch data every 3 seconds
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
    const clock = setInterval(() => setTime(new Date()), 1000);
    const pulseInterval = setInterval(() => setPulse(p => (p + 1) % 100), 50);
    return () => {
      clearInterval(interval);
      clearInterval(clock);
      clearInterval(pulseInterval);
    };
  }, [fetchData]);

  // Loading state
  if (loading && !data) {
    return (
      <div style={styles.loadingContainer}>
        <motion.div
          animate={{ scale: [1, 1.1, 1], opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity }}
          style={styles.loadingRing}
        />
        <p style={styles.loadingText}>HASAN initializing...</p>
      </div>
    );
  }

  const aliveCount = data?.daemons.alive || 0;
  const totalDaemons = data?.daemons.total || 23;
  const systemOnline = aliveCount > 0;
  const throttleColor = THROTTLE_COLORS[data?.cost.throttleLevel || 'green'];

  return (
    <div style={styles.container}>
      {/* Ambient background grid */}
      <div style={styles.gridBg} />

      {/* Top Bar */}
      <div style={styles.topBar}>
        <div style={styles.logo}>
          <motion.div
            animate={{ opacity: systemOnline ? [0.5, 1, 0.5] : 0.3 }}
            transition={{ duration: 3, repeat: Infinity }}
            style={{ ...styles.statusDot, background: systemOnline ? '#10b981' : '#ef4444' }}
          />
          <h1 style={styles.title}>HASAN</h1>
          <span style={styles.subtitle}>Autonomous System Interface</span>
        </div>
        <div style={styles.clock}>
          <span style={styles.timeText}>{time.toLocaleTimeString('en-US', { hour12: false })}</span>
          <span style={styles.dateText}>{time.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</span>
        </div>
      </div>

        {/* System Status Banner */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          style={styles.statusBanner}
        >
          <div style={styles.statusLeft}>
            <h2 style={{
              ...styles.statusTitle,
              color: systemOnline ? '#10b981' : '#ef4444'
            }}>
              {systemOnline ? `${aliveCount}/${totalDaemons} DAEMONS ACTIVE` : 'SYSTEM DEACTIVATED'}
            </h2>
            <p style={styles.statusSub}>
              {systemOnline
                ? 'All systems operational. Hasan is watching, learning, improving.'
                : 'Hasan is resting. Say "activate Hasan" to wake it up.'}
            </p>
          </div>
          <div style={styles.statusRight}>
            <div style={styles.statPill}>
              <span style={styles.statLabel}>CREDITS</span>
              <span style={{ ...styles.statValue, color: throttleColor }}>
                ${(data?.cost.remainingCredits || 0).toFixed(2)}
              </span>
            </div>
            <div style={styles.statPill}>
              <span style={styles.statLabel}>BURN/DAY</span>
              <span style={styles.statValue}>${(data?.cost.burnRatePerDay || 0).toFixed(2)}</span>
            </div>
            <div style={styles.statPill}>
              <span style={styles.statLabel}>THROTTLE</span>
              <span style={{ ...styles.statValue, color: throttleColor, textTransform: 'uppercase' }}>
                {data?.cost.throttleLevel || 'green'}
              </span>
            </div>
          </div>
        </motion.div>

        {/* Main Grid */}
        <div style={styles.mainGrid}>
          {/* Left: Daemon Grid */}
          <div style={styles.panel}>
            <div style={styles.panelHeader}>
              <h3 style={styles.panelTitle}>⚡ DAEMON GRID</h3>
              <span style={styles.panelCount}>{aliveCount}/{totalDaemons}</span>
            </div>
            <div style={styles.daemonGrid}>
              {data?.daemons.list.map((daemon, i) => {
                const info = DAEMON_INFO[daemon.name] || { friendly: daemon.name, category: 'Unknown', icon: '❓' };
                const isAlive = daemon.alive;
                const hbAge = daemon.heartbeatAge;
                const hbFresh = hbAge !== null && hbAge < 120;
                return (
                  <motion.div
                    key={daemon.name}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: i * 0.03 }}
                    whileHover={{ scale: 1.05, zIndex: 10 }}
                    onClick={() => setSelectedDaemon(selectedDaemon === daemon.name ? null : daemon.name)}
                    style={{
                      ...styles.daemonCard,
                      borderColor: isAlive
                        ? (hbFresh ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)')
                        : 'rgba(239, 68, 68, 0.2)',
                      background: selectedDaemon === daemon.name
                        ? 'rgba(59, 130, 246, 0.1)'
                        : 'rgba(255, 255, 255, 0.03)',
                      cursor: 'pointer',
                    }}
                  >
                    <div style={styles.daemonIcon}>{info.icon}</div>
                    <div style={styles.daemonInfo}>
                      <div style={styles.daemonName}>{info.friendly}</div>
                      <div style={styles.daemonCategory}>{info.category}</div>
                    </div>
                    <motion.div
                      animate={isAlive && hbFresh ? { opacity: [0.4, 1, 0.4] } : { opacity: 0.2 }}
                      transition={{ duration: 2, repeat: Infinity }}
                      style={{
                        ...styles.daemonDot,
                        background: isAlive
                          ? (hbFresh ? '#10b981' : '#f59e0b')
                          : '#ef4444',
                      }}
                    />
                  </motion.div>
                );
              })}
            </div>
          </div>

          {/* Right: Activity Feed + Stats */}
          <div style={styles.rightColumn}>
            {/* Activity Feed */}
            <div style={styles.panel}>
              <div style={styles.panelHeader}>
                <h3 style={styles.panelTitle}>📡 LIVE ACTIVITY</h3>
                <motion.div
                  animate={{ opacity: [0.3, 1, 0.3] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  style={styles.liveIndicator}
                />
              </div>
              <div style={styles.activityFeed}>
                <AnimatePresence mode="popLayout">
                  {data?.activity.map((item, i) => (
                    <motion.div
                      key={`${item.time}-${i}`}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      transition={{ duration: 0.3 }}
                      style={styles.activityItem}
                    >
                      <span style={styles.activityTime}>{item.time.split(' ')[1]}</span>
                      <span style={{
                        ...styles.activityLevel,
                        color: item.level === 'ERROR' ? '#ef4444' : '#10b981'
                      }}>
                        {item.level}
                      </span>
                      <span style={styles.activityDaemon}>
                        {DAEMON_INFO[item.daemon]?.friendly || item.daemon}
                      </span>
                      <span style={styles.activityMessage}>{item.message}</span>
                    </motion.div>
                  ))}
                </AnimatePresence>
                {(!data?.activity || data.activity.length === 0) && (
                  <div style={styles.emptyState}>
                    {systemOnline ? 'Waiting for activity...' : 'System deactivated'}
                  </div>
                )}
              </div>
            </div>

            {/* Stats Row */}
            <div style={styles.statsRow}>
              {/* SWOT */}
              <div style={styles.statCard}>
                <h4 style={styles.statCardTitle}>📊 SWOT</h4>
                {data?.swot ? (
                  <div style={styles.swotGrid}>
                    <div style={{ ...styles.swotItem, color: '#10b981' }}>
                      <span style={styles.swotNum}>{data.swot.strengths}</span>
                      <span style={styles.swotLabel}>S</span>
                    </div>
                    <div style={{ ...styles.swotItem, color: '#ef4444' }}>
                      <span style={styles.swotNum}>{data.swot.weaknesses}</span>
                      <span style={styles.swotLabel}>W</span>
                    </div>
                    <div style={{ ...styles.swotItem, color: '#3b82f6' }}>
                      <span style={styles.swotNum}>{data.swot.opportunities}</span>
                      <span style={styles.swotLabel}>O</span>
                    </div>
                    <div style={{ ...styles.swotItem, color: '#f59e0b' }}>
                      <span style={styles.swotNum}>{data.swot.threats}</span>
                      <span style={styles.swotLabel}>T</span>
                    </div>
                  </div>
                ) : <span style={styles.emptyState}>No data</span>}
              </div>

              {/* Queue */}
              <div style={styles.statCard}>
                <h4 style={styles.statCardTitle}>🔄 QUEUE</h4>
                <div style={styles.queueItems}>
                  <div style={styles.queueItem}>
                    <span style={styles.queueNum}>{data?.queue.newFindings || 0}</span>
                    <span style={styles.queueLabel}>Findings</span>
                  </div>
                  <div style={styles.queueItem}>
                    <span style={styles.queueNum}>{data?.queue.implementationQueue || 0}</span>
                    <span style={styles.queueLabel}>Implement</span>
                  </div>
                  <div style={styles.queueItem}>
                    <span style={{ ...styles.queueNum, color: (data?.queue.implementationFailed || 0) > 0 ? '#ef4444' : '#fff' }}>
                      {data?.queue.implementationFailed || 0}
                    </span>
                    <span style={styles.queueLabel}>Failed</span>
                  </div>
                </div>
              </div>

              {/* Memory */}
              <div style={styles.statCard}>
                <h4 style={styles.statCardTitle}>🧠 MEMORY</h4>
                <div style={styles.memoryInfo}>
                  <div style={styles.memItem}>
                    <span style={styles.memNum}>{data?.sharedMemory.knowledgeFacts || 0}</span>
                    <span style={styles.memLabel}>Shared</span>
                  </div>
                  <div style={styles.memItem}>
                    <span style={styles.memNum}>{data?.unlimitedMemory.sizeMB || '0'}</span>
                    <span style={styles.memLabel}>Unlimited MB</span>
                  </div>
                </div>
              </div>

              {/* Ummah Fund */}
              <div style={{ ...styles.statCard, borderColor: 'rgba(184, 146, 74, 0.3)' }}>
                <h4 style={{ ...styles.statCardTitle, color: '#b8924a' }}>🤲 UMMAH FUND</h4>
                <div style={styles.ummahInfo}>
                  <span style={styles.ummahAmount}>
                    ${(data?.ummah.totalDistributed || 0).toFixed(2)}
                  </span>
                  <span style={styles.ummahLabel}>Total Distributed</span>
                  <span style={styles.ummahNote}>
                    25% of profit → Palestine food, clinics, schools
                  </span>
                </div>
              </div>
            </div>

            {/* Radar */}
            {data?.radar && (
              <div style={styles.panel}>
                <div style={styles.panelHeader}>
                  <h3 style={styles.panelTitle}>📡 INDUSTRY RADAR</h3>
                  <span style={styles.panelCount}>{data.radar.totalSignals} signals</span>
                </div>
                <p style={styles.radarText}>
                  Scanning Hacker News, GitHub, HuggingFace, RSS feeds, Reddit, competitor changelogs
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div style={styles.footer}>
          <span style={styles.footerText}>
            HASAN — Named after Hasan ibn Ali (RA), chief of the youth of Paradise
          </span>
          <span style={styles.footerStats}>
            {data?.stats.sourceModules || 0} modules · {data?.stats.testFiles || 0} test files · 315 tests
          </span>
        </div>

      {/* Selected daemon detail popup */}
      <AnimatePresence>
        {selectedDaemon && data && (() => {
          const daemon = data.daemons.list.find(d => d.name === selectedDaemon);
          if (!daemon) return null;
          const info = DAEMON_INFO[daemon.name] || { friendly: daemon.name, category: 'Unknown', icon: '❓' };
          return (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              style={styles.detailPopup}
              onClick={() => setSelectedDaemon(null)}
            >
              <div style={styles.detailContent} onClick={e => e.stopPropagation()}>
                <div style={styles.detailHeader}>
                  <span style={styles.detailIcon}>{info.icon}</span>
                  <h3 style={styles.detailTitle}>{info.friendly}</h3>
                  <span style={styles.detailCategory}>{info.category}</span>
                </div>
                <div style={styles.detailBody}>
                  <div style={styles.detailRow}>
                    <span style={styles.detailKey}>Status</span>
                    <span style={{ color: daemon.alive ? '#10b981' : '#ef4444' }}>
                      {daemon.alive ? 'ALIVE' : 'OFFLINE'}
                    </span>
                  </div>
                  <div style={styles.detailRow}>
                    <span style={styles.detailKey}>PID</span>
                    <span style={styles.detailMono}>{daemon.pid || 'N/A'}</span>
                  </div>
                  <div style={styles.detailRow}>
                    <span style={styles.detailKey}>Heartbeat</span>
                    <span>{daemon.heartbeatAge !== null ? `${daemon.heartbeatAge}s ago` : 'N/A'}</span>
                  </div>
                  <div style={styles.detailRow}>
                    <span style={styles.detailKey}>Cycle</span>
                    <span>{daemon.extra.cycle_duration ? `${daemon.extra.cycle_duration}s` : 'N/A'}</span>
                  </div>
                  {daemon.extra.last_run && (
                    <div style={styles.detailRow}>
                      <span style={styles.detailKey}>Last Run</span>
                      <span style={styles.detailMono}>{daemon.extra.last_run.substring(0, 19)}</span>
                    </div>
                  )}
                </div>
                <button style={styles.detailClose} onClick={() => setSelectedDaemon(null)}>Close</button>
              </div>
            </motion.div>
          );
        })()}
      </AnimatePresence>

      {/* Error toast */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            style={styles.errorToast}
          >
            <span style={{ color: '#ef4444' }}>⚠</span> Connection error: {error}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ============================================================
// STYLES — Dark, futuristic, JARVIS-inspired
// ============================================================
const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    background: '#0a0a0f',
    color: '#e0e0e8',
    fontFamily: "'Inter', -apple-system, sans-serif",
    padding: '20px',
    position: 'relative',
    overflow: 'hidden',
  },
  gridBg: {
    position: 'absolute',
    top: 0, left: 0, right: 0, bottom: 0,
    backgroundImage: `
      linear-gradient(rgba(59, 130, 246, 0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(59, 130, 246, 0.03) 1px, transparent 1px)
    `,
    backgroundSize: '50px 50px',
    pointerEvents: 'none',
  },
  topBar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
    position: 'relative',
    zIndex: 1,
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  statusDot: {
    width: '12px',
    height: '12px',
    borderRadius: '50%',
    boxShadow: '0 0 10px currentColor',
  },
  title: {
    fontSize: '28px',
    fontWeight: 700,
    letterSpacing: '4px',
    margin: 0,
    background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
  },
  subtitle: {
    fontSize: '12px',
    color: '#6b7280',
    letterSpacing: '1px',
  },
  clock: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-end',
  },
  timeText: {
    fontSize: '24px',
    fontFamily: "'JetBrains Mono', monospace",
    fontWeight: 600,
    color: '#3b82f6',
  },
  dateText: {
    fontSize: '12px',
    color: '#6b7280',
  },
  statusBanner: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    background: 'rgba(255, 255, 255, 0.03)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '12px',
    padding: '20px 24px',
    marginBottom: '20px',
    position: 'relative',
    zIndex: 1,
  },
  statusLeft: { flex: 1 },
  statusTitle: {
    fontSize: '22px',
    fontWeight: 700,
    margin: 0,
    fontFamily: "'JetBrains Mono', monospace",
  },
  statusSub: {
    fontSize: '13px',
    color: '#6b7280',
    marginTop: '4px',
  },
  statusRight: {
    display: 'flex',
    gap: '12px',
  },
  statPill: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: '8px',
    padding: '8px 16px',
    minWidth: '80px',
  },
  statLabel: {
    fontSize: '10px',
    color: '#6b7280',
    letterSpacing: '1px',
  },
  statValue: {
    fontSize: '18px',
    fontWeight: 600,
    fontFamily: "'JetBrains Mono', monospace",
    marginTop: '2px',
  },
  mainGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '20px',
    position: 'relative',
    zIndex: 1,
  },
  panel: {
    background: 'rgba(255, 255, 255, 0.03)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '12px',
    padding: '20px',
  },
  panelHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
  },
  panelTitle: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#9ca3af',
    letterSpacing: '1px',
    margin: 0,
  },
  panelCount: {
    fontSize: '12px',
    color: '#3b82f6',
    fontFamily: "'JetBrains Mono', monospace",
  },
  liveIndicator: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    background: '#ef4444',
  },
  daemonGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
    gap: '10px',
  },
  daemonCard: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '12px',
    borderRadius: '8px',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    transition: 'all 0.2s',
  },
  daemonIcon: { fontSize: '20px' },
  daemonInfo: { flex: 1, minWidth: 0 },
  daemonName: {
    fontSize: '13px',
    fontWeight: 600,
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  daemonCategory: {
    fontSize: '10px',
    color: '#6b7280',
  },
  daemonDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    flexShrink: 0,
  },
  rightColumn: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
  },
  activityFeed: {
    maxHeight: '300px',
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  activityItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 12px',
    background: 'rgba(255, 255, 255, 0.02)',
    borderRadius: '6px',
    fontSize: '12px',
  },
  activityTime: {
    fontFamily: "'JetBrains Mono', monospace",
    color: '#6b7280',
    fontSize: '11px',
    flexShrink: 0,
  },
  activityLevel: {
    fontSize: '10px',
    fontWeight: 600,
    flexShrink: 0,
    width: '40px',
  },
  activityDaemon: {
    color: '#3b82f6',
    fontSize: '11px',
    flexShrink: 0,
    width: '80px',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  activityMessage: {
    color: '#d1d5db',
    fontSize: '11px',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    flex: 1,
  },
  emptyState: {
    textAlign: 'center',
    color: '#4b5563',
    padding: '20px',
    fontSize: '13px',
  },
  statsRow: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '12px',
  },
  statCard: {
    background: 'rgba(255, 255, 255, 0.03)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: '10px',
    padding: '16px',
  },
  statCardTitle: {
    fontSize: '12px',
    fontWeight: 600,
    color: '#9ca3af',
    margin: '0 0 12px 0',
  },
  swotGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr 1fr 1fr',
    gap: '8px',
  },
  swotItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  swotNum: {
    fontSize: '24px',
    fontWeight: 700,
    fontFamily: "'JetBrains Mono', monospace",
  },
  swotLabel: {
    fontSize: '10px',
    color: '#6b7280',
  },
  queueItems: {
    display: 'flex',
    justifyContent: 'space-around',
  },
  queueItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  queueNum: {
    fontSize: '24px',
    fontWeight: 700,
    fontFamily: "'JetBrains Mono', monospace",
  },
  queueLabel: {
    fontSize: '10px',
    color: '#6b7280',
  },
  memoryInfo: {
    display: 'flex',
    justifyContent: 'space-around',
  },
  memItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  memNum: {
    fontSize: '20px',
    fontWeight: 700,
    fontFamily: "'JetBrains Mono', monospace",
    color: '#8b5cf6',
  },
  memLabel: {
    fontSize: '10px',
    color: '#6b7280',
  },
  ummahInfo: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '4px',
  },
  ummahAmount: {
    fontSize: '28px',
    fontWeight: 700,
    color: '#b8924a',
    fontFamily: "'JetBrains Mono', monospace",
  },
  ummahLabel: {
    fontSize: '10px',
    color: '#9ca3af',
  },
  ummahNote: {
    fontSize: '9px',
    color: '#6b7280',
    textAlign: 'center',
    marginTop: '4px',
  },
  radarText: {
    fontSize: '12px',
    color: '#6b7280',
  },
  footer: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: '24px',
    padding: '12px 0',
    borderTop: '1px solid rgba(255, 255, 255, 0.05)',
    position: 'relative',
    zIndex: 1,
  },
  footerText: {
    fontSize: '11px',
    color: '#4b5563',
  },
  footerStats: {
    fontSize: '11px',
    color: '#6b7280',
    fontFamily: "'JetBrains Mono', monospace",
  },
  // Loading
  loadingContainer: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#0a0a0f',
    gap: '20px',
  },
  loadingRing: {
    width: '60px',
    height: '60px',
    borderRadius: '50%',
    border: '3px solid #3b82f6',
    borderTopColor: 'transparent',
  },
  loadingText: {
    color: '#3b82f6',
    fontSize: '18px',
    letterSpacing: '2px',
  },
  // Detail popup
  detailPopup: {
    position: 'fixed',
    top: 0, left: 0, right: 0, bottom: 0,
    background: 'rgba(0, 0, 0, 0.7)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 100,
  },
  detailContent: {
    background: '#13131a',
    border: '1px solid rgba(59, 130, 246, 0.3)',
    borderRadius: '12px',
    padding: '24px',
    minWidth: '320px',
  },
  detailHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '16px',
  },
  detailIcon: { fontSize: '28px' },
  detailTitle: {
    fontSize: '20px',
    fontWeight: 700,
    margin: 0,
  },
  detailCategory: {
    fontSize: '11px',
    color: '#6b7280',
    background: 'rgba(255, 255, 255, 0.05)',
    padding: '2px 8px',
    borderRadius: '4px',
  },
  detailBody: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  detailRow: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '13px',
  },
  detailKey: { color: '#6b7280' },
  detailMono: { fontFamily: "'JetBrains Mono', monospace" },
  detailClose: {
    marginTop: '16px',
    padding: '8px 16px',
    background: 'rgba(59, 130, 246, 0.1)',
    border: '1px solid rgba(59, 130, 246, 0.3)',
    borderRadius: '6px',
    color: '#3b82f6',
    cursor: 'pointer',
    fontSize: '13px',
    width: '100%',
  },
  errorToast: {
    position: 'fixed',
    bottom: '20px',
    left: '50%',
    transform: 'translateX(-50%)',
    background: '#1a1a2e',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    borderRadius: '8px',
    padding: '12px 20px',
    fontSize: '13px',
    zIndex: 200,
  },
};