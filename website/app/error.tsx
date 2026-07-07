'use client';

import Link from 'next/link';
import { useEffect } from 'react';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center px-6 bg-bg-primary relative overflow-hidden"
    >
      {/* Subtle dot-grid background */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage:
            'radial-gradient(circle at 1px 1px, rgba(26,24,22,0.04) 1px, transparent 0)',
          backgroundSize: '24px 24px',
        }}
      />

      <div className="text-center relative z-10">
        {/* Spark logo */}
        <svg width="48" height="48" viewBox="0 0 100 100" className="mx-auto mb-8" aria-hidden="true">
          <circle cx="50" cy="50" r="9" fill="#E25822" />
          <line x1="50" y1="50" x2="50" y2="14" stroke="#E25822" strokeWidth="3" stroke-linecap="round" />
          <line x1="50" y1="50" x2="76" y2="24" stroke="#E25822" strokeWidth="3" stroke-linecap="round" />
          <line x1="50" y1="50" x2="86" y2="50" stroke="#E25822" strokeWidth="3" stroke-linecap="round" />
          <line x1="50" y1="50" x2="76" y2="76" stroke="#E25822" strokeWidth="3" stroke-linecap="round" />
          <line x1="50" y1="50" x2="50" y2="86" stroke="#E25822" strokeWidth="3" stroke-linecap="round" />
          <line x1="50" y1="50" x2="24" y2="76" stroke="#E25822" strokeWidth="3" stroke-linecap="round" />
          <line x1="50" y1="50" x2="14" y2="50" stroke="#E25822" strokeWidth="3" stroke-linecap="round" />
          <line x1="50" y1="50" x2="24" y2="24" stroke="#E25822" strokeWidth="3" stroke-linecap="round" />
        </svg>

        <div
          className="text-8xl font-serif text-accent-primary mb-4"
          style={{ fontWeight: 300, letterSpacing: '-0.04em' }}
        >
          500
        </div>
        <h1 className="text-2xl font-serif text-text-primary mb-2" style={{ fontWeight: 400 }}>
          Something went wrong
        </h1>
        <p className="text-text-secondary mb-8 max-w-md mx-auto leading-relaxed">
          An error occurred on our end. We've been notified and are working on it.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button onClick={reset} className="btn-accent">
            Try Again
          </button>
          <Link href="/" className="btn-secondary">
            Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}