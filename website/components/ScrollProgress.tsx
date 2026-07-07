'use client';

import { motion, useScroll, useSpring } from 'framer-motion';

/**
 * Thin scroll progress bar at the top of the page.
 * Fills as you scroll. Disappears at top.
 */
export function ScrollProgress() {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001,
  });

  return (
    <motion.div
      className="fixed top-0 left-0 right-0 h-[2px] origin-left z-[9998]"
      style={{
        scaleX,
        background: '#E25822',
      }}
    />
  );
}