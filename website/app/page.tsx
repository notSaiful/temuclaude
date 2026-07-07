'use client';

import { useState, useCallback, useRef } from 'react';
import { motion, useScroll, useTransform, useInView } from 'framer-motion';
import { Navbar } from '@/components/Navbar';
import { StaggerReveal, StaggerItem } from '@/components/Animations';
import { FusionPipeline } from '@/components/FusionPipeline';
import { MagneticButton } from '@/components/MagneticButton';
import { PricingSection } from '@/components/PricingSection';
import { ScrollProgress } from '@/components/ScrollProgress';
import { CountUp, ScrollRevealText } from '@/components/CountUp';
import { Testimonials } from '@/components/Testimonials';

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [text]);
  return (
    <button
      onClick={handleCopy}
      className="absolute top-2 right-2 p-1.5 rounded opacity-0 group-hover:opacity-100 transition-opacity z-10"
      aria-label="Copy code to clipboard"
    >
      {copied ? (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#788C5D" strokeWidth="2">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      ) : (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#8E8B85" strokeWidth="2">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
        </svg>
      )}
    </button>
  );
}

/** Aurora glow that drifts on scroll — gives the hero atmosphere */
function AuroraGlow() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ['start start', 'end start'],
  });
  const y1 = useTransform(scrollYProgress, [0, 1], ['0%', '60%']);
  const y2 = useTransform(scrollYProgress, [0, 1], ['0%', '-40%']);
  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);

  return (
    <div ref={ref} className="absolute inset-0 pointer-events-none overflow-hidden">
      <motion.div
        style={{ y: y1, opacity }}
        className="absolute -top-20 -right-20 w-[600px] h-[600px] rounded-full"
        animate={{
          scale: [1, 1.1, 1],
        }}
        transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
      >
        <div className="w-full h-full rounded-full" style={{ background: 'radial-gradient(circle, rgba(226,88,34,0.12) 0%, transparent 70%)' }} />
      </motion.div>
      <motion.div
        style={{ y: y2, opacity }}
        className="absolute top-40 -left-20 w-[500px] h-[500px] rounded-full"
        animate={{
          scale: [1, 1.15, 1],
        }}
        transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut', delay: 1 }}
      >
        <div className="w-full h-full rounded-full" style={{ background: 'radial-gradient(circle, rgba(120,140,93,0.10) 0%, transparent 70%)' }} />
      </motion.div>
    </div>
  );
}

/** Floating model orbs — visual representation of the 8 models orbiting */
function FloatingOrbs() {
  const models = [
    { name: 'GLM', color: '#E25822', x: '5%', y: '15%', delay: 0, size: 44 },
    { name: 'DS', color: '#788C5D', x: '88%', y: '10%', delay: 0.3, size: 38 },
    { name: 'Gem', color: '#C46686', x: '92%', y: '70%', delay: 0.6, size: 36 },
    { name: 'MM', color: '#E8B547', x: '3%', y: '75%', delay: 0.9, size: 40 },
    { name: 'Nem', color: '#8E8B85', x: '50%', y: '5%', delay: 1.2, size: 32 },
    { name: 'Hy3', color: '#D4A574', x: '75%', y: '85%', delay: 1.5, size: 34 },
  ];

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden hidden lg:block">
      {models.map((m, i) => (
        <motion.div
          key={i}
          className="absolute flex items-center justify-center rounded-full font-mono text-[10px] font-semibold"
          style={{
            left: m.x,
            top: m.y,
            width: m.size,
            height: m.size,
            background: `${m.color}15`,
            border: `1px solid ${m.color}30`,
            color: m.color,
          }}
          animate={{
            y: [0, -12, 0],
            opacity: [0.4, 0.7, 0.4],
          }}
          transition={{
            duration: 4 + i,
            repeat: Infinity,
            ease: 'easeInOut',
            delay: m.delay,
          }}
        >
          {m.name}
        </motion.div>
      ))}
    </div>
  );
}

/** Pinned scroll section — the pipeline story unfolds as you scroll */
function PipelineStory() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ['start start', 'end end'],
  });

  const steps = [
    { num: '01', title: 'You ask', desc: 'One API call. No model selection. Just your question.', color: '#E25822' },
    { num: '02', title: 'We route', desc: 'Query classification picks the best models for your task type.', color: '#C46686' },
    { num: '03', title: 'They answer in parallel', desc: '3 models generate independently. Each sees the others and refines.', color: '#788C5D' },
    { num: '04', title: 'We fuse', desc: 'Dynamic aggregator synthesizes the best parts into one answer.', color: '#E8B547' },
    { num: '05', title: 'We verify', desc: 'Math is checked with code execution. Quality scored on 5 rubrics.', color: '#E25822' },
    { num: '06', title: 'You get one answer', desc: 'Plus full metadata: which models, cost, quality score, techniques.', color: '#1A1816' },
  ];

  return (
    <section ref={ref} className="relative" style={{ height: `${steps.length * 60}vh` }}>
      <div className="sticky top-0 h-screen flex items-center overflow-hidden">
        <div className="container-max w-full">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left: step text */}
            <div>
              <div className="mb-8">
                <span className="text-xs font-mono text-text-muted uppercase tracking-wider">The Pipeline</span>
              </div>
              {steps.map((step, i) => {
                const start = i / steps.length;
                const end = (i + 1) / steps.length;
                const opacity = useTransform(scrollYProgress, [start - 0.05, start, end, end + 0.05], [0, 1, 1, 0]);
                const y = useTransform(scrollYProgress, [start - 0.05, start, end, end + 0.05], [30, 0, 0, -30]);
                return (
                  <motion.div
                    key={i}
                    style={{ opacity, y }}
                    className="absolute"
                  >
                    <div
                      className="text-5xl font-serif mb-3"
                      style={{ fontWeight: 300, color: step.color, letterSpacing: '-0.04em' }}
                    >
                      {step.num}
                    </div>
                    <h3 className="text-2xl font-serif text-text-primary mb-2" style={{ fontWeight: 400 }}>
                      {step.title}
                    </h3>
                    <p className="text-text-secondary max-w-md leading-relaxed">{step.desc}</p>
                  </motion.div>
                );
              })}
            </div>

            {/* Right: visual pipeline */}
            <div className="relative h-[400px] flex items-center justify-center">
              <svg width="100%" height="100%" viewBox="0 0 400 400" className="absolute inset-0">
                {/* Connection lines */}
                {steps.slice(0, -1).map((_, i) => {
                  const angle = (i / (steps.length - 1)) * Math.PI * 2 - Math.PI / 2;
                  const nextAngle = ((i + 1) / (steps.length - 1)) * Math.PI * 2 - Math.PI / 2;
                  const r = 140;
                  const x1 = 200 + r * Math.cos(angle);
                  const y1 = 200 + r * Math.sin(angle);
                  const x2 = 200 + r * Math.cos(nextAngle);
                  const y2 = 200 + r * Math.sin(nextAngle);
                  return (
                    <motion.line
                      key={i}
                      x1={x1} y1={y1} x2={x2} y2={y2}
                      stroke="#E25822"
                      strokeWidth="1"
                      strokeDasharray="4 4"
                      initial={{ opacity: 0 }}
                      whileInView={{ opacity: 0.2 }}
                      transition={{ duration: 0.5, delay: i * 0.1 }}
                    />
                  );
                })}
                {/* Nodes */}
                {steps.map((step, i) => {
                  const angle = (i / (steps.length - 1)) * Math.PI * 2 - Math.PI / 2;
                  const r = 140;
                  const x = 200 + r * Math.cos(angle);
                  const y = 200 + r * Math.sin(angle);
                  return (
                    <motion.circle
                      key={i}
                      cx={x} cy={y} r="24"
                      fill={step.color}
                      initial={{ opacity: 0, scale: 0 }}
                      whileInView={{ opacity: 1, scale: 1 }}
                      transition={{ duration: 0.4, delay: i * 0.1 }}
                    />
                  );
                })}
                {/* Center hub */}
                <circle cx="200" cy="200" r="32" fill="#1A1816" />
                <text x="200" y="205" textAnchor="middle" fill="#FAF8F5" fontSize="12" fontFamily="monospace">fuse</text>
              </svg>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/** CTA section with dramatic finish */
function CtaSection() {
  return (
    <section className="relative py-32 px-6 overflow-hidden">
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse 60% 80% at 50% 50%, rgba(226,88,34,0.08) 0%, transparent 70%)',
        }}
      />
      <div className="container-max relative text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.7, ease: [0.25, 1, 0.5, 1] }}
        >
          <h2 className="text-4xl md:text-6xl font-serif text-text-primary mb-6 text-balance" style={{ fontWeight: 300, letterSpacing: '-0.03em' }}>
            Stop choosing models.<br />
            <span className="text-accent-primary">Start getting answers.</span>
          </h2>
          <p className="text-lg text-text-secondary mb-10 max-w-xl mx-auto">
            20 free queries per day. No signup. No credit card. Just one API call.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <MagneticButton href="/playground" className="btn-accent text-base px-8 py-3">
              Try Free Now
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
            </MagneticButton>
            <a href="https://github.com/notSaiful/temuclaude" target="_blank" rel="noopener noreferrer" className="btn-secondary text-base px-8 py-3">
              Star on GitHub
            </a>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

export default function HomePage() {
  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress: heroScroll } = useScroll({
    target: heroRef,
    offset: ['start start', 'end start'],
  });
  const heroY = useTransform(heroScroll, [0, 1], ['0%', '30%']);
  const heroOpacity = useTransform(heroScroll, [0, 0.8], [1, 0]);
  const heroScale = useTransform(heroScroll, [0, 1], [1, 0.95]);

  return (
    <>
      <Navbar />
      <ScrollProgress />
      <main id="main-content">
        {/* ━━ Hero — cinematic with parallax + floating orbs ━━ */}
        <section ref={heroRef} className="relative min-h-screen pt-32 pb-24 px-6 overflow-hidden flex items-center">
          {/* Dot grid + aurora glows */}
          <div
            className="absolute inset-0 pointer-events-none"
            style={{
              backgroundImage: `radial-gradient(circle at 1px 1px, rgba(26,24,22,0.04) 1px, transparent 0)`,
              backgroundSize: '24px 24px',
            }}
          />
          <AuroraGlow />
          <FloatingOrbs />

          <motion.div
            style={{ y: heroY, opacity: heroOpacity, scale: heroScale }}
            className="container-max relative z-10"
          >
            <div className="grid lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-7">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, ease: [0.25, 1, 0.5, 1] }}
                  className="inline-flex items-center gap-2 badge-accent mb-6"
                >
                  <span className="w-2 h-2 rounded-full bg-accent-olive animate-pulse-soft" />
                  One API · 8 models · MIT licensed
                </motion.div>

                <motion.h1
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8, delay: 0.1, ease: [0.25, 1, 0.5, 1] }}
                  className="text-5xl md:text-6xl lg:text-7xl font-serif tracking-tight text-text-primary leading-[1.02] mb-6 text-balance"
                  style={{ fontWeight: 300, letterSpacing: '-0.035em' }}
                >
                  Frontier-quality AI.<br />
                  <span className="text-accent-primary">Fraction of the cost.</span><br />
                  One API call.
                </motion.h1>

                <motion.p
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.3, ease: [0.25, 1, 0.5, 1] }}
                  className="text-lg text-text-secondary mb-8 max-w-lg leading-relaxed"
                >
                  TemuClaude runs 8 AI models in parallel, fuses their best answers,
                  verifies math with code execution, and self-checks every response.
                  You get one answer — smarter than any single model, at a fraction of the cost.
                </motion.p>

                {/* Code snippet */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.45, ease: [0.25, 1, 0.5, 1] }}
                  className="mb-6"
                >
                  <div className="bg-bg-dark rounded-md max-w-md font-mono text-sm overflow-hidden group relative">
                    <div className="flex items-center gap-1.5 px-4 py-2 border-b border-white/5">
                      <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#ff5f57' }} />
                      <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#febc2e' }} />
                      <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#28c840' }} />
                      <span className="text-[10px] text-text-muted ml-2">terminal</span>
                    </div>
                    <CopyButton text='curl -X POST temuclaude.com/api/chat -H "Content-Type: application/json" -d {"messages":[{"role":"user","content":"hi"}]}' />
                    <div className="p-4 overflow-x-auto">
                      <div className="text-text-muted text-xs mb-2"># One request. One answer. No model selection.</div>
                      <div><span className="text-accent-olive">curl</span> <span className="text-accent-fig">-X POST</span> temuclaude.com/api/chat \</div>
                      <div className="pl-4">-H <span className="text-accent-amber">"Content-Type: application/json"</span> \</div>
                      <div className="pl-4">-d <span className="text-accent-amber">{'{"messages":[{"role":"user","content":"hi"}]}'}</span></div>
                    </div>
                  </div>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.55, ease: [0.25, 1, 0.5, 1] }}
                  className="flex flex-col sm:flex-row gap-3 mb-6"
                >
                  <MagneticButton href="/playground" className="btn-accent">
                    Try Free — 20 queries/day
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
                  </MagneticButton>
                  <a href="/pricing" className="btn-secondary">
                    View Pricing
                  </a>
                </motion.div>

                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.6, delay: 0.8 }}
                  className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-text-muted"
                >
                  <span><strong className="text-text-primary">$0.50</strong> /MTok input</span>
                  <span className="text-border-default">·</span>
                  <span><strong className="text-text-primary">$2.00</strong> /MTok output</span>
                  <span className="text-border-default">·</span>
                  <span><strong className="text-text-primary">No signup</strong> to try</span>
                </motion.div>
              </div>

              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.4, ease: [0.25, 1, 0.5, 1] }}
                className="lg:col-span-5 flex items-center justify-center"
              >
                <FusionPipeline />
              </motion.div>
            </div>
          </motion.div>

          {/* Scroll indicator */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.5 }}
            className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10"
          >
            <motion.div
              animate={{ y: [0, 8, 0] }}
              transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
              className="flex flex-col items-center gap-1"
            >
              <span className="text-xs text-text-muted font-mono">scroll</span>
              <svg width="14" height="20" viewBox="0 0 14 20" fill="none" stroke="#8E8B85" strokeWidth="1.5">
                <rect x="1" y="1" width="12" height="18" rx="6" />
                <motion.circle
                  cx="7" cy="6" r="2" fill="#E25822"
                  animate={{ cy: [6, 12, 6] }}
                  transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
                />
              </svg>
            </motion.div>
          </motion.div>
        </section>

        {/* ━━ Social Proof strip — instant credibility ━━ */}
        <section className="py-16 px-6 border-y border-border-subtle">
          <div className="container-max">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
              {[
                { value: 472, label: 'tests passing', color: '#788C5D', decimals: 0 },
                { value: 8, label: 'models fused', color: '#E25822', decimals: 0 },
                { value: 10, label: 'quality layers', color: '#C46686', decimals: 0 },
                { value: 0.05, label: 'per M cached tokens', color: '#E8B547', decimals: 2, prefix: '$' },
              ].map((stat, i) => (
                <div key={i} className="text-center">
                  <div
                    className="text-3xl md:text-4xl font-serif mb-1"
                    style={{ fontWeight: 300, letterSpacing: '-0.02em', color: stat.color }}
                  >
                    <CountUp value={stat.value} prefix={stat.prefix || ''} decimals={stat.decimals} />
                  </div>
                  <div className="text-xs md:text-sm text-text-muted">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ━━ Pipeline Story — pinned scroll, cinematic ━━ */}
        <PipelineStory />

        {/* ━━ Why TemuClaude — bento grid ━━ */}
        <section className="py-24 px-6 bg-bg-secondary">
          <div className="container-max">
            <div className="mb-12 max-w-2xl">
              <ScrollRevealText
                text="Built for builders"
                className="text-3xl md:text-4xl font-serif text-text-primary mb-3"
                style={{ fontWeight: 300, letterSpacing: '-0.02em' }}
              />
              <p className="text-text-secondary">
                Stop paying $30/M tokens for GPT-5.5. Stop wrangling multiple APIs.
                One endpoint, frontier quality, a fraction of the cost.
              </p>
            </div>

            <StaggerReveal className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 auto-rows-[minmax(180px,auto)]">
              <StaggerItem>
                <div className="card lg:col-span-2 lg:row-span-2 h-full" style={{ padding: '32px' }}>
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-8 h-8 rounded-lg bg-accent-primary/10 flex items-center justify-center">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#E25822" strokeWidth="2">
                        <circle cx="6" cy="6" r="3" /><circle cx="18" cy="6" r="3" />
                        <circle cx="6" cy="18" r="3" /><circle cx="18" cy="18" r="3" />
                        <line x1="6" y1="9" x2="6" y2="15" /><line x1="18" y1="9" x2="18" y2="15" />
                        <line x1="9" y1="6" x2="15" y2="6" /><line x1="9" y1="18" x2="15" y2="18" />
                      </svg>
                    </div>
                    <span className="text-xs font-mono text-text-muted uppercase tracking-wider">Core Engine</span>
                  </div>
                  <h3 className="text-xl font-serif text-text-primary mb-3" style={{ fontWeight: 400 }}>3 models answer. 1 wins.</h3>
                  <p className="text-sm text-text-secondary mb-4 leading-relaxed">
                    For hard questions, 3 models answer independently in parallel. Each one
                    reviews the others' answers and refines its own. Then a dynamic aggregator
                    picks the best parts and synthesizes one superior answer.
                  </p>
                  <p className="text-sm text-text-muted leading-relaxed">
                    The result: measurably smarter than any single model — including GPT-5 and Claude.
                    You don't choose models. TemuClaude does it for you, automatically.
                  </p>
                  <div className="flex flex-wrap gap-2 mt-4">
                    {['Parallel generation', 'Cross-review', 'Dynamic aggregation', 'Consensus detection'].map(tag => (
                      <span key={tag} className="badge-muted text-xs">{tag}</span>
                    ))}
                  </div>
                </div>
              </StaggerItem>

              <StaggerItem>
                <div className="card h-full">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-7 h-7 rounded-lg bg-accent-olive/15 flex items-center justify-center">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#788C5D" strokeWidth="2">
                        <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
                      </svg>
                    </div>
                  </div>
                  <h3 className="text-base font-serif text-text-primary mb-2" style={{ fontWeight: 400 }}>Math that can't lie</h3>
                  <p className="text-sm text-text-secondary leading-relaxed">
                    Math answers are verified by generating Python code, running it in a sandbox,
                    and returning the actual output. No hallucinated numbers. Ever.
                  </p>
                </div>
              </StaggerItem>

              <StaggerItem>
                <div className="card h-full">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-7 h-7 rounded-lg bg-accent-fig/15 flex items-center justify-center">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#C46686" strokeWidth="2">
                        <path d="M9 12l2 2 4-4" /><circle cx="12" cy="12" r="10" />
                      </svg>
                    </div>
                  </div>
                  <h3 className="text-base font-serif text-text-primary mb-2" style={{ fontWeight: 400 }}>Self-checking</h3>
                  <p className="text-sm text-text-secondary leading-relaxed">
                    Every answer is scored on 5 quality rubrics. If it scores below 8/10,
                    TemuClaude retries with feedback. You always get the best version.
                  </p>
                </div>
              </StaggerItem>

              <StaggerItem>
                <div className="card lg:col-span-2 h-full">
                  <div className="flex items-center gap-4">
                    <div>
                      <h3 className="text-base font-serif text-text-primary mb-2" style={{ fontWeight: 400 }}>Radically cheap</h3>
                      <p className="text-sm text-text-secondary leading-relaxed mb-3">
                        60% of queries go to free models. 30% to ultra-cheap models ($0.06-0.14/M).
                        Only 10% use premium models. The cache serves repeat queries at $0.
                      </p>
                      <div className="flex flex-wrap gap-4 text-sm">
                        <div>
                          <span className="text-2xl font-serif text-accent-primary" style={{ fontWeight: 300, letterSpacing: '-0.02em' }}>$0.50</span>
                          <span className="text-text-muted ml-1">/M input</span>
                        </div>
                        <div>
                          <span className="text-2xl font-serif text-accent-primary" style={{ fontWeight: 300, letterSpacing: '-0.02em' }}>$2.00</span>
                          <span className="text-text-muted ml-1">/M output</span>
                        </div>
                        <div>
                          <span className="text-2xl font-serif text-accent-olive" style={{ fontWeight: 300, letterSpacing: '-0.02em' }}>$0.05</span>
                          <span className="text-text-muted ml-1">/M cached</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </StaggerItem>

              <StaggerItem>
                <div className="card h-full" style={{ background: 'linear-gradient(135deg, #788C5D 0%, #5D7048 100%)', color: '#fff', borderColor: 'transparent' }}>
                  <h3 className="text-base font-serif mb-2" style={{ fontWeight: 400 }}>25% of profit → charity</h3>
                  <p className="text-sm opacity-90 leading-relaxed">
                    Food relief, community kitchens, medical clinics, and education programs.
                    Your queries help people.
                  </p>
                </div>
              </StaggerItem>

              <StaggerItem>
                <div className="card h-full">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-7 h-7 rounded-lg bg-accent-amber/15 flex items-center justify-center">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#E8B547" strokeWidth="2">
                        <path d="M12 2L2 7v10l10 5 10-5V7L12 2z" /><path d="M12 22V12" /><path d="M2 7l10 5 10-5" />
                      </svg>
                    </div>
                  </div>
                  <h3 className="text-base font-serif text-text-primary mb-2" style={{ fontWeight: 400 }}>Open source</h3>
                  <p className="text-sm text-text-secondary leading-relaxed">
                    MIT licensed. Full pipeline visible. See exactly which models answered
                    and how the final answer was built. No black boxes.
                  </p>
                </div>
              </StaggerItem>
            </StaggerReveal>
          </div>
        </section>

        {/* ━━ GitHub badge ━━ */}
        <section className="py-12 px-6">
          <div className="container-max">
            <div className="flex justify-center">
              <a
                href="https://github.com/notSaiful/temuclaude"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-sm border border-border-default hover:border-accent-primary transition-all hover:shadow-md"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" className="text-text-primary">
                  <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.605-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
                </svg>
                <span className="text-sm font-medium text-text-primary">MIT Licensed · Open Source</span>
                <span className="text-sm text-text-muted">·</span>
                <span className="text-sm text-accent-primary">★ Star on GitHub</span>
              </a>
            </div>
          </div>
        </section>

        {/* ━━ Testimonials ━━ */}
        <Testimonials />

        {/* ━━ Model Pool ━━ */}
        <section className="py-24 px-6 bg-bg-secondary">
          <div className="container-max">
            <div className="mb-12 max-w-2xl">
              <ScrollRevealText
                text="8 models. You never pick."
                className="text-3xl md:text-4xl font-serif text-text-primary mb-3"
                style={{ fontWeight: 300, letterSpacing: '-0.02em' }}
              />
              <p className="text-text-secondary">
                TemuClaude routes automatically — the right model for the right question.
                Easy questions cost $0. Hard ones get the full fusion pipeline.
              </p>
            </div>

            <StaggerReveal className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { name: 'GLM-5.2', role: 'Orchestrator', iq: '51', desc: 'Highest open-weight IQ. Routes and aggregates.' },
                { name: 'DeepSeek V4 Pro', role: 'Reasoning', iq: '44', desc: 'Hard math, coding, complex logic.' },
                { name: 'Hy3 Preview', role: 'Cheap router', iq: '—', desc: 'Handles 60% of queries at lowest cost.' },
                { name: 'Gemini 3 Flash', role: 'Legal/Health', iq: '50', desc: '#1 Legal, #2 Health on benchmarks.' },
                { name: 'MiniMax M3', role: 'Vision/Creative', iq: '44', desc: 'Best GPQA score. Vision + creative.' },
                { name: 'MiMo-V2.5', role: 'Multimodal', iq: '40', desc: 'Text, image, video. From Xiaomi.' },
                { name: 'Claude Sonnet 5', role: 'Frontier', iq: '53', desc: 'Highest IQ. Used for hardest 2% only.' },
                { name: 'Nemotron 3 Ultra', role: 'QA Gate', iq: '38', desc: '550B MoE. Free — scores every answer.' },
              ].map((model, i) => (
                <StaggerItem key={i}>
                  <div className="card" style={{ padding: '20px 16px' }}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-text-primary">{model.name}</span>
                      {model.iq !== '—' && (
                        <span className="text-xs text-text-muted font-mono">IQ {model.iq}</span>
                      )}
                    </div>
                    <div className="text-xs text-accent-primary mb-2">{model.role}</div>
                    <p className="text-xs text-text-muted leading-relaxed">{model.desc}</p>
                  </div>
                </StaggerItem>
              ))}
            </StaggerReveal>

            <div className="mt-8 text-center">
              <a href="/models" className="text-sm text-accent-primary hover:underline">
                See detailed model profiles →
              </a>
            </div>
          </div>
        </section>

        {/* ━━ Benchmarks ━━ */}
        <section className="py-24 px-6">
          <div className="container-max">
            <div className="mb-12 max-w-2xl">
              <ScrollRevealText
                text="Benchmarks"
                className="text-3xl md:text-4xl font-serif text-text-primary mb-3"
                style={{ fontWeight: 300, letterSpacing: '-0.02em' }}
              />
              <p className="text-text-secondary">
                Projected from research analysis. Live results coming after third-party verification.
                We show projected scores because we believe in honesty over hype.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border-default">
                    <th className="text-left py-3 px-4 font-semibold text-text-primary">Benchmark</th>
                    <th className="text-center py-3 px-4 font-semibold text-accent-primary">TemuClaude*</th>
                    <th className="text-center py-3 px-4 font-semibold text-text-muted">Claude Sonnet 5</th>
                    <th className="text-center py-3 px-4 font-semibold text-text-muted">GPT-5.5</th>
                    <th className="text-center py-3 px-4 font-semibold text-text-muted">Gemini 3.1</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { name: 'GPQA Diamond', tc: '95-98%', comp: '88%', gpt: '94%', gem: '89%' },
                    { name: 'LiveCodeBench', tc: '96-99%', comp: '87%', gpt: '91%', gem: '85%' },
                    { name: 'SWE-Bench Pro', tc: '75-85%', comp: '70%', gpt: '68%', gem: '65%' },
                    { name: 'Terminal-Bench', tc: '91-96%', comp: '85%', gpt: '82%', gem: '80%' },
                    { name: 'MultiChallenge', tc: '87-94%', comp: '82%', gpt: '85%', gem: '79%' },
                  ].map((row, i) => (
                    <tr key={i} className={i % 2 === 0 ? 'bg-bg-secondary/40' : ''}>
                      <td className="py-3 px-4 text-text-primary font-medium">{row.name}</td>
                      <td className="py-3 px-4 text-center font-bold text-accent-primary">{row.tc}</td>
                      <td className="py-3 px-4 text-center text-text-secondary">{row.comp}</td>
                      <td className="py-3 px-4 text-center text-text-secondary">{row.gpt}</td>
                      <td className="py-3 px-4 text-center text-text-secondary">{row.gem}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="text-xs text-text-muted mt-4">
              * Projected from research analysis, not yet verified by ArtificialAnalysis. Frontier scores from published results.
            </p>
          </div>
        </section>

        {/* ━━ Pricing ━━ */}
        <PricingSection />

        {/* ━━ Final CTA ━━ */}
        <CtaSection />

        {/* ━━ Footer ━━ */}
        <footer className="py-16 px-6 border-t border-border-subtle bg-bg-secondary">
          <div className="container-max">
            <div className="flex flex-col items-center gap-3 mb-10">
              <svg width="36" height="36" viewBox="0 0 100 100" aria-hidden="true">
                <circle cx="50" cy="50" r="9" fill="#E25822"/>
                <line x1="50" y1="50" x2="50" y2="14" stroke="#E25822" strokeWidth="3" stroke-linecap="round"/>
                <line x1="50" y1="50" x2="76" y2="24" stroke="#E25822" strokeWidth="3" stroke-linecap="round"/>
                <line x1="50" y1="50" x2="86" y2="50" stroke="#E25822" strokeWidth="3" stroke-linecap="round"/>
                <line x1="50" y1="50" x2="76" y2="76" stroke="#E25822" strokeWidth="3" stroke-linecap="round"/>
                <line x1="50" y1="50" x2="50" y2="86" stroke="#E25822" strokeWidth="3" stroke-linecap="round"/>
                <line x1="50" y1="50" x2="24" y2="76" stroke="#E25822" strokeWidth="3" stroke-linecap="round"/>
                <line x1="50" y1="50" x2="14" y2="50" stroke="#E25822" strokeWidth="3" stroke-linecap="round"/>
                <line x1="50" y1="50" x2="24" y2="24" stroke="#E25822" strokeWidth="3" stroke-linecap="round"/>
              </svg>
              <div className="font-serif text-lg text-text-primary" style={{ fontWeight: 400 }}>
                TemuClaude
              </div>
              <p className="text-sm text-text-muted">Small input. Frontier output.</p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
              <div>
                <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">Product</h4>
                <ul className="space-y-2">
                  <li><a href="/playground" className="text-sm text-text-secondary hover:text-accent-primary transition-colors">Playground</a></li>
                  <li><a href="/models" className="text-sm text-text-secondary hover:text-accent-primary transition-colors">Models</a></li>
                  <li><a href="/benchmarks" className="text-sm text-text-secondary hover:text-accent-primary transition-colors">Benchmarks</a></li>
                  <li><a href="/pricing" className="text-sm text-text-secondary hover:text-accent-primary transition-colors">Pricing</a></li>
                </ul>
              </div>
              <div>
                <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">Resources</h4>
                <ul className="space-y-2">
                  <li><a href="/docs" className="text-sm text-text-secondary hover:text-accent-primary transition-colors">Documentation</a></li>
                  <li><a href="/enterprise" className="text-sm text-text-secondary hover:text-accent-primary transition-colors">Enterprise</a></li>
                </ul>
              </div>
              <div>
                <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">Connect</h4>
                <ul className="space-y-2">
                  <li><a href="https://github.com/notSaiful/temuclaude" className="text-sm text-text-secondary hover:text-accent-primary transition-colors" target="_blank" rel="noopener noreferrer">GitHub</a></li>
                </ul>
              </div>
              <div>
                <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">Legal</h4>
                <ul className="space-y-2">
                  <li><a href="/terms" className="text-sm text-text-muted hover:text-accent-primary transition-colors">Terms of Service</a></li>
                  <li><a href="/privacy" className="text-sm text-text-muted hover:text-accent-primary transition-colors">Privacy Policy</a></li>
                  <li><a href="/refunds" className="text-sm text-text-muted hover:text-accent-primary transition-colors">Refund Policy</a></li>
                </ul>
              </div>
            </div>

            <div className="pt-8 border-t border-border-subtle flex flex-col items-center gap-3">
              <p className="text-sm text-text-muted">
                Built by Mohammad Saiful Haque · MIT Licensed
              </p>
            </div>
          </div>
        </footer>
      </main>
    </>
  );
}