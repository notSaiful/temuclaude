'use client';

import { motion, useMotionValue, useTransform, animate } from 'framer-motion';
import { useEffect, useRef, useState } from 'react';

/**
 * Animated fusion pipeline card for the hero section.
 * Shows: question → 3 cheap Chinese models in parallel → fused answer + metadata.
 * Matches the site's light theme (warm cream/ink, #E25822 accent).
 */
export function FusionPipeline() {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);

  // Animated number for QA score
  const qaScore = useMotionValue(0);
  const qaDisplay = useTransform(qaScore, (v) => `✓ QA ${v.toFixed(1)}`);

  // Animated number for cost
  const cost = useMotionValue(0);
  const costDisplay = useTransform(cost, (v) => `$${v.toFixed(3)}`);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.2 },
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  // Animate numbers when visible
  useEffect(() => {
    if (!visible) return;
    const timer1 = setTimeout(() => {
      animate(qaScore, 9.4, { duration: 0.8, ease: 'easeOut' });
    }, 2400);
    const timer2 = setTimeout(() => {
      animate(cost, 0.012, { duration: 0.8, ease: 'easeOut' });
    }, 2400);
    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
    };
  }, [visible, qaScore, cost]);

  const models = [
    { name: 'GLM-5.2', color: '#E25822', delay: 0 },
    { name: 'DeepSeek', color: '#788C5D', delay: 0.3 },
    { name: 'MiniMax', color: '#C46686', delay: 0.6 },
  ];

  return (
    <div ref={ref} className="w-full max-w-sm">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={visible ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
        className="rounded-lg border border-border-subtle bg-white shadow-md overflow-hidden"
      >
        {/* Terminal header */}
        <div className="flex items-center gap-2 px-4 py-2.5 bg-bg-secondary border-b border-border-subtle">
          <div className="flex gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#ff5f57' }} />
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#febc2e' }} />
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#28c840' }} />
          </div>
          <span className="text-[11px] text-text-muted font-mono ml-2">
            temuclaude — live fusion
          </span>
        </div>

        <div className="p-4 font-mono text-sm">
          {/* Question */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={visible ? { opacity: 1 } : {}}
            transition={{ delay: 0.2, duration: 0.4 }}
            className="text-xs text-text-primary px-3 py-2 bg-bg-secondary rounded-sm border-l-2 mb-3"
            style={{ borderLeftColor: '#E25822' }}
          >
            &quot;Prove that the sum of two odd numbers is even.&quot;
          </motion.div>

          {/* Model bars */}
          <div className="flex gap-2 mb-3">
            {models.map((model) => (
              <div
                key={model.name}
                className="flex-1 text-center px-1.5 py-1.5 rounded-sm border border-border-subtle bg-bg-secondary"
              >
                <div
                  className="text-[10px] font-semibold mb-1"
                  style={{ color: model.color }}
                >
                  {model.name}
                </div>
                <div className="h-[3px] rounded-full bg-border-default overflow-hidden">
                  <motion.div
                    initial={{ width: '0%' }}
                    animate={visible ? { width: '100%' } : {}}
                    transition={{
                      delay: 0.4 + model.delay,
                      duration: 1.2,
                      ease: 'easeInOut',
                    }}
                    className="h-full rounded-full"
                    style={{ background: model.color }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* Fusion arrow */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={visible ? { opacity: 1 } : {}}
            transition={{ delay: 1.8, duration: 0.3 }}
            className="text-center text-xs text-text-muted mb-3"
          >
            ↓ fusion ↓
          </motion.div>

          {/* Answer */}
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={visible ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: 2.0, duration: 0.4 }}
            className="text-xs text-text-primary px-3 py-2 rounded-sm mb-3"
            style={{
              background: 'rgba(226, 88, 34, 0.06)',
              border: '1px solid rgba(226, 88, 34, 0.15)',
            }}
          >
            Let a = 2k+1, b = 2m+1. Then a+b = 2(k+m+1), which is even. ∎
          </motion.div>

          {/* Metadata */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={visible ? { opacity: 1 } : {}}
            transition={{ delay: 2.4, duration: 0.4 }}
            className="flex gap-3 text-[10px] text-text-muted"
          >
            <motion.span style={{ color: '#788C5D' }}>{qaDisplay}</motion.span>
            <motion.span style={{ color: '#E8B547' }}>{costDisplay}</motion.span>
            <span style={{ color: '#C46686' }}>moa-3-layer</span>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}