'use client';

import { useRef, useEffect, useState } from 'react';
import { motion, useInView, animate, useScroll, useTransform } from 'framer-motion';

interface CountUpProps {
  value: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  duration?: number;
  className?: string;
  style?: React.CSSProperties;
}

export function CountUp({
  value,
  prefix = '',
  suffix = '',
  decimals = 0,
  duration = 1.2,
  className,
  style,
}: CountUpProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: '-50px' });
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (!inView) return;
    const controls = animate(0, value, {
      duration,
      ease: 'easeOut',
      onUpdate: (v) => setDisplay(v),
    });
    return () => controls.stop();
  }, [inView, value, duration]);

  return (
    <span
      ref={ref}
      className={className}
      style={{ fontVariantNumeric: 'tabular-nums', ...style }}
    >
      {prefix}{display.toFixed(decimals)}{suffix}
    </span>
  );
}

/**
 * ScrollRevealText — splits text into words and reveals them
 * one-by-one on scroll. From awwwards-design skill technique.
 */
interface ScrollRevealTextProps {
  text: string;
  className?: string;
  style?: React.CSSProperties;
  delay?: number;
}

export function ScrollRevealText({
  text,
  className,
  style,
  delay = 0,
}: ScrollRevealTextProps) {
  const ref = useRef<HTMLHeadingElement>(null);
  const inView = useInView(ref, { once: true, margin: '-80px' });
  const words = text.split(' ');

  return (
    <h2
      ref={ref}
      className={className}
      style={style}
    >
      {words.map((word, i) => (
        <span key={i} style={{ display: 'inline-block', overflow: 'hidden', verticalAlign: 'top' }}>
          <motion.span
            style={{ display: 'inline-block' }}
            initial={{ y: '100%', opacity: 0 }}
            animate={inView ? { y: 0, opacity: 1 } : {}}
            transition={{
              duration: 0.5,
              delay: delay + i * 0.04,
              ease: [0.25, 1, 0.5, 1],
            }}
          >
            {word}
            {i < words.length - 1 ? '\u00A0' : ''}
          </motion.span>
        </span>
      ))}
    </h2>
  );
}

/**
 * ParallaxSection — subtle parallax on scroll for background depth.
 * From awwwards-design skill: "Parallax Layers: Background and
 * foreground elements move at different speeds, creating depth."
 */
interface ParallaxSectionProps {
  children: React.ReactNode;
  className?: string;
  speed?: number; // 0 = no parallax, 1 = full scroll
}

export function ParallaxSection({
  children,
  className,
  speed = 0.15,
}: ParallaxSectionProps) {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ['start end', 'end start'],
  });
  const y = useTransform(scrollYProgress, [0, 1], [`${speed * 100}%`, `${-speed * 100}%`]);

  return (
    <div ref={ref} className={className}>
      <motion.div style={{ y }}>{children}</motion.div>
    </div>
  );
}