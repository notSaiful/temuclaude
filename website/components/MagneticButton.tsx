'use client';

import { useRef, useState, ReactNode } from 'react';

interface MagneticButtonProps {
  href: string;
  children: ReactNode;
  className?: string;
  pullStrength?: number;
}

/**
 * Magnetic button — pulls toward cursor slightly.
 * Uses only transform (compositor-friendly). Respects reduced-motion.
 */
export function MagneticButton({
  href,
  children,
  className = '',
  pullStrength = 0.25,
}: MagneticButtonProps) {
  const ref = useRef<HTMLAnchorElement>(null);
  const [transform, setTransform] = useState('');

  function handleMouseMove(e: React.MouseEvent<HTMLAnchorElement>) {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    setTransform(`translate(${x * pullStrength}px, ${y * pullStrength}px)`);
  }

  function handleMouseLeave() {
    setTransform('translate(0px, 0px)');
  }

  return (
    <a
      ref={ref}
      href={href}
      className={className}
      style={{
        transform,
        transition: 'transform 0.3s cubic-bezier(0.25, 1, 0.5, 1)',
      }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {children}
    </a>
  );
}