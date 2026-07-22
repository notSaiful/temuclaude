'use client';

import dynamic from 'next/dynamic';

const NeonRift = dynamic(() => import('./Game'), {
  ssr: false,
  loading: () => <main className="grid min-h-screen place-items-center bg-[#050611] text-cyan-200">Loading Neon Rift…</main>,
});

export default function NeonRiftPage() {
  return <NeonRift />;
}
